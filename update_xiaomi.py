import requests
import json
from datetime import datetime, timezone

YAHOO_QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=1810.HK"
FX_URL = "https://api.frankfurter.app/latest?from=HKD&to=EUR"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

def get_xiaomi_hkd():
    r = requests.get(YAHOO_QUOTE_URL, headers=HEADERS, timeout=15)
    # Debug minimal pour voir ce que Yahoo renvoie
    print("Yahoo status:", r.status_code)
    print("Yahoo content-type:", r.headers.get("Content-Type", ""))
    text_preview = r.text[:300].replace("\n", " ")
    print("Yahoo body preview:", text_preview)

    try:
        data = r.json()
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Réponse non JSON de Yahoo (code {r.status_code}) : {text_preview}"
        )

    try:
        result = data["quoteResponse"]["result"][0]
    except Exception:
        raise RuntimeError(f"Données Yahoo introuvables : {data}")

    price_hkd = result.get("regularMarketPrice")
    change_hkd = result.get("regularMarketChange")
    change_pct = result.get("regularMarketChangePercent")
    ts = result.get("regularMarketTime")

    if price_hkd is None:
        raise RuntimeError(f"Prix HKD introuvable : {result}")

    if ts:
        last_time = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    else:
        last_time = None

    return price_hkd, change_hkd, change_pct, last_time

def get_hkd_to_eur():
    r = requests.get(FX_URL, headers=HEADERS, timeout=15)
    print("FX status:", r.status_code)
    print("FX content-type:", r.headers.get("Content-Type", ""))
    text_preview = r.text[:200].replace("\n", " ")
    print("FX body preview:", text_preview)

    try:
        data = r.json()
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Réponse non JSON de Frankfurter (code {r.status_code}) : {text_preview}"
        )

    try:
        return float(data["rates"]["EUR"])
    except Exception:
        raise RuntimeError(f"Taux HKD/EUR introuvable : {data}")

def main():
    price_hkd, change_hkd, change_pct, last_time = get_xiaomi_hkd()
    rate_hkd_eur = get_hkd_to_eur()
    price_eur = price_hkd * rate_hkd_eur

    payload = {
        "symbol": "1810.HK",
        "price_hkd": price_hkd,
        "price_eur": price_eur,
        "change_hkd": change_hkd,
        "change_percent": change_pct,
        "last_trading_time": last_time,
        "rate_hkd_eur": rate_hkd_eur,
        "generated_at_utc": datetime.now(timezone.utc).isoformat()
    }

    with open("xiaomi.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print("xiaomi.json mis à jour :", payload)

if __name__ == "__main__":
    main()
