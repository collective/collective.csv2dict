.. contents::


Documentation
=============


What is this?
-------------

This package defines base classes ``BaseCSVReader`` and
``BaseMultilineCSVReader``.  These can be used to iterate over a csv
file and return its contents as a dictionary.  Normally you should use
the ``BaseCSVReader``.  The ``BaseMultilineCSVReader`` can be used
when you run into problems with csv files that can have newline
characters within a column, which could trip up the standard reader.


Example usage
-------------

You should write an own class that inherits from one of the base
classes.  The ``example.py`` file has an example.  Basically it
will be something like this::

  from collective.csv2dict import BaseCSVReader, to_int, to_string

  class ExampleCSVReader(BaseCSVReader):
      """Example csv reader class.

      We read three columns and skip one.
      """
      skip = [2]  # skip column index 2
      fields = [
          # The format is: (field name, filter method)
          ('id', to_int),
          ('fullname', to_string),
          ('email', to_string),
      ]

You can then use this class to read a csv file.  The ``example.py``
file again has sample code to read the csv file and some options from
the command line.  Simply put, it boils down to this::

    c = reader(open(filename, 'U'))
    # Iterate over the entries and print them.
    for entry in c:
        print entry
    print '%d entries ignored due to errors.' % c.ignored
    print '%d entries read without errors.' % c.success

It would turn this csv (contained in ``example.csv``)::

  1,Maurits van Rees,ignored,maurits@example.org
  2,Arthur Dent,ignored again,dentarthurdent@example.org

into this dictionary::

   {'email': u'maurits@example.org',
    'fullname': u'Maurits van Rees',
    'id': 1}
   {'email': u'dentarthurdent@example.org',
    'fullname': u'Arthur Dent',
    'id': 2}


Notes
-----

- It is recommented to always open a file in universal newline mode.
  This is usually the best way to avoid some potential problems with
  newlines within a single row.

- The base reader tries to guess the encoding of the file in a
  simplistic way and will avoid breaking when no good encoding can be
  found.

- The reader might ignore the first row of the csv file as it may be a
  header.  We do a simple check for this: if none of the columns of
  the first row can be turned into an integer, then it is not a header
  line and it will be treated as data.  If this logic does not work
  for you, then override the ``is_header`` method in your own class,
  simply like this::

    def is_header(self, items):
        return False

  That will make sure the first line is always treated as data.  If
  you want it to always be treated as a header, just do ``return
  True``.

- You can override the ``prepare_iterable`` method if you need to
  do some fixes to some rows or the complete csv file before the
  reader starts to handle it.  The ``BaseMultilineCSVReader`` has an
  example for this.

- By default the excel csv dialect is used (or whatever your Python
  version has as default).  If you want to use a specific dialect, you
  can override the ``dialect`` variable in your reader class.  For
  example, you can use tabs as delimiter like this::

    import csv

    class MyDialect(csv.excel):
        delimiter = '\t'

    csv.register_dialect('mydialect', MyDialect)

    class ExampleCSVReader(BaseCSVReader):
        dialect = 'mydialect'
        fields = [...]


Compatibility
-------------

I have tried this on Python 2.6 and an earlier version on 2.4.  It
will likely work on all 2.x versions from 2.3 onwards.

Tested on Mac OS X so likely also working on any Unix-like system.
Should work on Windows too, though I can imagine problems with newline
characters in some corner cases.


Note for Plone users
--------------------

I usually make packages for use in Plone, but this one can be used
with plain Python.  Nevertheless, a note for Plone users is probably
good.

If you want to use it within your Plone buildout, just add it to the
eggs in your buildout.cfg.  You do not need to load zcml or install
anything.  You just need to write your own class definition, as in the
example above.  Then you probably want to write a browser view that
uses this class to turn some uploaded csv file to a dictionary.  Then
you probably create a content item or a member for each item in this
dictionary or do whatever you want with it.


Authors
-------

- Maurits van Rees (package creation, various improvements and
  generalizations)

- Guido Wesdorp (initial code, written for a client way back in 2007)
