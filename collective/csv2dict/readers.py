"""Base importer of CSV files.
"""

import csv
import logging

from utils import NEWLINE_MARKER

# We try a few encodings while reading the csv file; we try to be a
# bit smart about it though.
ENCODINGS = ('ascii', 'iso-8859-1', 'utf-8', 'cp1252')
logger = logging.getLogger('collective.csv2dict')


class CSVImportError(Exception):
    pass


def to_string(v):
    v = v.strip()
    if v == '0':
        return ''
    return v


def to_int(v):
    v = v.strip()
    if not v:
        return None
    return int(v)


def to_bool(v):
    v = v.strip()
    return bool(v)


def to_text(v):
    # For fields with multiple lines that have first been changed into
    # NEWLINE_MARKER.
    v = v.strip()
    if not v:
        return ''
    return v.replace(NEWLINE_MARKER, '\n')


class BaseCSVReader(object):

    # This is the default encoding we try.
    encoding = 'utf-8'
    # Skip the columns with these indexes.  The first column has index 0.
    skip = []
    # Registered csv dialect to use.  With None we use the standard.
    dialect = None

    def prepare_iterable(self, iterable):
        """Do any preparing work to the iterable.

        Override this in child classes if you need to do something
        special, like handling for csv files where there are line
        breaks within a single row.
        """
        return iterable

    def __init__(self, iterable, raise_exceptions=False):
        """Initialize.
        """
        iterable = self.prepare_iterable(iterable)
        if self.dialect is not None:
            self.reader = csv.reader(iterable, self.dialect)
        else:
            self.reader = csv.reader(iterable)
        self.lineno = 0  # for more useful debug info
        self.ignored = 0  # Number of ignored lines
        self.success = 0  # Successfully imported lines
        self.errors = []  # List of errors encountered.
        # Should we raise exceptions or just continue when
        # encountering some bad data?
        self.raise_exceptions = raise_exceptions

    def decode_it(self, value):
        """Decode the string value to unicode.

        We don't like to fail due to some unicode problems, so we try
        to be smart about choosing a nice encoding.
        """
        # First try the standard encoding that is set in the class.
        try:
            value = value.decode(self.encoding)
        except UnicodeDecodeError:
            pass
        else:
            return value
        # When that fails, try the supported encodings.
        for encoding in ENCODINGS:
            try:
                value = value.decode(self.encoding)
            except UnicodeDecodeError:
                pass
            else:
                # Make sure this encoding gets tried first for the next value:
                self.encoding = encoding
                return value
        # When all else fails, just ignore the errors.
        return value.decode('utf-8', 'ignore')

    def is_header(self, items):
        # We do a simple check: if none of the items can be turned into
        # an integer, then it is not a header line.
        for item in items:
            try:
                int(item.strip())
            except:
                continue
            # We have an integer, which will not happen in a header.
            return False
        # No integers found, so it is a header.
        return True

    def next(self):
        """Get the next line.

        It could be a borked line though, with 'newline inside string'
        (Python 2.4) or 'new-line character seen in unquoted field'
        (Python 2.6).  When that happens, Python suggests:

          "do you need to open the file in universal-newline mode?"

        So that is this: open(filename, 'U')

        In case of borked lines, the next few lines could also be
        broken due to the same error or due to not enough columns, so
        we try a few times to get a working line.
        """

        tries = 0
        max_tries = 100
        while tries < max_tries:
            tries += 1
            self.lineno += 1
            try:
                items = self.reader.next()
            except StopIteration:
                raise
            except Exception, e:
                self.ignored += 1
                msg = "%s: line %d (row %d) ignored because of error: %s" % (
                    self.__class__.__name__, self.lineno,
                    self.ignored + self.success, e)
                self.errors.append(msg)
                logger.warn(msg)
                if self.raise_exceptions:
                    raise CSVImportError(msg)
                continue
            else:
                if len(items) == len(self.fields) + len(self.skip):
                    # A good line found
                    break
                elif tries == 1:
                    # Bad line found on first try.
                    self.ignored += 1
                    error = ("No correct number of columns (%d instead of %d)."
                             % (len(items), len(self.fields) + len(self.skip)))
                    msg = ("%s: line %d (row %d) ignored because of error: "
                           "%s" % (
                               self.__class__.__name__, self.lineno,
                               self.ignored + self.success, error))
                    logger.warn(msg)
                    if self.raise_exceptions:
                        raise CSVImportError(msg)
                else:
                    # Bad line found, but caused by an earlier reading
                    # error, likely a 'newline inside string'
                    # exception, so we have already counted this as an
                    # ignored row.
                    pass
        if tries >= max_tries:
            raise CSVImportError("Failed to find a good line after %d tries"
                                 % tries)
        # First line might be a header, we ignore that one then.
        if self.lineno == 1 and self.is_header(items):
            self.lineno += 1
            items = self.reader.next()
        ret = {}
        if self.skip:
            # Some columns need to be skipped.
            items = [item for (index, item) in enumerate(items)
                     if index not in self.skip]
        for index, (name, filter) in enumerate(self.fields):
            value = items[index]
            if value == '\N':
                # This is NULL.
                value = None
            if filter and value is not None:
                try:
                    value = filter(value)
                except Exception, e:
                    # Make the exception info a little more useful or
                    # ignore it.
                    msg = '%s (field="%s", value="%s", line %d, filter %r)' % (
                        e, name, value, self.lineno, filter.__name__)
                    self.errors.append(msg)
                    logger.warn(msg)
                    if self.raise_exceptions:
                        raise CSVImportError(msg)
                    value = None
            if isinstance(value, str):
                value = self.decode_it(value)
            ret[name] = value
        self.success += 1
        return ret

    def __iter__(self):
        return self


class BaseMultilineCSVReader(BaseCSVReader):
    """Read rows that span multiple lines.

    Use this when you run into problems with the base reader.  Note
    that Python 2.6 is already better than 2.4 here, and opening files
    in universal newline mode also helps.
    """

    def prepare_iterable(self, iterable):
        """Do any preparing work to the iterable.

        Sometimes there is just too much going wrong with newlines, so
        we need to get in and fix it ourselves.  Quite ugly.

        We could make this a generator and use yield, but it is a bit
        hard to know when exactly a line is correct.
        """
        new = []
        broken = False
        for line in iterable.readlines():
            if line == '\\\n':
                # The next line belongs to the previous line.
                broken = True
                continue
            line = line.strip()
            if broken:
                # This line belongs to the previous line.
                new[-1] += NEWLINE_MARKER + line
                broken = False
            else:
                # All is normal.
                new.append(line)
            if line.endswith('\\'):
                # There will be a continuation in the next line.
                broken = True
                continue
        return new
