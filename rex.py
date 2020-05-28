import os.path
import sys
import glob

__all__ = []

# Use native Git tools to update submodules.
app_dir = os.path.abspath(os.getcwd())
sys.path.extend(glob.glob(os.path.join(app_dir, "vendor/*")))
