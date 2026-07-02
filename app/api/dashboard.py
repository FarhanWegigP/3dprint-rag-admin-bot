"""Minimal read-only HTML dashboard — one table, no JS framework, auto-refreshes via meta tag."""
from __future__ import annotations

from html import escape

from app.history import SessionOverview

_STYLE = """
body { font-family: system-ui, sans-serif; margin: 2rem; background: #0f172a; color: #e2e8f0; }
h1 { font-size: 1.25rem; }
table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
th, td { text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #334155; vertical-align: top; }
th { color: #94a3b8; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; }
tr:hover { background: #1e293b; }
.badge { padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
.badge-active { background: #14532d; color: #bbf7d0; }
.badge-paused { background: #78350f; color: #fde68a; }
.msg { max-width: 32rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.muted { color: #64748b; font-size: 0.8rem; }
"""


def render_dashboard(sessions: list[SessionOverview]) -> str:
    rows = "\n".join(_render_row(s) for s in sessions) or (
        '<tr><td colspan="6" class="muted">Belum ada sesi chat.</td></tr>'
    )

    return f"""\
<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="10">
<title>3D Print Bot — Dashboard</title>
<style>{_STYLE}</style>
</head>
<body>
<h1>Status percakapan customer</h1>
<p class="muted">Auto-refresh tiap 10 detik.</p>
<table>
<thead>
<tr>
<th>Customer</th>
<th>Status</th>
<th>Pernah ditangani admin?</th>
<th>Jml pesan</th>
<th>Pesan terakhir</th>
<th>Aktivitas terakhir</th>
</tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</body>
</html>
"""


def _render_row(s: SessionOverview) -> str:
    if s.paused:
        status = '<span class="badge badge-paused">Admin nangani</span>'
    else:
        status = '<span class="badge badge-active">Bot aktif</span>'
    ever_human = "Ya" if s.ever_human else "Belum"

    if s.customer_phone:
        session_cell = (
            f'<a href="https://wa.me/{escape(s.customer_phone)}" target="_blank" rel="noopener">'
            f"{escape(s.customer_phone)} ↗</a>"
            f'<div class="muted">{escape(s.session_id)}</div>'
        )
    else:
        # session_id is a privacy "@lid" ID — the real phone number couldn't be resolved.
        session_cell = f'{escape(s.session_id)}<div class="muted">nomor gak kedeteksi</div>'

    return f"""\
<tr>
<td>{session_cell}</td>
<td>{status}</td>
<td>{ever_human}</td>
<td>{s.message_count}</td>
<td class="msg">{escape(s.last_message)}</td>
<td class="muted">{escape(s.updated_at)}</td>
</tr>"""
