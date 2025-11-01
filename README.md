# Papercut — _Issues you can touch_

Print your tickets on a real receipt printer.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Set Up Environment Variables

Create a `.env` file based on the `.env.example` in the project root.

> [!NOTE]
> Section 5 explains how to get your webhook URL and Linear signing secret.

All `COMPANY_` prefixed variables are optional, omitting them will fallback to default values, and passing an empty value will omit the line from the receipt.

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

**Docker (Optional):**

```bash
make compose-up
```

### 4. Expose to Internet

Use ngrok for development:

```bash
ngrok http 8000
```

### 5. Configure Linear Webhook

1. Go to Linear → Settings → API → Webhooks
2. Click "New Webhook"
3. Set URL to `https://your-domain.com/webhooks/linear` (or ngrok URL + `/webhooks/linear`)
4. Copy the signing secret to your `.env` file
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

2. **Configure in `.env`:**

   ```bash
   PRINTER_USB_VENDOR_ID=0x04b8
   PRINTER_USB_PRODUCT_ID=0x0202  # TM-T20III
   ```

3. **For Docker deployments:** USB devices are automatically mounted via compose.yaml

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
