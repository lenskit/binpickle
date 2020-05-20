# BinPickle - efficient binary pickled data

![Test and Build](https://github.com/lenskit/binpickle/workflows/Test%20and%20Package/badge.svg)

This package uses the new Pickle Protocol 5 in Python 3.8 (or its `pickle5` backport)
to efficiently serialize large objects, particularly from scientific Python packages,
to an on-disk format.  This format is designed to support two use cases:

1.  Serializing data-intensive statistical models in a memory-mappable format so
    multiple processes can share the same (read-only) model memory.
2.  Serializing data-intensive statistical models with good compression for long-term
    storage and cross-machine transportation.

BinPickle does this by using Pickle 5's out-of-band buffer serialization support to
write buffers uncompressed and page-aligned for memory mapping (use case 1) or with
per-buffer efficient compression with libraries like Blosc (use case 2).

## Acknowledgements

This material is based upon work supported by the National Science Foundation under
Grant No. IIS 17-51278. Any opinions, findings, and conclusions or recommendations
expressed in this material are those of the author(s) and do not necessarily reflect
the views of the National Science Foundation.  This page has not been approved by
Boise State University and does not reflect official university positions.
