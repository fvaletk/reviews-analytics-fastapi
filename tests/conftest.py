import sys
import os

# Ensure the project root (/app inside the container) is on sys.path so that
# `from main import app` resolves correctly when pytest is invoked from /app.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
