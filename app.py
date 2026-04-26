#!/usr/bin/env python

import os
import subprocess
import sys

if __name__ == "__main__":
    port = os.environ.get("PORT", "8501")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "frontend/app.py",
        "--server.port", port,
        "--server.headless", "true",
        "--server.runOnSave", "false"
    ])