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

The page uses the Mamees app theme. logo.jpg and favicon.png in this folder
are shown on the page if present.
"""

import argparse
import html
import json
from pathlib import Path
from urllib.parse import quote_plus

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


def is_url(value):
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def map_link(details):
    """Pop an explicit "Location" link if given, else search Maps for the address."""
    for key in list(details):
        if key.lower() in ("location", "map", "map link", "google maps") and is_url(details[key]):
            return details.pop(key)
    address = next((v for k, v in details.items() if "address" in k.lower()), None)
    if address:
        return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(plain_value(address))
    return None


def html_value(key, value, maps_url=None):
    if isinstance(value, list):
        return "\n".join(html_value(key, v, maps_url) for v in value)
    text = html.escape(str(value))
    key = key.lower()
    if "phone" in key or "mobile" in key or "whatsapp" in key:
        number = text.replace(" ", "")
        buttons = f'<a class="btn" href="tel:{number}">Call</a>'
        if "whatsapp" in key:
            buttons += f'<a class="btn wa" href="https://wa.me/{number.lstrip("+")}">WhatsApp</a>'
        return f'<div class="line"><span>{text}</span><span class="btns">{buttons}</span></div>'
    if "email" in key:
        return f'<div class="line"><a href="mailto:{text}">{text}</a></div>'
    if "address" in key and maps_url:
        return (f'<div class="line">{text}</div>'
                f'<a class="btn map" href="{html.escape(maps_url)}">Open in Google Maps</a>')
    if is_url(value):
        return f'<div class="line"><a href="{text}">{text}</a></div>'
    return f'<div class="line">{text}</div>'


def make_qr(data, out_path):
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(out_path)


def write_html(details, out_path):
    details = dict(details)
    name = html.escape(str(details.pop("Business Name", "Business Details")))
    maps_url = map_link(details)
    fields = "\n".join(
        f'    <div class="field"><div class="label">{html.escape(k)}</div>{html_value(k, v, maps_url)}</div>'
        for k, v in details.items()
    )
    # logo.jpg / favicon.png next to index.html are used if present
    folder = out_path.parent
    header = (f'<img class="logo" src="logo.jpg" alt="{name}">' if (folder / "logo.jpg").exists()
              else f'<h1>{name}</h1>')
    favicon = ('\n  <link rel="icon" type="image/png" href="favicon.png">'
               if (folder / "favicon.png").exists() else "")
    out_path.write_text(f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#6D060A">
  <title>{name}</title>{favicon}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Outfit:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    /* Mamees brand theme (same as the Mamees app): maroon, cream, gold */
    :root {{
      --primary: #6D060A; --primary-h: #8A0A0F; --primary-rgb: 109, 6, 10;
      --accent: #E4B05B; --bg: #FFFBF2; --logo-bg: #F6DFB6; --surface: #FFFFFF;
      --border: #F0DDBE; --text: #1A0604; --muted: #8C6255;
    }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: "Outfit", system-ui, sans-serif; background: var(--bg); margin: 0; padding: 20px 16px 32px; color: var(--text); line-height: 1.45; -webkit-font-smoothing: antialiased; }}
    .card {{ max-width: 460px; margin: auto; background: var(--surface); border: 1px solid var(--border); border-radius: 16px; overflow: hidden;
             box-shadow: 0 1px 4px rgba(var(--primary-rgb),.06), 0 4px 16px rgba(var(--primary-rgb),.06); }}
    header {{ background: var(--logo-bg); text-align: center; }}
    .logo {{ display: block; width: 100%; height: auto; }}
    h1 {{ font-family: "Cormorant Garamond", Georgia, serif; font-size: 2rem; color: var(--primary); margin: 0; padding: 24px 20px; }}
    .gold-line {{ height: 2px; background: linear-gradient(90deg, transparent, var(--accent), transparent); }}
    .fields {{ padding: 4px 20px 12px; }}
    .field {{ padding: 14px 0; border-top: 1px solid var(--border); }}
    .field:first-child {{ border-top: 0; }}
    .label {{ font-size: .72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin-bottom: 4px; }}
    .line {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; padding: 2px 0; word-break: break-word; }}
    .line + .line {{ margin-top: 6px; }}
    .btns {{ display: flex; gap: 6px; }}
    a {{ color: var(--primary); }}
    .btn {{ display: inline-block; padding: 6px 14px; border-radius: 10px; border: 1px solid var(--primary); font-size: .85rem; font-weight: 600; text-decoration: none; white-space: nowrap; }}
    .btn.wa {{ background: var(--primary); color: #fff; }}
    .btn.map {{ margin-top: 10px; }}
  </style>
</head>
<body>
  <div class="card">
    <header>{header}</header>
    <div class="gold-line"></div>
    <div class="fields">
{fields}
    </div>
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
