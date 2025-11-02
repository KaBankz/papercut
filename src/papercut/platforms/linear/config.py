"""
Linear provider configuration and validation.
Self-contained config schema for the Linear integration.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LinearProviderConfig:
    """Linear provider configuration."""

    disabled: bool
    signing_secret: Optional[str]
    max_title_length: int
    max_description_length: int


def validate_config(config: LinearProviderConfig) -> None:
    """
    Validate Linear provider configuration.

    Args:
        config: Linear provider configuration to validate

    Raises:
        ValueError: If configuration is invalid
    """
    if not config.disabled:
        if not config.signing_secret:
            raise ValueError(
                "Linear signing_secret is required when Linear provider is enabled.\n\n"
                "To fix this, either:\n"
                "1. Set signing_secret in [providers.linear] section\n"
                "2. Disable Linear: [providers.linear] disabled = true"
            )

    if config.max_title_length <= 0:
        raise ValueError("max_title_length must be positive")

    if config.max_description_length <= 0:
        raise ValueError("max_description_length must be positive")


def _normalize_optional_string(value: str | None) -> Optional[str]:
    """Convert empty strings to None for opt-out behavior."""
    if value == "":
        return None
    return value


def load_config_from_toml(toml_data: dict) -> LinearProviderConfig:
    """
    Load and validate Linear config from TOML data.

    Args:
        toml_data: Raw TOML dictionary with providers.linear section

    Returns:
        Validated LinearProviderConfig

    Raises:
        ValueError: If config is invalid or missing required fields
    """
    providers_data = toml_data.get("providers", {})
    linear_data = providers_data.get("linear", {})

    try:
        config = LinearProviderConfig(
            disabled=linear_data["disabled"],
            signing_secret=_normalize_optional_string(linear_data.get("signing_secret")),
            max_title_length=linear_data["max_title_length"],
            max_description_length=linear_data["max_description_length"],
        )
    except KeyError as e:
        raise ValueError(
            f"Missing required Linear config field: {e}\n"
            "Check [providers.linear] section in your config file"
        ) from e

    # Validate the loaded config
    validate_config(config)

    return config
