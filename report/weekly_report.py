"""
Générateur du bilan hebdomadaire au format PDF.
Utilise reportlab pour la mise en page et matplotlib pour les graphiques.
"""
import os
import tempfile
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak,
)

CONTRACTS = ["JUI26", "SEP26", "DEC26", "MAR27"]
BRAND_COLOR = colors.HexColor("#0a2540")
ACCENT = colors.HexColor("#1e90ff")


def generate_weekly_report(
    parsed_days: list,
    masi_df: pd.DataFrame,
    news_items: list,
    week_start,
    week_end,
    contracts: list,
) -> str:
    """Génère le rapport PDF et retourne son chemin."""
    tmpdir = tempfile.mkdtemp()
    output_path = os.path.join(tmpdir, f"bilan_hebdo_{week_start}_{week_end}.pdf")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title", parent=styles["Title"],
        textColor=BRAND_COLOR, fontSize=22, spaceAfter=6,
    )
    h2 = ParagraphStyle(
        "h2", parent=styles["Heading2"],
        textColor=BRAND_COLOR, fontSize=14, spaceBefore=12, spaceAfter=6,
    )
    normal = styles["Normal"]

    story = []

    # -------- Header --------
    story.append(Paragraph("PLATFORM-20", title_style))
    story.append(Paragraph(
        f"Bilan hebdomadaire — du {week_start.strftime('%d/%m/%Y')} "
        f"au {week_end.strftime('%d/%m/%Y')}",
        styles["Heading3"],
    ))
    story.append(Paragraph(
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        normal,
    ))
    story.append(Spacer(1, 0.5 * cm))

    # -------- Section 1 : Valeurs importantes --------
    story.append(Paragraph("1. Valeurs clés de la semaine", h2))

    if masi_df is not None and not masi_df.empty:
        week = masi_df.tail(5)
        open_v = float(week.iloc[0]["close"])
        close_v = float(week.iloc[-1]["close"])
        high_v = float(week["close"].max())
        low_v = float(week["close"].min())
        var_pct = (close_v - open_v) / open_v * 100

        masi_table = [
            ["Indicateur", "Valeur"],
            ["MASI 20 — Ouverture semaine", f"{open_v:,.2f}"],
            ["MASI 20 — Clôture semaine", f"{close_v:,.2f}"],
            ["MASI 20 — Plus haut", f"{high_v:,.2f}"],
            ["MASI 20 — Plus bas", f"{low_v:,.2f}"],
            ["Variation hebdo", f"{var_pct:+.2f} %"],
        ]
        t = Table(masi_table, colWidths=[9 * cm, 6 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("Données MASI 20 indisponibles.", normal))

    story.append(Spacer(1, 0.4 * cm))

    # -------- Section 2 : Contrats futures --------
    story.append(Paragraph("2. Contrats à terme MASI 20", h2))

    # Agréger les futures depuis les bulletins parsés
    futures_agg = {c: {"prices": [], "volumes": [], "contracts": []} for c in CONTRACTS}
    for day in parsed_days:
        for c in CONTRACTS:
            f = day.get("futures", {}).get(c, {})
            if f.get("price") is not None:
                futures_agg[c]["prices"].append(f["price"])
            if f.get("volume") is not None:
                futures_agg[c]["volumes"].append(f["volume"])
            if f.get("contracts") is not None:
                futures_agg[c]["contracts"].append(f["contracts"])

    futures_table = [["Contrat", "Prix moy.", "Volume total", "Nb contrats", "Variation"]]
    for c in CONTRACTS:
        prices = futures_agg[c]["prices"]
        vols = futures_agg[c]["volumes"]
        cts = futures_agg[c]["contracts"]
        avg_price = sum(prices) / len(prices) if prices else 0
        tot_vol = sum(vols) if vols else 0
        tot_ct = sum(cts) if cts else 0
        var = ((prices[-1] - prices[0]) / prices[0] * 100) if len(prices) >= 2 else 0
        futures_table.append([
            f"MASI20 {c}",
            f"{avg_price:,.2f}" if avg_price else "—",
            f"{tot_vol:,.0f}" if tot_vol else "—",
            f"{tot_ct:,}" if tot_ct else "—",
            f"{var:+.2f} %" if var else "—",
        ])

    t2 = Table(futures_table, colWidths=[4.5 * cm, 2.5 * cm, 3 * cm, 2.5 * cm, 2.5 * cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.5 * cm))

    # -------- Section 3 : Graphiques --------
    story.append(Paragraph("3. Évolution graphique", h2))

    # Graphe 1 : MASI 20
    if masi_df is not None and not masi_df.empty:
        chart1 = _make_masi_chart(masi_df.tail(5), tmpdir)
        story.append(Image(chart1, width=16 * cm, height=7 * cm))
        story.append(Spacer(1, 0.3 * cm))

    # Graphe 2 : 4 contrats futures
    chart2 = _make_futures_chart(futures_agg, tmpdir)
    if chart2:
        story.append(Image(chart2, width=16 * cm, height=7 * cm))

    story.append(PageBreak())

    # -------- Section 4 : Tableau récap quotidien --------
    story.append(Paragraph("4. Récapitulatif quotidien", h2))
    recap = [["Date", "MASI 20 Clôture", "Variation"]]
    for day in parsed_days:
        d = day.get("date")
        d_str = d.strftime("%d/%m/%Y") if d else "—"
        masi = day.get("masi20", {})
        close = masi.get("close")
        var = masi.get("variation")
        recap.append([
            d_str,
            f"{close:,.2f}" if close else "—",
            f"{var:+.2f} %" if var else "—",
        ])
    t3 = Table(recap, colWidths=[5 * cm, 5 * cm, 5 * cm])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    story.append(t3)
    story.append(Spacer(1, 0.5 * cm))

    # -------- Section 5 : News marquantes --------
    if news_items:
        story.append(Paragraph("5. News marquantes de la semaine", h2))
        for item in news_items[:8]:
            story.append(Paragraph(
                f"<b>• {item['title']}</b><br/><font size=8 color='grey'>"
                f"{item['source']} — {item.get('date', '')}</font>",
                normal,
            ))
            story.append(Spacer(1, 0.2 * cm))

    # -------- Footer --------
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        "<font size=8 color='grey'>PLATFORM-20 — Rapport automatique. "
        "Les données présentées sont fournies à titre informatif uniquement.</font>",
        normal,
    ))

    doc.build(story)
    return output_path


def _make_masi_chart(df: pd.DataFrame, tmpdir: str) -> str:
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(df["date"], df["close"], marker="o", linewidth=2, color="#1e90ff")
    ax.fill_between(df["date"], df["close"], alpha=0.15, color="#1e90ff")
    ax.set_title("Évolution du MASI 20 sur la semaine", fontsize=12, color="#0a2540", fontweight="bold")
    ax.set_ylabel("Points")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    plt.tight_layout()
    path = os.path.join(tmpdir, "masi_chart.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def _make_futures_chart(futures_agg: dict, tmpdir: str) -> str:
    fig, ax = plt.subplots(figsize=(8, 3.5))
    colors_list = ["#1e90ff", "#22c55e", "#f59e0b", "#ef4444"]
    has_data = False
    for (c, data), col in zip(futures_agg.items(), colors_list):
        prices = data["prices"]
        if prices:
            ax.plot(range(1, len(prices) + 1), prices,
                    marker="o", linewidth=2, label=f"MASI20 {c}", color=col)
            has_data = True
    if not has_data:
        plt.close(fig)
        return None
    ax.set_title("Variations des 4 contrats à terme sur la semaine",
                 fontsize=12, color="#0a2540", fontweight="bold")
    ax.set_xlabel("Jour")
    ax.set_ylabel("Prix")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    path = os.path.join(tmpdir, "futures_chart.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
