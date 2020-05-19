Codecs
======

.. py:module:: binpickle.codecs

BinPickle supports codecs to compress buffer content.
These are similar in spirit to numcodecs_, but automatically handle some cases
such as splitting arrays into blocks and can reduce copying in some situations.

.. _numcodecs: https://numcodecs.readthedocs.io/en/stable/

.. toctree::

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
