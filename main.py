"""
BooTheSchedule — Entry Point

Starts the Flask API server.
Run with:
    python main.py
    # or
    flask --app src.backend.api run --port 5000
"""

import sys
from pathlib import Path

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).parent / "src" / "backend"))

from api import app

if __name__ == "__main__":
    import os

    debug = os.getenv("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    print(f"Starting BooTheSchedule API on http://0.0.0.0:5000 (debug={debug})")
    app.run(host="0.0.0.0", port=5000, debug=debug)
