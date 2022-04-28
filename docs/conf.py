import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import binpickle

project = 'BinPickle'
copyright = '2020-2022 Boise State University'
author = 'Michael D. Ekstrand'

release = binpickle.__version__

extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

source_suffix = '.rst'

pygments_style = 'sphinx'
highlight_language = 'python3'

html_theme = 'furo'
html_theme_options = {
    'github_user': 'lenskit',
    'github_repo': 'binpickle',
    'travis_button': False,
    # 'canonical_url': 'https://binpickle.lenskit.org/',
    # 'font_family': 'Georgia, Charter, serif'
}
templates_path = ['_templates']

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numba': ('https://numba.readthedocs.io/en/stable/', None),
}

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource'
}
