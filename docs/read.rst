Reading BinPickle Files
=======================

Reading an object from a BinPickle file is done with :py:func:`load()`::

    from binpickle import load
    obj = load('file.bpk')

The ``load`` Function
---------------------

.. autofunction:: binpickle.load

The ``BinPickleFile`` Class
---------------------------

For full control of the deserialization process, and in particular to support
memory-mapped object contents (e.g. for shared memory use), use
:py:class:`binpickle.BinPickleFile` directly.

If you open the BinPickle file in *direct* mode (the ``direct=True`` argument
to :py:meth:`binpickle.BinPickleFile.__init__`), then the contents of buffers
in the object (e.g. NumPy arrays or Pandas columns) will be directly backed by
a read-only memory-mapped region from the BinPickle file.  This has two
consequences:

1.  Multiple processes with the same file open in direct mode will (usually)
    *share* buffer memory.  This is one of BinPickle's particular benefits:
    an easy way to load large array data, such as the learned parameters of
    many SciKit-style machine learning models, in multiple processes with
    minimal duplication.

2.  The :py:class:`binpickle.BinPickleFile` object cannot be closed until
    all objects referencing its memory have been destroyed.
    :py:meth:`binpickle.BinPickleFile.close` will throw an exception if it
    is closed prematurely.

.. autoclass:: binpickle.BinPickleFile
