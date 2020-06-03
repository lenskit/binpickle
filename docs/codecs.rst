Codecs
======

.. py:module:: binpickle.codecs

BinPickle supports codecs to compress buffer content.
These are similar in spirit to numcodecs_, but automatically handle some cases
such as splitting arrays into blocks and can reduce copying in some situations.

.. _numcodecs: https://numcodecs.readthedocs.io/en/stable/

.. toctree::

.. autofunction:: make_codec

Codec API
---------

.. autoclass:: Codec

Codec Implementations
---------------------

Null codec
~~~~~~~~~~

.. autoclass:: Null


Blosc codec
~~~~~~~~~~~

.. autoclass:: Blosc


Gzip codec
~~~~~~~~~~

.. autoclass:: GZ


NumCodecs
~~~~~~~~~

BinPickle also supports any codec from numcodecs_ through the :class:`NC` wrapper.  This
is automatically used by the :func:`make_codec` function, so you can also pass a NumCodecs
codec directly to :meth:`binpickle.BinPickler.compressed`.

