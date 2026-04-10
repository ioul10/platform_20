"""
Scraper des news MASI 20 depuis les sites financiers marocains.
Sources : Medias24, Boursenews, Le Boursier.
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

KEYWORDS = ["masi", "masi 20", "masi20", "bourse", "marché à terme", "future", "indice"]


def fetch_masi20_news(limit: int = 20) -> list:
    """Récupère les news des 3 sources et filtre par mots-clés MASI."""
    results = []
    for fn in (_scrape_medias24, _scrape_boursenews, _scrape_leboursier):
        try:
            results.extend(fn())
        except Exception as e:
            print(f"[news] {fn.__name__} a échoué : {e}")

    # Filtrer par mots-clés
    filtered = [
        r for r in results
        if any(kw in (r["title"] + " " + r.get("summary", "")).lower() for kw in KEYWORDS)
    ]
    return filtered[:limit] if filtered else results[:limit]


def _scrape_medias24() -> list:
    url = "https://medias24.com/categorie/bourse/"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    items = []
    for article in soup.find_all("article")[:15]:
        title_el = article.find(["h2", "h3"])
        link_el = article.find("a", href=True)
        if title_el and link_el:
            items.append({
                "title": title_el.get_text(strip=True),
                "url": link_el["href"],
                "source": "Medias24",
                "date": datetime.now().strftime("%d/%m/%Y"),
                "summary": "",
            })
    return items


def _scrape_boursenews() -> list:
    url = "https://www.boursenews.ma/"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    items = []
    for a in soup.find_all("a", href=True)[:100]:
        title = a.get_text(strip=True)
        if len(title) > 25 and any(kw in title.lower() for kw in KEYWORDS):
            href = a["href"]
            if not href.startswith("http"):
                href = "https://www.boursenews.ma" + href
            items.append({
                "title": title,
                "url": href,
                "source": "Boursenews",
                "date": datetime.now().strftime("%d/%m/%Y"),
                "summary": "",
            })
    return items[:15]


def _scrape_leboursier() -> list:
    url = "https://www.leboursier.ma/"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    items = []
    for h in soup.find_all(["h2", "h3"])[:30]:
        a = h.find("a", href=True)
        if a:
            title = a.get_text(strip=True)
            if len(title) > 15:
                href = a["href"]
                if not href.startswith("http"):
                    href = "https://www.leboursier.ma" + href
                items.append({
                    "title": title,
                    "url": href,
                    "source": "Le Boursier",
                    "date": datetime.now().strftime("%d/%m/%Y"),
                    "summary": "",
                })
    return items[:15]
