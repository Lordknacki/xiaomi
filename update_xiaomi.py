import requests
import json
from datetime import datetime, timezone

API_KEY = "MQVABCZ827XVHMA5"
SYMBOL = "1810.HK"

def get_xiaomi_quote_hkd():
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": SYMBOL,
        "apikey": API_KEY,
    }
    r = requests.get(url, timeout=30)
    data = r.json()

    if "Global Quote" not in data or "05. price" not in data["Global Quote"]:
        # Essayons en daily si GLOBAL_QUOTE ne renvoie rien
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": SYMBOL,
            "apikey": API_KEY,
            "outputsize": "compact",
        }
        r = requests.get(url, timeout=30)
        data = r.json()
        series = data.get("Time Series (Daily)")
        if not series:
            raise RuntimeError(f"Aucune donnée de cours pour {SYMBOL}: {data}")
        dates = sorted(series.keys())
        last_date = dates[-1]
        last_bar = series[last_date]
        price_hkd = float(last_bar["4. close"])
        prev_bar = series[dates[-2]] if len(dates) > 1 else None
        prev_close = float(prev_bar["4. close"]) if prev_bar else price_hkd
        change_hkd = price_hkd - prev_close
        change_pct = (change_hkd / prev_close) * 100 if prev_close != 0 else 0.0
        last_time = last_date + " 00:00:00"
        return price_hkd, change_hkd, change_pct, last_time

    q = data["Global Quote"]
    price_hkd = float(q["05. price"])
    change_hkd = float(q.get("09. change", 0.0))
    change_pct = float(q.get("10. change percent", "0").replace("%", "")) if q.get("10. change percent") else 0.0
    last_time = q.get("07. latest trading day", "")
    return price_hkd, change_hkd, change_pct, last_time

def get_hkd_to_eur_rate():
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": "HKD",
        "to_currency": "EUR",
        "apikey": API_KEY,
    }
    r = requests.get(url, timeout=30)
    data = r.json()
    fx = data.get("Realtime Currency Exchange Rate")
    if not fx or "5. Exchange Rate" not in fx:
        raise RuntimeError(f"Aucun taux HKD/EUR: {data}")
    return float(fx["5. Exchange Rate"])

def main():
    price_hkd, change_hkd, change_pct, last_time = get_xiaomi_quote_hkd()
    rate_hkd_eur = get_hkd_to_eur_rate()
    price_eur = price_hkd * rate_hkd_eur

    payload = {
        "symbol": SYMBOL,
        "price_hkd": price_hkd,
        "price_eur": price_eur,
        "change_hkd": change_hkd,
        "change_percent": change_pct,
        "last_trading_time": last_time,
        "rate_hkd_eur": rate_hkd_eur,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    with open("xiaomi.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("xiaomi.json mis à jour :", payload)

if __name__ == "__main__":
    main()
