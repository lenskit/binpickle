Format
======

.. module:: binpickle.format

The :py:mod:`binpickle.format` module contains the data structures that define the
BinPickle format.

Users will not need these classes.  They are documented here in the interest of documenting
the file format.

File Structure
--------------

BinPickle uses Pickle 5's out-of-band buffer serialization support, and thus stores the
pickled object in two parts:

1. The contents of the out-of-band buffers.
2. The Protocol 5 pickled bytes.

The bytes are stored as another buffer, so pickling an object with *n* buffers stores
*n+1* buffers in the file, the last one of which contains the pickle bytes.

The BinPickle format is inspired by Zip, with an index at the end of the file that tells
the reader where in the file to find the various contents.

A Version 1 BinPickle file is organized as follows:

1. 16-byte header, beginning with magic bytes ``BPCK`` (see :py:class:`FileHeader`).
2. The out-of-band buffers, in order.  Padding may appear before or after any buffer's contents.
3. The pickle bytes, as a buffer.
4. The file index, stored as a list of :py:class:`IndexEntry` objects encoded in MsgPack.
5. 16-byte trailer (see :py:class:`FileTrailer`).

The position and length of each buffer is stored in the index, so buffers can have arbitrary
padding between them.  They could even technically be out-of-order, but such a file should
not be generated.  Uncompressed BinPickle files intended for memory-mapped use align each
buffer to the operating system page size (from :py:data:`mmap.PAGESIZE`).

Classes
-------

.. autoclass:: FileHeader

.. autoclass:: FileTrailer

.. autoclass:: IndexEntry
