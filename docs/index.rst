BinPickle
=========

The BinPickle library provides an optimized file format for serializing Python objects
in a scientific computing setting.  It uses Pickle Protocol 5 (with the ``pickle5``
library on older versions of Python) to efficiently serialize objects with large
binary data blobs such as NumPy arrays; one of the primary use cases for BinPickle
is efficiently serializing scikit-style statistical and machine learning models.

BinPickle supports a few useful features on top of standard pickling:

* Optional per-buffer compression and transcoding with :py:mod:`numcodecs`.
* Memory-mapped buffers (when uncompressed) for efficiently sharing

Contents
--------

.. toctree::
   :maxdepth: 1

   codecs
   format

Inspiriation
------------

BinPickle is inspired in part by `joblib`_'s ``dump`` and ``load`` routines that support
memory-mapping numpy buffers.  By building on top of Pickle Protocol 5, we are able to
obtain the same functionality without hacking the pickle serialization protocol.

.. _`joblib`: https://github.com/joblib/joblib
