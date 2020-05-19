BinPickle
=========

The BinPickle library provides an optimized file format for serializing Python objects
in a scientific computing setting.  It uses Pickle Protocol 5 (with the ``pickle5``
library on older versions of Python) to efficiently serialize objects with large
binary data blobs such as NumPy arrays; one of the primary use cases for BinPickle
is efficiently serializing scikit-style statistical and machine learning models.

BinPickle supports a few useful features on top of standard pickling:

* Optional per-buffer compression
* Memory-mapped buffers (when uncompressed) for efficiently sharing

BinPickle wraps Python's pickling functionality, so any object that can be pickled
(including SciKit models) can be stored with BinPickle.  If the object supports
Pickle Protocol 5 (or stores most of its data in NumPy arrays, which in recent
versions support Pickle 5), then large array data will be efficiently stored,
either compressed (with Blosc compression by default) or page-aligned and ready
for memory-mapping, possibly into multiple processes simultaneously.

Quick Start
-----------

Save an object::

    from binpickle import dump, load
    dump(my_large_object, 'file.bpk')

Load an object::

    model = load('file.bpk')

Contents
--------

.. toctree::
   :maxdepth: 1

   write
   read
   codecs
   format

Inspiriation
------------

BinPickle is inspired in part by `joblib`_'s ``dump`` and ``load`` routines that support
memory-mapping numpy buffers.  By building on top of Pickle Protocol 5, we are able to
obtain the same functionality without hacking the pickle serialization protocol.

.. _`joblib`: https://github.com/joblib/joblib
