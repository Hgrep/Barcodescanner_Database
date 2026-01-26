import os
import sys

# ------------------------------
# EANSearch API Key
# ------------------------------
EANSEARCH_API_KEY = "PUT_YOUR_KEY_HERE"

# ------------------------------
# Database Path
# ------------------------------
# Use a writable location in AppData for the SQLite database
if getattr(sys, 'frozen', False):
    # Running as PyInstaller .exe
    base_dir = os.path.join(os.environ['APPDATA'], "BookScanner")
else:
    # Running as script
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Ensure the directory exists
os.makedirs(base_dir, exist_ok=True)

# Full path to database
DATABASE_PATH = os.path.join(base_dir, "books.db")
