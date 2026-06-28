"""
test_qr.py — unit tests for app/services/qr.py.

Pure: no DB, no HTTP, no FastAPI. We can't easily *decode* the QR without an
extra dependency, so we verify it is well-formed SVG and that distinct URLs
produce distinct codes (i.e. the URL actually drives the output).
"""
from app.services.qr import build_qr_svg


def test_returns_svg_markup():
    svg = build_qr_svg("http://localhost:8000/c/abc123")
    assert isinstance(svg, str)
    assert "<svg" in svg
    assert svg.strip().endswith("</svg>")


def test_distinct_urls_produce_distinct_codes():
    a = build_qr_svg("http://localhost:8000/c/aaaaaaaa")
    b = build_qr_svg("http://localhost:8000/c/bbbbbbbb")
    assert a != b


def test_same_url_is_deterministic():
    url = "http://localhost:8000/c/same"
    assert build_qr_svg(url) == build_qr_svg(url)
