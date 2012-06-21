"""Example importer of a CSV file.
"""

import sys

from readers import BaseCSVReader
from utils import to_int, to_string
from utils import setup_logging, handle_file


class ExampleCSVReader(BaseCSVReader):
    """Example csv reader class.

    We read three columns and skip one.  It would turn this csv:

      1,Maurits van Rees,ignored,maurits@example.org
      2,Arthur Dent,ignored again,dentarthurdent@example.org

    into this dictionary:

      {'email': u'maurits@example.org',
       'fullname': u'Maurits van Rees',
       'id': 1}
      {'email': u'dentarthurdent@example.org',
       'fullname': u'Arthur Dent',
       'id': 2}

    """
    skip = [2]
    fields = [
        # The format is: (field name, filter method)
        ('id', to_int),
        ('fullname', to_string),
        ('email', to_string),
    ]


def usage():
    text = """Usage: %(prog)s <csv filename to import> [num]

This then uses our importer on the specified file.
The goal is mostly to see if the complete file can be read
without errors.

Optionally, you can specify a number of entries that will be printed.
""" % dict(prog=sys.argv[0])
    print text


if __name__ == '__main__':
    setup_logging()
    # Handle command line arguments.
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)
    if len(sys.argv) > 2:
        try:
            lines_to_print = int(sys.argv[2])
        except:
            usage()
            sys.exit(1)
    else:
        lines_to_print = 0

    filename = sys.argv[1]
    handle_file(ExampleCSVReader, filename, lines_to_print=lines_to_print)
