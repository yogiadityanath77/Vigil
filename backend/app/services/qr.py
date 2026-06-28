"""
qr.py — render a crisis URL into a scannable QR code (SVG).

Kept isolated like transform.py: pure-ish (depends only on the `qrcode`
library), no DB, no HTTP, no FastAPI. Input a URL string, output SVG markup.

SVG (not PNG) on purpose: no Pillow/binary dependency, and it scales crisply
to any print size — the QR's real-world role is a printed card, not a thumbnail.

Error-correction level M (~15% recovery) is the qrcode default and is the right
trade-off for a card that may get scuffed: enough resilience without bloating
the module count, which keeps the code dense enough to scan on a weak phone.
"""
from __future__ import annotations

import io

import qrcode
from qrcode.image.svg import SvgPathImage


def build_qr_svg(url: str, *, box_size: int = 10, border: int = 2) -> str:
    """
    Render `url` as an SVG QR code and return the SVG markup as a string.

    box_size / border control the module pixel size and the quiet-zone width.
    The default border of 2 is below the spec-recommended 4-module quiet zone
    but scans reliably on phones and keeps the card compact; bump it for print
    if a scanner struggles.
    """
    img = qrcode.make(url, image_factory=SvgPathImage, box_size=box_size, border=border)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode("utf-8")
