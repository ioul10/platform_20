"""
Parser des bulletins PDF quotidiens de la Bourse de Casablanca.
Extrait : date, valeur MASI 20, et données des 4 contrats futures
(prix, volume, nombre de contrats).

NOTE : Le format exact des bulletins officiels peut varier. Les expressions
régulières ci-dessous sont génériques et à ajuster au premier bulletin réel.
"""
import pdfplumber
import re
from datetime import datetime

CONTRACTS = ["JUI26", "SEP26", "DEC26", "MAR27"]


def parse_bulletin_pdf(file) -> dict:
    """
    Extrait les données d'un bulletin PDF quotidien.
    Retourne un dict :
    {
        "date": datetime,
        "masi20": {"open": ..., "close": ..., "high": ..., "low": ..., "variation": ...},
        "futures": {
            "JUI26": {"price": ..., "volume": ..., "contracts": ...},
            ...
        },
        "raw_text": str,
    }
    """
    with pdfplumber.open(file) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    result = {
        "date": _extract_date(text),
        "masi20": _extract_masi20(text),
        "futures": _extract_futures(text),
        "raw_text": text,
    }
    return result


def _extract_date(text: str):
    """Cherche une date au format JJ/MM/AAAA ou AAAA-MM-JJ."""
    patterns = [
        r"(\d{2}/\d{2}/\d{4})",
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{2}-\d{2}-\d{4})",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            date_str = m.group(1)
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
    return datetime.now()


def _extract_masi20(text: str) -> dict:
    """Extrait les valeurs du MASI 20 depuis le texte du bulletin."""
    result = {"open": None, "close": None, "high": None, "low": None, "variation": None}

    # Recherche d'une ligne contenant "MASI 20" ou "MASI20"
    masi_section = re.search(
        r"MASI\s*20[^\n]*\n?([\d\s,\.\-\+%]+)",
        text,
        re.IGNORECASE,
    )
    if masi_section:
        numbers = re.findall(r"-?\d+[,\.]\d+", masi_section.group(0))
        numbers = [float(n.replace(",", ".")) for n in numbers]
        if len(numbers) >= 1:
            result["close"] = numbers[0]
        if len(numbers) >= 2:
            result["variation"] = numbers[1]
        if len(numbers) >= 4:
            result["open"], result["high"], result["low"], result["close"] = numbers[:4]
    return result


def _extract_futures(text: str) -> dict:
    """Extrait les données des 4 contrats futures."""
    futures = {}
    for echeance in CONTRACTS:
        # Cherche la section du contrat
        pattern = rf"(?:MASI20\s*FUTURE\s*)?{echeance}[^\n]*"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            line = match.group(0)
            # Extraire les nombres de la ligne
            numbers = re.findall(r"-?\d+(?:[,\.\s]\d+)*", line)
            cleaned = []
            for n in numbers:
                try:
                    cleaned.append(float(n.replace(" ", "").replace(",", ".")))
                except ValueError:
                    pass
            futures[echeance] = {
                "price": cleaned[0] if len(cleaned) >= 1 else None,
                "volume": cleaned[1] if len(cleaned) >= 2 else None,
                "contracts": int(cleaned[2]) if len(cleaned) >= 3 else None,
            }
        else:
            futures[echeance] = {"price": None, "volume": None, "contracts": None}
    return futures
