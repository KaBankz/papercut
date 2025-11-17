"""
Configuration settings for Papercut.
Loads configuration from TOML file with proper validation and empty string handling.
"""

import tomllib
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from papercut.core.utils import normalize_optional_string as _normalize_optional_string

logger = logging.getLogger(__name__)

RECEIPT_WIDTH = 48  # Standard for 80mm thermal printers
RECEIPT_PADDING = 2  # Console preview padding
RECEIPT_INNER_WIDTH = RECEIPT_WIDTH - (RECEIPT_PADDING * 2)


@dataclass
class PrinterConfig:
    """USB printer configuration."""

    usb_vendor_id: int
    usb_product_id: int
    profile: str


@dataclass
class HeaderConfig:
    """Receipt header configuration."""

    logo_disabled: bool
    logo_path: Optional[str]  # Resolved path (None if disabled or not found)
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
class ProvidersConfig:
    """Providers configuration - dynamically populated by provider modules."""

    linear: Optional[object] = None  # Will be LinearProviderConfig from provider module


@dataclass
class Config:
    """Main configuration object."""

    printer: PrinterConfig
    header: HeaderConfig
    footer: FooterConfig
    providers: ProvidersConfig


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
        profile = printer_data["profile"]
        printer = PrinterConfig(
            usb_vendor_id=int(vendor_id_str, 16)
            if isinstance(vendor_id_str, str)
            else vendor_id_str,
            usb_product_id=int(product_id_str, 16)
            if isinstance(product_id_str, str)
            else product_id_str,
            profile=profile,
        )
    except (KeyError, ValueError) as e:
        raise ValueError(
            f"Invalid or missing USB printer config. Check [printer] section in config file: {e}"
        ) from e

    # Parse and normalize header (empty strings → None)
    header_data = toml_data.get("header", {})

    # Logo: convention over configuration
    # If not disabled, check for /config/logo.* then ./config/logo.* with supported formats
    logo_disabled = header_data.get("logo_disabled", False)
    resolved_logo_path = None
    if not logo_disabled:
        # Supported image formats for ESC/POS printers
        supported_extensions = [".png", ".jpg", ".gif", ".bmp"]

        # Prefer absolute path first
        for ext in supported_extensions:
            absolute_logo = Path(f"/config/logo{ext}")
            if absolute_logo.exists():
                resolved_logo_path = str(absolute_logo)
                break

        # Fall back to relative path if not found
        if resolved_logo_path is None:
            for ext in supported_extensions:
                relative_logo = Path(f"./config/logo{ext}")
                if relative_logo.exists():
                    resolved_logo_path = str(relative_logo)
                    break

    header = HeaderConfig(
        logo_disabled=logo_disabled,
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

    # Load provider configs dynamically from their modules
    providers = ProvidersConfig()

    # Linear provider (if available)
    try:
        from papercut.platforms.linear import (
            load_config_from_toml as load_linear_config,
        )

        providers.linear = load_linear_config(toml_data)
    except ImportError:
        # Linear provider not installed/available
        pass
    except ValueError as e:
        # Linear config validation failed
        raise ValueError(
            f"Linear provider config error (from {config_file_path}):\n{e}"
        ) from e

    # Create config object
    config = Config(
        printer=printer,
        header=header,
        footer=footer,
        providers=providers,
    )

    # Log final merged configuration
    logger.info("=" * 60)
    logger.info(f"Config source: {config_file_path}")
    logger.info("=" * 60)
    logger.info("")
    logger.info("[printer]")
    logger.info(f"  usb_vendor_id = {hex(config.printer.usb_vendor_id)}")
    logger.info(f"  usb_product_id = {hex(config.printer.usb_product_id)}")
    logger.info(f"  profile = {config.printer.profile}")
    logger.info("")
    logger.info("[header]")
    logger.info(f"  logo_disabled = {config.header.logo_disabled}")
    logger.info(f"  company_name = {config.header.company_name}")
    logger.info(f"  address_line1 = {config.header.address_line1}")
    logger.info(f"  address_line2 = {config.header.address_line2}")
    logger.info(f"  phone = {config.header.phone}")
    logger.info(f"  url = {config.header.url}")
    logger.info("")
    logger.info("[footer]")
    logger.info(f"  disabled = {config.footer.disabled}")
    logger.info(f"  qr_code_disabled = {config.footer.qr_code_disabled}")
    logger.info(f"  qr_code_size = {config.footer.qr_code_size}")
    logger.info(f"  qr_code_title = {config.footer.qr_code_title}")
    logger.info(f"  footer_text = {config.footer.footer_text}")
    logger.info("")
    if config.providers.linear:
        logger.info("[providers.linear]")
        logger.info(f"  disabled = {config.providers.linear.disabled}")
        logger.info(
            f"  signing_secret = {'***' if config.providers.linear.signing_secret else None}"
        )
        logger.info(f"  max_title_length = {config.providers.linear.max_title_length}")
        logger.info(
            f"  max_description_length = {config.providers.linear.max_description_length}"
        )
    logger.info("=" * 60)

    return config


# Load config on module import
config = load_config()
