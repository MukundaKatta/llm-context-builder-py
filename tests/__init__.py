"""Test package bootstrap.

The library uses a ``src/`` layout, so ``src`` must be importable for the test
suite to find ``llm_context_builder`` without an editable install. This makes
``python3 -m unittest discover -s tests`` work out of the box.
"""

import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
