import json, urllib.request
UA = {"User-Agent": "Mozilla/5.0"}
def series(sym, rng="6mo"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range={rng}"
    d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read())
    res = d["chart"]["result"][0]
    closes = [c for c in res["indicators"]["quote"][0]["close"] if c is not None]
    return closes[-1], closes

syms = {
    "S&P500": "^GSPC", "Nasdaq": "^IXIC", "NDX100": "^NDX",
    "Nikkei": "^N225", "VIX": "^VIX", "TNX(10Y%)": "^TNX", "DXY": "DX-Y.NYB",
}
for name, s in syms.items():
    try:
        last, cl = series(s)
        hi3 = max(cl[-60:]); lo3 = min(cl[-60:])
        ma20 = sum(cl[-20:]) / 20; ma50 = sum(cl[-50:]) / 50
        above20 = "▲above" if last > ma20 else "▼below"
        above50 = "▲above" if last > ma50 else "▼below"
        print(f"{name:10} {s:10} last={last:9.2f}  ma20={ma20:9.2f}{above20}  ma50={ma50:9.2f}{above50}  3moH={hi3:9.2f} 3moL={lo3:9.2f}")
    except Exception as e:
        print(name, "ERR", repr(e))
