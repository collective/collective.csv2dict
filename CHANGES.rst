Changelog
=========


1.1 (unreleased)
----------------

- Optionally allow ignoring extra columns.  To use this: initialize
  the reader with ``ignore_extra_columns=True``.
  [maurits]

- Add ``formatting`` method to readers.  It currently returns the
  delimiter, the dialect instance and the expected number of columns.
  You can use this to give a hint in an upload form.
  [maurits]


1.0 (2012-06-21)
----------------

- Initial release
  [maurits]
