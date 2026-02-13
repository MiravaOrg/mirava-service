"""CLI entry point"""

import sys
import os

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hyper_mirror.main import create_app
import uvicorn


def run():
    """Run the server"""
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")


if __name__ == "__main__":
    run()
