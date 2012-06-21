"""Base importer of CSV files.
"""

import logging
from pprint import pprint

logger = logging.getLogger('collective.csv2dict')
NEWLINE_MARKER = '--NEWLINE--'


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


def setup_logging():
    # Set up logging.
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


def handle_file(reader, filename, lines_to_print=0, raise_exceptions=False,
                print_key=None):
    """Open the file with the reader.

    Arguments:

    - reader: class to open the file with.

    - filename: filename to open.  We open it in universal newlines
      mode, as that potentially avoids lots of errors with Python 2.4
      and some with Python 2.6.

    - lines_to_print: number of entries to print.  By default we print
      nothing, so you can easily check if all lines can be read
      correctly.

    - raise_exceptions: stop when encountering an error.  This value
      is passed to the reader.

    - print_key: when set, we print the value of this key for each
      item in the resulting dictionary.
    """
    c = reader(open(filename, 'U'), raise_exceptions=raise_exceptions)
    logger.info('Reading %s with %s importer', filename, reader.__name__)

    # Test that all entries can be read.  Output some info when wanted.
    for entry in c:
        if print_key:
            print entry.get(print_key)
        if c.success <= lines_to_print:
            pprint(entry)
    logger.info('%d entries ignored due to errors.', c.ignored)
    logger.info('%d entries read without errors.', c.success)
