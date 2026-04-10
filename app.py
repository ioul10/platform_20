"""
PLATFORM-20
Plateforme de suivi du MASI 20 et du marché à terme sur indice (Bourse de Casablanca)
"""
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

from scrapers.masi_scraper import fetch_masi20_data, fetch_futures_snapshot
from scrapers.news_scraper import fetch_masi20_news
from parsers.bulletin_parser import parse_bulletin_pdf
from report.weekly_report import generate_weekly_report

# ---------- Config ----------
st.set_page_config(
    page_title="PLATFORM-20",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Contrats futures suivis ----------
FUTURES_CONTRACTS = [
    "MASI20 FUTURE JUI26",
    "MASI20 FUTURE SEP26",
    "MASI20 FUTURE DEC26",
    "MASI20 FUTURE MAR27",
]

# ---------- Style ----------
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #0a2540, #1e90ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .subtitle { color: #64748b; font-size: 1rem; margin-top: 0; }
    .contract-card {
        background: #0f172a;
        border-radius: 10px;
        padding: 18px;
        color: white;
        text-align: center;
        border: 1px solid #1e293b;
    }
    .contract-name { font-size: 0.85rem; color: #94a3b8; letter-spacing: 1px; }
    .contract-price { font-size: 1.8rem; font-weight: 700; margin: 8px 0; }
    .up { color: #22c55e; }
    .down { color: #ef4444; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.markdown('<p class="main-title">PLATFORM-20</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">MASI 20 & Marché à terme sur indice — Bourse de Casablanca</p>',
    unsafe_allow_html=True,
)
st.divider()

# ---------- Sidebar navigation ----------
page = st.sidebar.radio(
    "Navigation",
    ["🏠 Accueil & Live", "📰 News MASI 20", "📄 Bilan Hebdomadaire"],
)
st.sidebar.divider()
st.sidebar.caption(f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ==================================================================
# PAGE 1 — ACCUEIL & LIVE
# ==================================================================
if page == "🏠 Accueil & Live":
    st.subheader("Snapshot du marché")

    # -- Futures cards --
    with st.spinner("Chargement des contrats futures..."):
        futures_data = fetch_futures_snapshot(FUTURES_CONTRACTS)

    cols = st.columns(4)
    for col, contract in zip(cols, FUTURES_CONTRACTS):
        data = futures_data.get(contract, {})
        price = data.get("price", "—")
        change = data.get("change_pct", 0.0)
        arrow = "▼" if change < 0 else "▲"
        css_class = "down" if change < 0 else "up"
        col.markdown(
            f"""
            <div class="contract-card">
                <div class="contract-name">{contract}</div>
                <div class="contract-price">{price}</div>
                <div class="{css_class}">{arrow} ({change:+.2f}%)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # -- MASI 20 spot --
    st.subheader("MASI 20 — Indice spot")
    col1, col2 = st.columns([2, 1])
    with st.spinner("Chargement du MASI 20..."):
        masi_df = fetch_masi20_data(days=30)

    if masi_df is not None and not masi_df.empty:
        with col1:
            st.line_chart(masi_df.set_index("date")["close"], height=320)
        with col2:
            last = masi_df.iloc[-1]
            prev = masi_df.iloc[-2] if len(masi_df) > 1 else last
            var = (last["close"] - prev["close"]) / prev["close"] * 100
            st.metric("Clôture", f"{last['close']:,.2f}", f"{var:+.2f}%")
            st.metric("Plus haut (30j)", f"{masi_df['close'].max():,.2f}")
            st.metric("Plus bas (30j)", f"{masi_df['close'].min():,.2f}")
    else:
        st.warning("Données MASI 20 indisponibles pour le moment.")

    st.divider()

    # -- Données de la semaine --
    st.subheader("Données de la semaine")
    if masi_df is not None and not masi_df.empty:
        week_df = masi_df.tail(5).copy()
        week_df.columns = [c.capitalize() for c in week_df.columns]
        st.dataframe(week_df, use_container_width=True, hide_index=True)

# ==================================================================
# PAGE 2 — NEWS
# ==================================================================
elif page == "📰 News MASI 20":
    st.subheader("Actualités MASI 20")
    st.caption("Sources : Medias24, Boursenews, Le Boursier, Bourse de Casablanca")

    with st.spinner("Récupération des news..."):
        news_items = fetch_masi20_news(limit=20)

    if not news_items:
        st.info("Aucune news récupérée. Vérifie ta connexion ou les sources.")
    else:
        for item in news_items:
            with st.container():
                st.markdown(f"### [{item['title']}]({item['url']})")
                st.caption(f"🗞️ {item['source']} — {item.get('date', 'Date inconnue')}")
                if item.get("summary"):
                    st.write(item["summary"])
                st.divider()

# ==================================================================
# PAGE 3 — BILAN HEBDO
# ==================================================================
elif page == "📄 Bilan Hebdomadaire":
    st.subheader("Génération du bilan hebdomadaire")
    st.caption(
        "Importe les bulletins quotidiens (PDF) de la semaine. "
        "Un à cinq fichiers sont acceptés — les jours manquants seront ignorés."
    )

    uploaded_files = st.file_uploader(
        "Glisser-déposer les bulletins PDF",
        type=["pdf"],
        accept_multiple_files=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        week_start = st.date_input(
            "Début de semaine",
            value=datetime.now() - timedelta(days=datetime.now().weekday()),
        )
    with col_b:
        week_end = st.date_input(
            "Fin de semaine",
            value=datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=4),
        )

    if st.button("🚀 Générer le bilan PDF", type="primary", disabled=not uploaded_files):
        with st.spinner("Analyse des bulletins en cours..."):
            parsed_days = []
            for f in uploaded_files:
                try:
                    data = parse_bulletin_pdf(f)
                    parsed_days.append(data)
                    st.success(f"✅ {f.name} — parsé")
                except Exception as e:
                    st.error(f"❌ {f.name} — erreur : {e}")

        if parsed_days:
            with st.spinner("Génération du rapport PDF..."):
                # Enrichir avec le MASI 20 spot
                masi_df = fetch_masi20_data(days=7)
                news_items = fetch_masi20_news(limit=10)
                output_path = generate_weekly_report(
                    parsed_days=parsed_days,
                    masi_df=masi_df,
                    news_items=news_items,
                    week_start=week_start,
                    week_end=week_end,
                    contracts=FUTURES_CONTRACTS,
                )
            st.success("Bilan généré avec succès !")
            with open(output_path, "rb") as f:
                st.download_button(
                    label="⬇️ Télécharger le bilan PDF",
                    data=f.read(),
                    file_name=f"bilan_hebdo_{week_start}_{week_end}.pdf",
                    mime="application/pdf",
                )
