"""
Papercut entry point.
Starts the FastAPI webhook server.
"""

import sys
import uvicorn

try:
    from config import config
    from papercut.api import app
except FileNotFoundError as e:
    print(f"❌ Configuration Error: {e}", file=sys.stderr)
    print(
        "\nMake sure papercut.toml exists at repo root or /config/papercut.toml",
        file=sys.stderr,
    )
    sys.exit(1)
except ValueError as e:
    print(f"❌ Configuration Error: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error loading configuration: {e}", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    print(
        f"  Linear provider: {'disabled' if config.providers.linear.disabled else 'enabled'}"
    )
    print(f"  Footer: {'disabled' if config.footer.disabled else 'enabled'}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
