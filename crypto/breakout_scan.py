"""OKX 永续突破追单扫描器
用法: python breakout_scan.py UNI-USDT-SWAP [ENA-USDT-SWAP ...]
输出: 现价/均线/RSI/ATR/摆动高低点/近14日OHLC/突破追单参数(触发·止损·TP·杠杆·仓位)
"""
import urllib.request
import json
import datetime
import sys

BASE = "https://www.okx.com/api/v5"


def fetch(u):
    r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    return json.loads(urllib.request.urlopen(r, timeout=25).read().decode("utf-8", "ignore"))


def dstr(ms):
    return datetime.datetime.fromtimestamp(int(ms) / 1000, datetime.UTC).strftime("%m-%d")


def lev_by_atr(atrpct):
    if atrpct < 5:
        return 5, "低波动"
    if atrpct < 8:
        return 3, "中波动"
    if atrpct < 12:
        return 2, "高波动"
    return 1.5, "极高波动"


def analyze(inst):
    sym = inst.split("-")[0]
    print("=" * 66)
    print(f"  {sym}   ({inst})")
    print("=" * 66)

    t = fetch(f"{BASE}/market/ticker?instId={inst}")["data"][0]
    last, o24 = float(t["last"]), float(t["open24h"])
    print(f"  现价 {last:.4f} | 24h {(last-o24)/o24*100:+.2f}% | 24h高 {float(t['high24h']):.4f} 低 {float(t['low24h']):.4f}")

    c = fetch(f"{BASE}/market/candles?instId={inst}&bar=1D&limit=200")["data"]
    closes = [float(r[4]) for r in c]
    highs = [float(r[2]) for r in c]
    lows = [float(r[3]) for r in c]
    n = len(closes)
    print(f"  K线 {n} 根")

    s20, s50 = sum(closes[:20]) / 20, sum(closes[:50]) / 50
    print(f"  SMA20 {s20:.4f} | SMA50 {s50:.4f} | 价格{'高于' if last > s20 else '低于'}SMA20")

    gains, losses = [], []
    for i in range(14):
        ch = closes[i] - closes[i + 1]
        gains.append(max(ch, 0))
        losses.append(max(-ch, 0))
    ag, al = sum(gains) / 14, sum(losses) / 14
    rsi = 100 - 100 / (1 + ag / al) if al else 100
    tag = "(超买)" if rsi >= 70 else "(超卖)" if rsi <= 30 else "(中性)"
    print(f"  RSI14 {rsi:.1f} {tag}")

    try:
        c4 = fetch(f"{BASE}/market/candles?instId={inst}&bar=4H&limit=60")["data"]
        cl4 = [float(r[4]) for r in c4]
        g4, l4 = [], []
        for i in range(14):
            ch = cl4[i] - cl4[i + 1]
            g4.append(max(ch, 0))
            l4.append(max(-ch, 0))
        a4, b4 = sum(g4) / 14, sum(l4) / 14
        rsi4 = 100 - 100 / (1 + a4 / b4) if b4 else 100
        print(f"  4H RSI14 {rsi4:.1f}")
    except Exception:
        rsi4 = None

    trs = []
    for i in range(14):
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i + 1]), abs(lows[i] - closes[i + 1])))
    atr = sum(trs) / 14
    atrp = atr / last * 100
    print(f"  ATR14 {atr:.4f}  ({atrp:.2f}% of price)")

    hi60, lo60 = max(highs[:60]), min(lows[:60])
    hi20, lo20 = max(highs[:20]), min(lows[:20])
    print(f"  60日高 {hi60:.4f} 低 {lo60:.4f} | 20日高 {hi20:.4f} 低 {lo20:.4f}")
    print(f"  距60日高 {(last-hi60)/hi60*100:+.2f}%")

    print("  Fib 回撤(60日高→低):")
    for p in (0.236, 0.382, 0.5, 0.618, 0.786):
        print(f"    {p*100:5.1f}%  {hi60-(hi60-lo60)*p:.4f}")

    try:
        f = fetch(f"{BASE}/public/funding-rate?instId={inst}")["data"][0]
        fr = float(f["fundingRate"])
        print(f"  资金费率 年化 {fr*3*365*100:+.2f}%")
    except Exception:
        print("  资金费率 获取失败")

    print("\n  最近14日 (月-日  O / H / L / C):")
    for r in c[:14]:
        print(f"   {dstr(r[0])}  O {float(r[1]):>9.4f}  H {float(r[2]):>9.4f}  L {float(r[3]):>9.4f}  C {float(r[4]):>9.4f}")

    sh, sl_list = [], []
    for i in range(2, min(45, n - 2)):
        if highs[i] >= max(highs[i - 2:i]) and highs[i] >= max(highs[i + 1:i + 3]):
            sh.append((dstr(c[i][0]), highs[i]))
        if lows[i] <= min(lows[i - 2:i]) and lows[i] <= min(lows[i + 1:i + 3]):
            sl_list.append((dstr(c[i][0]), lows[i]))
    print(f"\n  摆动高点(阻力): {', '.join(f'{d}@{v:.4f}' for d, v in sh[:5])}")
    print(f"  摆动低点(支撑): {', '.join(f'{d}@{v:.4f}' for d, v in sl_list[:5])}")

    h10 = max(highs[1:11])
    trig = h10 * 1.004
    stop = trig - 1.0 * atr
    r = trig - stop
    lev, ltag = lev_by_atr(atrp)
    print(f"\n  ---- 突破追单参数 ----")
    print(f"  近10日高 {h10:.4f} (距现价 {(h10-last)/last*100:+.2f}%)")
    print(f"  触发     {trig:.4f}   (近10日高 +0.4%)")
    print(f"  止损     {stop:.4f}   (1ATR, 风险 {(r/trig*100):.2f}%)")
    print(f"  TP1 (2R) {trig+2*r:.4f}  (+{(2*r/trig*100):.2f}%)")
    print(f"  TP2 (3R) {trig+3*r:.4f}  (+{(3*r/trig*100):.2f}%)")
    print(f"  距触发还需涨 {(trig-last)/last*100:+.2f}%")
    budget = 0.02 if atrp < 12 else 0.015
    notional = budget / (r / trig)
    print(f"  建议杠杆 {lev}x ({ltag}) | 账户1000U参考: 名义 {1000*notional:.0f}U, 保证金 {1000*notional/lev:.0f}U (风险预算{ budget*100:.1f}%)")
    print(f"  各杠杆下: " + " | ".join(
        f"{L}x 止损-{r/trig*100*L:.0f}% TP1+{2*r/trig*100*L:.0f}%" for L in (1.5, 2, 3, 5)))
    return dict(sym=sym, last=last, atrp=atrp, rsi=rsi, rsi4=rsi4, trig=trig, stop=stop, hi60=hi60)


if __name__ == "__main__":
    insts = sys.argv[1:] or ["UNI-USDT-SWAP"]
    for i in insts:
        print()
        analyze(i)
        print()
