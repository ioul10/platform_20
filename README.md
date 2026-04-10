# PLATFORM-20

Plateforme de suivi du **MASI 20** et du **marché à terme sur indice** de la Bourse de Casablanca.

## Fonctionnalités

- 🏠 **Accueil & Live** — Snapshot des 4 contrats à terme MASI 20 (JUI26, SEP26, DEC26, MAR27) + évolution du MASI 20 spot sur 30 jours
- 📰 **News MASI 20** — Agrégation des actualités depuis Medias24, Boursenews et Le Boursier
- 📄 **Bilan Hebdomadaire** — Upload des bulletins PDF quotidiens (1 à 5) → génération automatique d'un **rapport PDF** contenant :
  - Valeurs clés (MASI 20, contrats futures, volumes)
  - Graphique d'évolution du MASI 20 sur la semaine
  - Graphique des variations des 4 contrats futures
  - Tableau récapitulatif quotidien
  - News marquantes de la semaine

## Structure du projet

```
platform-20/
├── app.py                      # Application Streamlit principale
├── requirements.txt
├── .streamlit/config.toml
├── scrapers/
│   ├── masi_scraper.py         # Scraping MASI 20 + contrats futures
│   └── news_scraper.py         # Scraping news Medias24 / Boursenews / Le Boursier
├── parsers/
│   └── bulletin_parser.py      # Extraction données depuis bulletins PDF
├── report/
│   └── weekly_report.py        # Génération du rapport PDF hebdomadaire
└── data/
```

## Lancement en local

```bash
git clone https://github.com/<ton-user>/platform-20.git
cd platform-20
pip install -r requirements.txt
streamlit run app.py
```

L'application sera accessible sur http://localhost:8501

## Déploiement sur Streamlit Community Cloud

1. Pousse le projet sur un repo GitHub public
2. Va sur [share.streamlit.io](https://share.streamlit.io)
3. Connecte ton compte GitHub
4. Clique sur **New app** → sélectionne le repo, la branche `main`, et le fichier `app.py`
5. Clique sur **Deploy** — Streamlit installe automatiquement les dépendances depuis `requirements.txt`

## Notes importantes

### Sources de données

- **MASI 20 spot** : tente d'abord `yfinance` (tickers `^MASI`, `MASI.CS`…), puis fallback sur le scraping de `casablanca-bourse.com`. En dernier recours, des données simulées sont utilisées pour que l'app reste fonctionnelle.
- **Contrats futures** : scraping de la page dérivés de la Bourse de Casablanca. En cas d'échec, valeurs de démo basées sur la capture du 10/04/2026.
- **News** : scraping HTML des 3 sites marocains. Les sélecteurs CSS sont génériques et peuvent nécessiter un ajustement si les sites changent leur structure.

### Parsing des bulletins PDF

Le parser `bulletin_parser.py` utilise des expressions régulières génériques. **Au premier bulletin réel testé**, il faudra probablement ajuster les regex pour matcher précisément le format officiel (position du MASI 20, libellés exacts des contrats, etc.).

### Limitations

- Pas d'API officielle → le scraping peut casser si les sites sources modifient leur HTML
- Streamlit Community Cloud a un quota gratuit (1 app active, 1 Go RAM) — suffisant pour cet usage
- Les bulletins PDF doivent être textuels (pas scannés). Pour du scanné, ajouter `pytesseract` + OCR.

## Roadmap possible

- [ ] Cache des données scraped (Streamlit `@st.cache_data`)
- [ ] Planificateur automatique (GitHub Actions) pour scraper 1×/jour et archiver
- [ ] Historique des rapports hebdo
- [ ] Alertes email sur variations importantes
- [ ] Ajout du volume et de l'open interest sur les graphiques futures

## Licence

Usage personnel. Les données affichées sont fournies à titre informatif uniquement et ne constituent pas un conseil d'investissement.
