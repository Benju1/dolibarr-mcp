import sys
import os
sys.path.insert(0, os.path.abspath("src"))
from dolibarr_mcp.server import search_projects

print(f"Type: {type(search_projects)}")
print(f"Dir: {dir(search_projects)}")
