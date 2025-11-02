"""
Configuration settings for Papercut.
Loads configuration from TOML file with proper validation and empty string handling.
"""

import tomllib
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

RECEIPT_WIDTH = 48  # Standard for 80mm thermal printers
RECEIPT_PADDING = 2  # Console preview padding
RECEIPT_INNER_WIDTH = RECEIPT_WIDTH - (RECEIPT_PADDING * 2)


@dataclass
class PrinterConfig:
    """USB printer configuration."""

    usb_vendor_id: int
    usb_product_id: int


@dataclass
class HeaderConfig:
    """Receipt header configuration."""

    logo_path: Optional[str]
    company_name: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    phone: Optional[str]
    url: Optional[str]


@dataclass
class FooterConfig:
    """Receipt footer configuration."""

    disabled: bool
    qr_code_disabled: bool
    qr_code_size: int
    qr_code_title: Optional[str]
    footer_text: Optional[str]


@dataclass
class LinearProviderConfig:
    """Linear provider configuration."""

    disabled: bool
    signing_secret: Optional[str]
    max_title_length: int
    max_description_length: int


@dataclass
class ProvidersConfig:
    """Providers configuration."""

    linear: LinearProviderConfig


@dataclass
class Config:
    """Main configuration object."""

    printer: PrinterConfig
    header: HeaderConfig
    footer: FooterConfig
    providers: ProvidersConfig


def _normalize_optional_string(value: str | None) -> Optional[str]:
    """
    Convert empty strings to None for opt-out behavior.

    Args:
        value: String value from TOML config

    Returns:
        None if value is empty string, otherwise the value as-is
    """
    if value == "":
        return None
    return value


def _deep_merge(base: dict, overlay: dict) -> None:
    """
    Deep merge overlay dict into base dict (modifies base in-place).

    Args:
        base: Base dictionary to merge into
        overlay: Overlay dictionary with values to merge
    """
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def load_config() -> Config:
    """
    Load configuration from TOML file.

    Priority:
    1. /config/papercut.toml (user's mounted config - Docker)
    2. ./config/papercut.toml (user's local config - development)
    3. ./papercut.toml (repo default - always present)

    Returns:
        Config: Validated configuration object

    Raises:
        FileNotFoundError: If no config file found
        ValueError: If validation fails
        tomllib.TOMLDecodeError: If TOML file is malformed
    """
    # Load repo default first (always exists)
    repo_default = Path("papercut.toml")
    if not repo_default.exists():
        raise FileNotFoundError(
            "Repo default config 'papercut.toml' not found. This file should always exist in the repo."
        )

    try:
        with open(repo_default, "rb") as f:
            toml_data = tomllib.load(f)
        config_file_path = repo_default
    except tomllib.TOMLDecodeError as e:
        raise ValueError(
            f"Failed to parse repo default config {repo_default}: {e}"
        ) from e

    # Try to overlay user config (optional)
    user_config_paths = [
        Path("/config/papercut.toml"),
        Path("./config/papercut.toml"),
    ]

    for user_path in user_config_paths:
        if user_path.exists():
            try:
                with open(user_path, "rb") as f:
                    user_data = tomllib.load(f)
                # Deep merge user config over defaults
                _deep_merge(toml_data, user_data)
                config_file_path = f"{repo_default} + {user_path}"
                break
            except tomllib.TOMLDecodeError as e:
                raise ValueError(
                    f"Failed to parse user config file {user_path}: {e}"
                ) from e

    # Parse printer config (convert hex strings to integers)
    printer_data = toml_data.get("printer", {})
    try:
        vendor_id_str = printer_data["usb_vendor_id"]
        product_id_str = printer_data["usb_product_id"]
        printer = PrinterConfig(
            usb_vendor_id=int(vendor_id_str, 16)
            if isinstance(vendor_id_str, str)
            else vendor_id_str,
            usb_product_id=int(product_id_str, 16)
            if isinstance(product_id_str, str)
            else product_id_str,
        )
    except (KeyError, ValueError) as e:
        raise ValueError(
            f"Invalid or missing USB printer config. Check [printer] section in config file: {e}"
        ) from e

    # Parse and normalize header (empty strings → None)
    header_data = toml_data.get("header", {})

    # Resolve and validate logo path
    logo_path_raw = _normalize_optional_string(header_data.get("logo_path"))
    resolved_logo_path = None
    if logo_path_raw:
        logo_path_obj = Path(logo_path_raw)
        if logo_path_obj.is_absolute():
            # Absolute path - use as-is if exists
            resolved_logo_path = logo_path_raw if logo_path_obj.exists() else None
        else:
            # Try /config/ first (user's mounted logo), then relative path
            config_logo = Path(f"/config/{logo_path_raw}")
            if config_logo.exists():
                resolved_logo_path = str(config_logo)
            elif logo_path_obj.exists():
                resolved_logo_path = logo_path_raw
            # If neither exists, resolved_logo_path stays None

    header = HeaderConfig(
        logo_path=resolved_logo_path,
        company_name=_normalize_optional_string(header_data.get("company_name")),
        address_line1=_normalize_optional_string(header_data.get("address_line1")),
        address_line2=_normalize_optional_string(header_data.get("address_line2")),
        phone=_normalize_optional_string(header_data.get("phone")),
        url=_normalize_optional_string(header_data.get("url")),
    )

    # Parse and normalize footer (empty strings → None for text fields)
    footer_data = toml_data.get("footer", {})
    footer = FooterConfig(
        disabled=footer_data["disabled"],
        qr_code_disabled=footer_data["qr_code_disabled"],
        qr_code_size=footer_data["qr_code_size"],
        qr_code_title=_normalize_optional_string(footer_data.get("qr_code_title")),
        footer_text=_normalize_optional_string(footer_data.get("footer_text")),
    )

    # Parse providers.linear
    providers_data = toml_data.get("providers", {})
    linear_data = providers_data.get("linear", {})
    linear = LinearProviderConfig(
        disabled=linear_data["disabled"],
        signing_secret=_normalize_optional_string(linear_data.get("signing_secret")),
        max_title_length=linear_data["max_title_length"],
        max_description_length=linear_data["max_description_length"],
    )

    providers = ProvidersConfig(linear=linear)

    # Create config object
    config = Config(
        printer=printer,
        header=header,
        footer=footer,
        providers=providers,
    )

    # Validation: Linear signing secret required if not disabled
    if not config.providers.linear.disabled:
        if not config.providers.linear.signing_secret:
            raise ValueError(
                f"Linear signing_secret is required when Linear provider is enabled.\n"
                f"Config file: {config_file_path}\n\n"
                f"To fix this, either:\n"
                f"1. Set signing_secret in [providers.linear] section\n"
                f"2. Disable Linear: [providers.linear] disabled = true"
            )

    return config


# Load config on module import
config = load_config()
