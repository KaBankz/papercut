"""Platform-specific webhook adapters and routers."""

from papercut.platforms import linear
from papercut.platforms import slack

__all__ = ["linear", "slack"]
