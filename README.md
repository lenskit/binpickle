# BinPickle - efficient binary pickled data

[![PyPI version](https://badge.fury.io/py/binpickle.svg)](https://badge.fury.io/py/binpickle)
![Test and Build](https://github.com/lenskit/binpickle/workflows/Test%20and%20Package/badge.svg)
[![codecov](https://codecov.io/gh/lenskit/binpickle/branch/master/graph/badge.svg)](https://codecov.io/gh/lenskit/binpickle)

This package uses the new Pickle Protocol 5 added in Python 3.8 to efficiently
serialize large objects, particularly from scientific Python packages, to an
on-disk format.  This format is designed to support two use cases:

1.  Serializing data-intensive statistical models in a memory-mappable format so
    multiple processes can share the same (read-only) model memory.
2.  Serializing data-intensive statistical models with good compression for long-term
    storage and cross-machine transportation.

BinPickle does this by using Pickle 5's out-of-band buffer serialization support to
write buffers uncompressed and page-aligned for memory mapping (use case 1) or with
per-buffer efficient compression with libraries like Blosc (use case 2).

## Format Stability

We do **not** yet guarantee the stability of the BinPickle format.  We will avoid gratuitous changes,
but BinPickle 1.0 will be the first with a stability guarantee.

## Acknowledgements

This material is based upon work supported by the National Science Foundation under
Grant No. IIS 17-51278. Any opinions, findings, and conclusions or recommendations
expressed in this material are those of the author(s) and do not necessarily reflect
the views of the National Science Foundation.  This page has not been approved by
Boise State University and does not reflect official university positions.
