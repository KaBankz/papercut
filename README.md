# Linear Ticket Printer

Print out linear tickets on a thermal printer.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Set Up Environment Variables

Create a `.env` file based on the `.env.example` in the project root.

> [!NOTE]
> Sections 4 and 5 explain how to get your webhook URL and Linear signing secret.

All `COMPANY_` prefixed variables are optional, omitting them will fallback to default values, and passing an empty value will omit the line from the receipt.

### 3. Run the Server

**Development (with auto-reload):**

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Production:**

```bash
uv run python main.py
```

The server will start on `http://localhost:8000`

- Webhook endpoint: `POST http://localhost:8000/`
- Health check: `GET http://localhost:8000/`
- API docs: `http://localhost:8000/docs`

### 4. Expose to Internet

Linear needs to reach your webhook from the internet.

#### ngrok (for development)

```bash
# Install ngrok: https://ngrok.com/
ngrok http 8000
```

This gives you a public URL like: `https://abc123.ngrok.io`

### 5. Configure in Linear

1. Go to your Linear workspace settings
2. Navigate to **Settings → API → Webhooks**
3. Click **New Webhook**
4. Copy the signing secret and add it to your `.env` file as `LINEAR_SIGNING_SECRET`
5. Set the webhook URL to your server's public URL or your ngrok URL
6. Select these events:
   - ✅ **Issues**
7. Save!

## 📝 What It Does

When a **new issue is created** in Linear:

1. Linear sends a POST request to your webhook
2. The server verifies the signature and timestamp (security)
3. Prints a beautiful receipt on a thermal printer and ascii art! 🎫

**All other webhook types are silently ignored** - the server logs them and returns 200 OK to keep Linear happy, but doesn't process them.

### Security Features

- ✅ **HMAC-SHA256 signature verification** - Ensures webhooks are from Linear
- ✅ **Timestamp validation** - Prevents replay attacks (60-second window)
- ✅ **Timing-safe comparison** - Protects against timing attacks

## 🛠️ Tech Stack

- **FastAPI** - Modern, fast web framework
- **Uvicorn** - Lightning-fast ASGI server
- **uv** - Fast Python package manager

## 📖 Resources

- [Linear Webhooks Documentation](https://developers.linear.app/docs/graphql/webhooks)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
