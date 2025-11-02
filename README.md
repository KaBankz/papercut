# Papercut — _Issues you can touch_

Print your tickets on a real receipt printer.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Papercut

Copy the default configuration file and customize it:

```bash
cp papercut.toml ./config/papercut.toml
```

Edit `./config/papercut.toml` to set your Linear signing secret and customize the receipt:

```toml
[providers.linear]
signing_secret = "your_linear_signing_secret_here"  # Get from Linear webhook settings

[header]
company_name = "Your Company"
# Set to empty string "" to hide any field
address_line1 = ""  # This will hide address line 1

[footer]
disabled = false  # Set to true to hide entire footer
footer_text = "Made with ❤️ by Your Company"
```

> [!NOTE]
> Section 5 explains how to get your Linear signing secret.
>
> **Hiding fields:** Set any header/footer field to empty string `""` to hide it from receipts.
>
> **Provider control:** Set `[providers.linear] disabled = true` to disable Linear webhooks.

### 3. Run the Server

**Development (with auto-reload):**

```bash
make dev
```

**Production:**

```bash
make start
```

Server runs on `http://localhost:8000`

- Webhook: `POST http://localhost:8000/webhooks/linear`
- Health check: `GET http://localhost:8000/`
- API docs: `http://localhost:8000/docs`

**Docker:**

First, set up your config:

```bash
cp papercut.toml ./config/papercut.toml
# Edit ./config/papercut.toml with your settings
```

Then start the services:

```bash
make compose-up
```

The `./config` directory is mounted to `/config` in the container.

### 4. Expose to Internet

Use ngrok for development:

```bash
ngrok http 8000
```

### 5. Configure Linear Webhook

1. Go to Linear → Settings → API → Webhooks
2. Click "New Webhook"
3. Set URL to `https://your-domain.com/webhooks/linear` (or ngrok URL + `/webhooks/linear`)
4. Copy the signing secret to `./config/papercut.toml` under `[providers.linear]` section
5. Select: **Issues** → **created**
6. Save

## 🖨️ Printer Setup

### Supported Printers

Tested on **Epson TM-T20III** (Monochrome Thermal POS Printer C31CH51001). Works with any ESC/POS compatible USB receipt printer (using python-escpos).

### USB Printer Setup

1. **Find your printer's USB IDs:**

   ```bash
   lsusb
   ```

   Look for your Epson printer (Vendor ID: `04b8`, Product ID varies by model)

2. **Configure in `./config/papercut.toml`:**

   ```toml
   [printer]
   usb_vendor_id = "0x04b8"
   usb_product_id = "0x0202"  # TM-T20III
   ```

3. **For Docker deployments:** USB devices are automatically mounted via `compose.yaml`

4. **Linux permissions:** You may need to add your user to the `lp` group:

   ```bash
   sudo usermod -a -G lp $USER
   ```

### Common Epson USB Product IDs

- TM-T20III: `0x0e28` or `0x0202` (varies by firmware/region)
- TM-T88III: `0x0e28`
- TM-T88V: `0x0202`
- TM-T88VI: `0x0228`

**Always verify your specific device:**

- macOS: `ioreg -p IOUSB -l -w 0 | grep -i "TM-T20III" -B 10 -A 5`
- Linux: `lsusb`

## Security

- HMAC-SHA256 signature verification
- Timestamp validation (prevents replay attacks)
- Only processes Issue creation webhooks

## Tech Stack

- FastAPI - Modern Python web framework
- Uvicorn - ASGI server
- uv - Fast package manager
- python-escpos - Receipt printer support
