# Papercut Print API

Print anything on a physical receipt printer by posting markdown content to a single endpoint.

## Endpoint

```
POST /webhooks/slack
Content-Type: application/json
```

No authentication required.

## Request Body

```json
{
  "content": "# Your markdown content here",
  "include_header": true,
  "include_footer": true,
  "footer_url": "https://example.com",
  "cut": true
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `content` | string | **Yes** | | Markdown-formatted content to print |
| `include_header` | boolean | No | `true` | Print the receipt header (logo, company name, address) |
| `include_footer` | boolean | No | `true` | Print the receipt footer (footer text, optional QR code) |
| `footer_url` | string | No | `null` | URL to encode as a QR code in the footer. If omitted, no QR code is printed. |
| `cut` | boolean | No | `true` | Cut the paper after printing |

The only required field is `content`. The simplest possible request:

```json
{"content": "Hello, world!"}
```

## Response

```json
{
  "status": "printed",
  "message": "Content sent to printer",
  "content_length": 123
}
```

## Receipt Dimensions

The printer is an 80mm thermal receipt printer. The printable area is:

- **Text width:** 48 characters per line (font A)
- **Image width:** 576 pixels max

All text is automatically word-wrapped to fit. You do not need to handle text wrapping. Images must be sized to 576px wide or smaller by the caller.

## Supported Markdown

The `content` field accepts markdown. The following elements are rendered with receipt-appropriate formatting:

### Headers

```markdown
# H1 - Bold, double width, double height
## H2 - Bold, double height
### H3 through H6 - Bold
```

### Inline Formatting

```markdown
**bold text** - Prints bold
*italic text* - Prints underlined (thermal printers have no italic)
```

### Bullet Lists

```markdown
- Item one
- Item two
* Also works with asterisks
```

### Inline Images

```markdown
![alt text](https://example.com/image.png)
```

Images are downloaded and printed inline within the content flow. They must be:
- **Max 576px wide** (the printer's printable area)
- A supported format: PNG, JPG, GIF, or BMP
- Accessible via a public URL

If an image fails to download or exceeds the max width, a text placeholder is printed instead.

### Plain Text

Anything that isn't a recognized markdown element prints as-is, with automatic word wrapping.

## Examples

### Minimal

```json
{"content": "Just a line of text"}
```

### Formatted Receipt

```json
{
  "content": "# Order #1042\n\n**Customer:** Jane Doe\n**Date:** Jan 15, 2026\n\n---\n\n- Widget x2\n- Gadget x1\n- Thingamajig x3\n\n**Total: $47.99**\n\n*Thank you for your purchase!*",
  "footer_url": "https://example.com/orders/1042"
}
```

This prints:

```
[logo]
[company header]

Jan 15, 2026 at 03:22 PM

        ORDER #1042

Customer:                Jane Doe
Date:              Jan 15, 2026

• Widget x2
• Gadget x1
• Thingamajig x3

Total: $47.99

Thank you for your purchase!

[QR code → https://example.com/orders/1042]
[footer text]
```

### With Inline Image

```json
{
  "content": "# Daily Report\n\n![chart](https://example.com/chart.png)\n\n**Summary:** All systems operational.",
  "include_footer": false
}
```

### No Header, No Footer, No Cut

```json
{
  "content": "This prints raw content only.\n\nNo header, no footer, no paper cut.\n\nUseful for chaining multiple prints on one continuous strip.",
  "include_header": false,
  "include_footer": false,
  "cut": false
}
```

## Content Limits

Content is truncated at **2000 characters** (configurable server-side). Plan your content within this limit.

## curl

```bash
curl -X POST http://localhost:8000/webhooks/slack \
  -H "Content-Type: application/json" \
  -d '{"content": "# Hello\n\nThis is a **test** print."}'
```
