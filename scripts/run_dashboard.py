"""Convenience script to launch Streamlit dashboard."""

import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
APP_PATH = ROOT_DIR / "dashboard" / "app.py"


def launch_dashboard():
    """Starts the Streamlit application."""
    print(f"Launching Streamlit Dashboard from: {APP_PATH}")
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_PATH),
        "--server.port=8501",
        "--server.address=localhost",
    ]
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nStreamlit dashboard terminated.")


if __name__ == "__main__":
    launch_dashboard()
