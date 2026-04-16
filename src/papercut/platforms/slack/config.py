"""
Slack provider configuration and validation.
Self-contained config schema for the Slack integration.
"""

from dataclasses import dataclass
from typing import Optional
from papercut.core.utils import normalize_optional_string as _normalize_optional_string


@dataclass
class SlackProviderConfig:
    """Slack provider configuration."""

    disabled: bool
    auth_token: Optional[str]
    max_content_length: int


def validate_config(config: SlackProviderConfig) -> None:
    """
    Validate Slack provider configuration.

    Args:
        config: Slack provider configuration to validate

    Raises:
        ValueError: If configuration is invalid
    """
    if config.max_content_length <= 0:
        raise ValueError("max_content_length must be positive")


def load_config_from_toml(toml_data: dict) -> SlackProviderConfig:
    """
    Load and validate Slack config from TOML data.

    Args:
        toml_data: Raw TOML dictionary with providers.slack section

    Returns:
        Validated SlackProviderConfig

    Raises:
        ValueError: If config is invalid or missing required fields
    """
    providers_data = toml_data.get("providers", {})
    slack_data = providers_data.get("slack", {})

    try:
        config = SlackProviderConfig(
            disabled=slack_data["disabled"],
            auth_token=_normalize_optional_string(slack_data.get("auth_token")),
            max_content_length=slack_data["max_content_length"],
        )
    except KeyError as e:
        raise ValueError(
            f"Missing required Slack config field: {e}\n"
            "Check [providers.slack] section in your config file"
        ) from e

    # Validate the loaded config
    validate_config(config)

    return config
