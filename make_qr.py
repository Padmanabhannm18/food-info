"""Generate a QR code for a food business from business.json.

Two modes:

  1. Static (default) - the details are stored inside the QR itself.
     Works offline, but if you change a detail you must re-print the QR.

         python make_qr.py

  2. Editable (--url) - the QR only stores a link. The script also writes
     index.html (a details page built from business.json). Host that page at
     the link; to change details later, edit business.json, re-run, and
     re-upload index.html. The printed QR never changes.

         python make_qr.py --url https://yourname.github.io/food-info/

Add any extra details (phone, email, GSTIN, ...) as new lines in
business.json - they are picked up automatically in both modes.
"""

import argparse
import html
import json
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_M

HERE = Path(__file__).parent


def load_details(path):
    with open(path, encoding="utf-8") as f:
        return flatten(json.load(f))


def flatten(details):
    """Lift fields out of nested groups like "Contact": {"Phone": ...}."""
    flat = {}
    for k, v in details.items():
        if isinstance(v, dict):
            flat.update(flatten(v))
        else:
            flat[k] = v
    return flat


def plain_value(value):
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def html_value(key, value):
    if isinstance(value, list):
        return "<br>".join(html_value(key, v) for v in value)
    text = html.escape(str(value))
    key = key.lower()
    if "phone" in key or "mobile" in key or "whatsapp" in key:
        number = text.replace(" ", "")
        out = f'<a href="tel:{number}">{text}</a>'
        if "whatsapp" in key:
            out += f' &middot; <a href="https://wa.me/{number.lstrip("+")}">WhatsApp</a>'
        return out
    if "email" in key:
        return f'<a href="mailto:{text}">{text}</a>'
    return text


def make_qr(data, out_path):
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(out_path)


def write_html(details, out_path):
    title = html.escape(details.get("Business Name", "Business Details"))
    rows = "\n".join(
        f"    <tr><th>{html.escape(k)}</th><td>{html_value(k, v)}</td></tr>"
        for k, v in details.items()
    )
    out_path.write_text(f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #f5f5f0; margin: 0; padding: 24px 16px; color: #222; }}
    .card {{ max-width: 480px; margin: auto; background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
    h1 {{ font-size: 1.4rem; margin: 0 0 16px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 10px 0; border-top: 1px solid #eee; vertical-align: top; }}
    th {{ width: 40%; color: #666; font-weight: 500; }}
  </style>
</head>
<body>
  <div class="card">
  <h1>{title}</h1>
  <table>
{rows}
  </table>
  </div>
</body>
</html>
""", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--details", default=HERE / "business.json", type=Path, help="JSON file with the details")
    parser.add_argument("--url", help="link to encode instead of the details (editable mode)")
    parser.add_argument("--out", default=HERE / "business_qr.png", type=Path, help="output PNG file")
    args = parser.parse_args()

    details = load_details(args.details)

    if args.url:
        html_path = args.out.parent / "index.html"
        write_html(details, html_path)
        make_qr(args.url, args.out)
        print(f"QR (link to {args.url}) saved to {args.out}")
        print(f"Upload {html_path} so it is served at that link.")
    else:
        text = "\n".join(f"{k}: {plain_value(v)}" for k, v in details.items())
        make_qr(text, args.out)
        print(f"QR with details saved to {args.out}")
        print(text)


if __name__ == "__main__":
    main()
