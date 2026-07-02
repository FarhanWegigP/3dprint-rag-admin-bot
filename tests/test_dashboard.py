"""Self-check for the dashboard HTML renderer. Run: python tests/test_dashboard.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api.dashboard import render_dashboard
from app.history import SessionOverview


def test_render_dashboard() -> None:
    sessions = [
        SessionOverview(
            session_id="628123<script>@lid",
            paused=True,
            ever_human=True,
            message_count=5,
            last_message="harga PLA berapa?",
            updated_at="2026-07-02T15:00:00",
            customer_phone=None,
        ),
        SessionOverview(
            session_id="628999@lid",
            paused=False,
            ever_human=False,
            message_count=2,
            last_message="",
            updated_at="2026-07-02T14:00:00",
            customer_phone="628999<script>",
        ),
    ]
    html = render_dashboard(sessions)

    # User-controlled content (session_id, message, phone) must be HTML-escaped — no raw injection.
    assert "<script>" not in html
    assert "&lt;script&gt;" in html

    assert "Admin nangani" in html
    assert "Bot aktif" in html
    assert "harga PLA berapa?" in html
    assert 'href="https://wa.me/628999' in html, "should render a wa.me link when phone is known"
    assert "nomor gak kedeteksi" in html, "should show fallback note when phone is unknown"


def test_render_dashboard_empty() -> None:
    html = render_dashboard([])
    assert "Belum ada sesi chat." in html


if __name__ == "__main__":
    test_render_dashboard()
    test_render_dashboard_empty()
    print("OK - all dashboard checks passed")
