# Papercut — _Issues you can touch_

Print your tickets on a real receipt printer

## 📋 Prerequisites

- A receipt printer
- A Cloudflare Tunnel - [Docs](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/)
- A ticketing system (e.g. Linear)
- Docker or Python 3.14+ with uv

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

4. Connect your ticketing system (example: Linear)

   - Webhook URL: `https://<your-domain>/webhooks/linear`
   - In Linear: Settings → API → Webhooks → New
     - Set a Label for the webhook (e.g. "Papercut")
     - Set the webhook URL
     - Save the signing secret to your `papercut.toml` file

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

5. Connect your ticketing system (example: Linear)

   - Webhook URL: `https://<your-domain>/webhooks/linear`
   - In Linear: Settings → API → Webhooks → New
     - Set a Label for the webhook (e.g. "Papercut")
     - Set the webhook URL
     - Save the signing secret to your `papercut.toml` file

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

All papercut configuration is done in the `papercut.toml` file.

This file should be placed in the `config` directory.

If you want to omit certain fields, you can set them to an empty string.

You can also place a `logo.png` file in the `config` directory to display a logo on the receipt header.

## 🐛 Troubleshooting

To find your printer's USB IDs, you can run the following commands:

On Linux:

```bash
lsusb
```

On macOS:

```bash
ioreg -p IOUSB
```
