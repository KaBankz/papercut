"""
Papercut entry point.
Starts the FastAPI webhook server.
"""

import uvicorn
from papercut.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
