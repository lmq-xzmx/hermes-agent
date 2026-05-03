"""
Root conftest.py for file_manager tests.

Sets up Python path so that `from file_manager...` imports work correctly.
"""

import sys
from pathlib import Path

# Add tools/ to path so `from file_manager...` imports work
tools_path = Path(__file__).parent.parent
if str(tools_path) not in sys.path:
    sys.path.insert(0, str(tools_path))
