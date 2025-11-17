# Papercut — _Pings you can touch_

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Docker](https://img.shields.io/badge/Docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://github.com/kabankz/papercut/pkgs/container/papercut)
[![Python](https://img.shields.io/badge/Python-%2314354C.svg?style=flat&logo=python&logoColor=white)](https://github.com/kabankz/papercut/blob/main/pyproject.toml)

**Make the digital physical** — Papercut brings the satisfying tactility of receipt printers to your digital life. There's something magical about physical output in our increasingly digital world. Whether it's a critical bug that needs fixing, a coffee order that just came in, or just the satisfaction of tearing off a completed task - physical receipts create a presence that pixels can't match.

## ✨ Features

- 🖨️ **ESC/POS Compatible** - Works with most USB receipt printers
- 🔌 **Webhook-driven** - Integrates with any service that supports webhooks
- 🎨 **Fully Customizable** - Control layout, formatting, fields, and branding
- 🐳 **Docker Ready** - Simple deployment with Docker Compose
- 🔧 **Extensible** - Easy to add new integrations and print formats
- ⚡ **Real-time** - Instant printing when events occur

## 📋 Prerequisites

- **Receipt Printer**: ESC/POS compatible USB printer
  - Tested on: Epson TM-T20III
  - Should work with any printer supported by [python-escpos](https://github.com/python-escpos/python-escpos)
- **Cloudflare Account**: For creating a tunnel to expose your webhook endpoint - [Setup Guide](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/)
- **Integration Source**: Any webhook-capable service (Linear, Slack, etc.)
- **Runtime**: Docker or Python 3.14+ with uv

> [!NOTE]
> We recommend using Cloudflare Tunnels to securely expose your papercut instance.
>
> But you can use any other method you prefer (e.g. port-forwarding, ngrok) to expose your papercut instance.

## 🚀 Quick Start (Docker Compose)

> [!IMPORTANT]
> Docker on macOS cannot pass USB devices into containers.
>
> For macOS, skip to the [Manual Setup](#🧪-manual-setup) section

1. Create a `compose.yaml` file

   ```yaml
   name: papercut

   services:
     papercut:
       image: ghcr.io/kabankz/papercut:latest
       volumes:
         - /dev/bus/usb:/dev/bus/usb:ro
         - ./config:/config:ro
       privileged: true
       restart: unless-stopped

     cloudflared:
       image: docker.io/cloudflare/cloudflared:2025.6.1
       command: tunnel --no-autoupdate run
       environment:
         - TUNNEL_TOKEN=${TUNNEL_TOKEN}
       restart: unless-stopped
   ```

2. Create a `.env` file

   ```bash
   TUNNEL_TOKEN=YOUR_CLOUDFLARE_TUNNEL_TOKEN
   ```

3. Create a `config/papercut.toml` file

   ```toml
   # Set your printer USB IDs (Linux: lsusb, macOS: ioreg)
   [printer]
   usb_vendor_id = "0x04b8"   # e.g., Epson
   usb_product_id = "0x0e28"  # model-specific

   [header]
   company_name = "Your Company"
   address_line1 = "123 Main St"
   address_line2 = "City, State 12345"

   # Configure the provider you want to use
   [providers.linear]
   signing_secret = "YOUR_PROVIDER_SIGNING_SECRET"
   ```

4. Connect your webhook source

   **Example: Linear Integration**

   - Webhook URL: `https://<your-domain>/webhooks/linear`
   - In Linear: Settings → API → Webhooks → New
     - Label: "Papercut"
     - URL: Your webhook URL
     - Events: Select events to print (e.g., "Issue created")
   - Copy the signing secret to your `papercut.toml`

5. Start papercut

   > [!TIP]
   > This is what your directory structure should look like:
   >
   > ```text
   > papercut/
   > ├─ compose.yaml
   > ├─ .env
   > └─ config/
   >    ├─ papercut.toml
   >    └─ logo.png # Optional
   > ```

   ```bash
   docker compose up -d
   ```

## 🧪 Manual Setup

1. Clone the repository

   ```bash
   git clone https://github.com/kabankz/papercut.git
   cd papercut
   ```

2. Install dependencies

   ```bash
   uv sync
   ```

3. Create a `.env` file

   ```bash
   TUNNEL_TOKEN=YOUR_CLOUDFLARE_TUNNEL_TOKEN
   ```

4. Create a `config/papercut.toml` file

   ```toml
   # Set your printer USB IDs (Linux: lsusb, macOS: ioreg)
   [printer]
   usb_vendor_id = "0x04b8"   # e.g., Epson
   usb_product_id = "0x0e28"  # model-specific

   [header]
   company_name = "Your Company"
   address_line1 = "123 Main St"
   address_line2 = "City, State 12345"

   # Configure the provider you want to use
   [providers.linear]
   signing_secret = "YOUR_PROVIDER_SIGNING_SECRET"
   ```

5. Connect your webhook source

   **Example: Linear Integration**

   - Webhook URL: `https://<your-domain>/webhooks/linear`
   - In Linear: Settings → API → Webhooks → New
     - Label: "Papercut"
     - URL: Your webhook URL
     - Events: Select events to print (e.g., "Issue created")
   - Copy the signing secret to your `papercut.toml`

6. Start the Cloudflare Tunnel

   - Remove the `papercut` service from your `compose.yaml` file, then run:

   ```bash
   docker compose up -d
   ```

7. Start papercut

   ```bash
   make start
   ```

## 📝 Configuration

All configuration is managed through `config/papercut.toml`. Check out the [default config](papercut.toml) for all available options with documentation.

Key things to configure:

- **Printer IDs**: Your printer's USB vendor and product IDs
- **Provider settings**: Webhook secrets

> [!TIP]
> Place a file named `logo` in the `config/` directory with any supported format (png, jpg, gif, bmp) to add your logo to receipts

## 🐛 Troubleshooting

### Finding Your Printer's USB IDs

**Linux:**

```bash
lsusb
# Look for your printer, e.g.:
# Bus 001 Device 004: ID 04b8:0e28 Seiko Epson Corp.
#                     ID ^^^^:^^^^ (vendor:product)
```

**macOS:**

```bash
ioreg -p IOUSB -l | grep -E '"(idVendor|idProduct|USB Product Name)"'
# Returns values in decimal - convert to hex for config
```

## 🤝 Contributing

Have ideas for what to print? Found a bug? Want to add support for your favorite service? PRs welcome!

The core is intentionally generic - if it has webhooks, we can probably print it.

## 📄 License

This project is licensed under the [AGPL-3.0 License](LICENSE).

---

<!-- markdownlint-disable MD033 -->
<p align="center">
  Made with ❤️ by <a href="https://github.com/kabankz">KaBanks</a>
</p>
