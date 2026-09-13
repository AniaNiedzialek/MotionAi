import os
import sys

# The real_time modules import each other by bare name (from database import ...),
# so put that directory on the path the same way running app.py directly does.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "real_time"))
