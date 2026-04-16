# Papercut Print API

Print anything on a physical receipt printer by posting markdown content to a single endpoint.

## Endpoint

```
POST https://papercut.krabby.dev/webhooks/slack
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

- **Text width:** 48 characters per line
- **Image width:** 576 pixels max

All text is automatically word-wrapped to fit within 48 characters. Images must be sized to 576px wide or smaller by the caller.

## Two-Column Layout

To print key-value detail lines (like ticket metadata), use space padding to right-align values. The receipt is exactly **48 characters wide**. Pad each line so the total length is exactly 48 characters:

```
spaces = 48 - len(label) - len(value)
line = label + (" " * spaces) + value
```

Every line must be **exactly 48 characters total**. No more, no less. If a line is shorter, the value won't be right-aligned. If longer, it will wrap and break the layout.

### Example calculation

```
"ID:"      (3 chars) + "ENG-42"       (6 chars)  = 39 spaces → 48 total
"Team:"    (5 chars) + "Engineering" (11 chars)  = 32 spaces → 48 total
"Priority:"(9 chars) + "High"         (4 chars)  = 35 spaces → 48 total
"Status:"  (7 chars) + "In Progress" (11 chars)  = 30 spaces → 48 total
```

### Example output on the receipt

```
ID:                                       ENG-42
Team:                                Engineering
Priority:                                   High
Status:                              In Progress
```

### Implementation (pseudocode)

```python
WIDTH = 48

def format_detail(label: str, value: str) -> str:
    spaces = WIDTH - len(label) - len(value)
    return label + (" " * spaces) + value

details = [
    format_detail("ID:", "ENG-42"),
    format_detail("Team:", "Engineering"),
    format_detail("Priority:", "High"),
]

# Join with newlines — each line is exactly 48 chars
detail_block = "\n".join(details)
```

## Section Spacing

Use blank lines (`\n\n`) to separate visual sections. Without them, the receipt looks like one dense blob of text.

Required spacing for a well-formatted receipt:

```
[detail lines — no blank lines between them]
                                            ← blank line
# Title
                                            ← blank line
Description text, bullets, images, etc.
```

In the content string, this means:

```
...last detail line\n\n# Title\n\nDescription starts here...
```

## Supported Markdown

The `content` field accepts markdown. The following elements are rendered with receipt-appropriate formatting:

### Headers

```markdown
# H1 - Bold, double width, double height (use for titles)
## H2 - Bold, double height (use for section identifiers)
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

Anything that isn't a recognized markdown element prints as-is, with automatic word wrapping to 48 characters.

## Ticket Format Reference

To replicate the standard ticket receipt layout (matching the Linear ticket format), structure the content as follows:

### Structure

```
[two-column details — space-padded to 48 chars each]
[blank line]
[# Title as H1]
[blank line]
[description — markdown with bullets, bold, etc.]
```

### Full example payload

```json
{
  "content": "ID:                                       ENG-42\nTeam:                                Engineering\nPriority:                                   High\nStatus:                              In Progress\nProject:                             Papercut v2\nAssignee:                               Jane Doe\nCreator:                              John Smith\nLabels:                            bug, frontend\n\n# Fix login page CSS regression\n\nThe login button has a CSS regression causing it to overlap with the password field on mobile viewports under 375px.\n\n- Regression introduced in PR #127\n- Affects Safari and Chrome on iOS\n- **Blocking** v2.1 release",
  "footer_url": "https://google.com"
}
```

### What prints on the receipt

```
[logo]
[company header]
[timestamp]

ID:                                       ENG-42
Team:                                Engineering
Priority:                                   High
Status:                              In Progress
Project:                             Papercut v2
Assignee:                               Jane Doe
Creator:                              John Smith
Labels:                            bug, frontend

      FIX LOGIN PAGE CSS
         REGRESSION

The login button has a CSS regression
causing it to overlap with the password
field on mobile viewports under 375px.

• Regression introduced in PR #127
• Affects Safari and Chrome on iOS
• Blocking v2.1 release

          Scan for details:
          [QR code → google.com]
          [footer text]
```

### Building a ticket programmatically

```python
WIDTH = 48

def format_detail(label: str, value: str) -> str:
    spaces = WIDTH - len(label) - len(value)
    return label + (" " * spaces) + value

def build_ticket(
    details: list[tuple[str, str]],
    title: str,
    description: str,
) -> str:
    lines = [format_detail(label, value) for label, value in details]
    detail_block = "\n".join(lines)
    return f"{detail_block}\n\n# {title}\n\n{description}"

# Usage
content = build_ticket(
    details=[
        ("ID:", "ENG-42"),
        ("Team:", "Engineering"),
        ("Priority:", "High"),
        ("Status:", "In Progress"),
        ("Assignee:", "Jane Doe"),
        ("Labels:", "bug, frontend"),
    ],
    title="Fix login page CSS regression",
    description=(
        "The login button has a CSS regression.\n\n"
        "- Regression in PR #127\n"
        "- Affects Safari and Chrome\n"
        "- **Blocking** v2.1 release"
    ),
)
```

## Other Examples

### Minimal

```json
{"content": "Just a line of text"}
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
  "content": "Raw content only.\n\nNo header, no footer, no paper cut.\nUseful for chaining multiple prints.",
  "include_header": false,
  "include_footer": false,
  "cut": false
}
```

## Content Limits

Content is truncated at **2000 characters** (configurable server-side). Plan your content within this limit.

## curl Examples

Simple print:

```bash
curl -X POST https://papercut.krabby.dev/webhooks/slack \
  -H "Content-Type: application/json" \
  -d '{"content": "# Hello\n\nThis is a **test** print."}'
```

Ticket-style print with two-column details and QR code:

```bash
curl -X POST https://papercut.krabby.dev/webhooks/slack \
  -H "Content-Type: application/json" \
  -d '{
    "content": "ID:                                       ENG-42\nTeam:                                Engineering\nPriority:                                   High\nStatus:                              In Progress\n\n# Fix login page CSS regression\n\nThe login button overlaps the password field on mobile.\n\n- Regression in PR #127\n- **Blocking** v2.1 release",
    "footer_url": "https://google.com"
  }'
```
