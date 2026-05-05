"""PDF/HTML report generation service."""

from __future__ import annotations

import html
from datetime import datetime
from typing import Any


def generate_html_report(detection_result: dict[str, Any], original_text: str) -> str:
    """Render a full plagiarism report as a self-contained HTML document."""
    overall = detection_result.get("overall_similarity", 0)
    risk = detection_result.get("risk_level", "low")
    flagged = detection_result.get("flagged_sentences", [])
    stats = detection_result.get("text_stats", {})
    ai = detection_result.get("ai_detection", {})

    risk_color = {
        "low": "#22c55e",
        "medium": "#eab308",
        "high": "#f97316",
        "critical": "#ef4444",
    }.get(risk, "#6b7280")

    flagged_rows = ""
    for i, f in enumerate(flagged, 1):
        score_pct = round(f["similarity_score"] * 100, 1)
        src = html.escape(str(f.get("matched_source", "N/A")))
        sent = html.escape(f["sentence"][:120])
        flagged_rows += f"""
        <tr>
            <td>{i}</td>
            <td>{sent}</td>
            <td>{score_pct}%</td>
            <td style="font-size:0.85em">{src}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PlagGuard Report</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background:#0f172a; color:#e2e8f0; padding:2rem; }}
  .container {{ max-width:900px; margin:0 auto; }}
  h1 {{ font-size:1.8rem; margin-bottom:0.5rem; }}
  .meta {{ color:#94a3b8; margin-bottom:2rem; }}
  .score-card {{ display:flex; gap:1.5rem; margin-bottom:2rem; flex-wrap:wrap; }}
  .card {{ background:#1e293b; border-radius:12px; padding:1.5rem; flex:1; min-width:180px; }}
  .card h3 {{ color:#94a3b8; font-size:0.85rem; text-transform:uppercase; margin-bottom:0.5rem; }}
  .card .value {{ font-size:2rem; font-weight:700; }}
  .risk {{ color:{risk_color}; }}
  table {{ width:100%; border-collapse:collapse; margin-top:1rem; }}
  th, td {{ padding:0.75rem 1rem; text-align:left; border-bottom:1px solid #334155; }}
  th {{ background:#1e293b; color:#94a3b8; font-size:0.8rem; text-transform:uppercase; }}
  .section {{ margin-top:2rem; }}
  .section h2 {{ font-size:1.3rem; margin-bottom:1rem; padding-bottom:0.5rem; border-bottom:1px solid #334155; }}
  .highlight {{ background:rgba(239,68,68,0.15); padding:2px 4px; border-radius:3px; }}
  .footer {{ margin-top:3rem; color:#64748b; font-size:0.8rem; text-align:center; }}
</style>
</head>
<body>
<div class="container">
  <h1>🛡️ PlagGuard Analysis Report</h1>
  <p class="meta">Generated on {datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")}</p>

  <div class="score-card">
    <div class="card">
      <h3>Overall Similarity</h3>
      <div class="value">{round(overall * 100, 1)}%</div>
    </div>
    <div class="card">
      <h3>Risk Level</h3>
      <div class="value risk">{risk.upper()}</div>
    </div>
    <div class="card">
      <h3>Sentences Flagged</h3>
      <div class="value">{len(flagged)}</div>
    </div>
    <div class="card">
      <h3>AI Probability</h3>
      <div class="value">{round(ai.get('ai_probability', 0) * 100, 1)}%</div>
    </div>
  </div>

  <div class="section">
    <h2>Text Statistics</h2>
    <div class="score-card">
      <div class="card"><h3>Words</h3><div class="value">{stats.get('word_count', 0)}</div></div>
      <div class="card"><h3>Sentences</h3><div class="value">{stats.get('sentence_count', 0)}</div></div>
      <div class="card"><h3>Avg Sentence Length</h3><div class="value">{stats.get('avg_sentence_length', 0)}</div></div>
      <div class="card"><h3>Readability</h3><div class="value">{stats.get('readability_score', 0)}</div></div>
    </div>
  </div>

  <div class="section">
    <h2>AI Detection Analysis</h2>
    <div class="score-card">
      <div class="card"><h3>Verdict</h3><div class="value">{'AI-Generated' if ai.get('is_ai_generated') else 'Likely Human'}</div></div>
      <div class="card"><h3>Perplexity</h3><div class="value">{ai.get('perplexity_score', 0)}</div></div>
      <div class="card"><h3>Burstiness</h3><div class="value">{ai.get('burstiness_score', 0)}</div></div>
    </div>
  </div>

  {"<div class='section'><h2>Flagged Sentences</h2><table><thead><tr><th>#</th><th>Sentence</th><th>Similarity</th><th>Matched Source</th></tr></thead><tbody>" + flagged_rows + "</tbody></table></div>" if flagged_rows else "<div class='section'><h2>Flagged Sentences</h2><p style='color:#22c55e'>✅ No sentences flagged — text appears original.</p></div>"}

  <div class="footer">
    <p>PlagGuard v1.0.0 — Plagiarism Detection & Text Humanization Platform</p>
  </div>
</div>
</body>
</html>"""
