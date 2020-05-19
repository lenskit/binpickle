"""
Compatibility support.
"""

import pickle

# Make sure we have Pickle 5
if pickle.HIGHEST_PROTOCOL < 5:
    import pickle5 as pickle
