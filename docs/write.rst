Writing BinPickle Files
=======================

The easy, single-function entry point for saving data is :py:func:`binpickle.dump`::

    from binpickle import dump
    dump(obj, 'file.bpk')


The ``dump`` Function
---------------------

.. autofunction:: binpickle.dump

The ``BinPickler`` Class
------------------------

For full control over the serialization process, you can directly use the
:py:class:`binpickle.BinPickler` backend class.

.. autoclass:: binpickle.BinPickler
