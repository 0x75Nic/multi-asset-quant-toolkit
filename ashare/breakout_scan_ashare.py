"""A股 突破追单扫描器
核心数据: 直连东方财富 K线接口 (urllib, 不依赖 akshare 的 requests, 沙箱/代理环境更稳)
可选增强: akshare 取现货行情 / 北向资金 (失败不致命)
方法学: 复用加密突破扫描 — 近20日摆动高点 / ATR止损 / R:R目标 / 按波动率定杠杆
A股专属层: T+1 提醒 / 涨停板突破判定 / 北向资金 / 板块联动

用法:
    python breakout_scan_ashare.py 600519
    python breakout_scan_ashare.py 300750 600519
    python breakout_scan_ashare.py 比亚迪        # 名称模糊匹配(需 akshare)
依赖(仅增强项): pip install akshare
"""
import sys
import os
os.environ.setdefault("TQDM_DISABLE", "1")  # 关闭 akshare 内部的 tqdm 进度条噪声
import json
import time
import datetime
import urllib.request
import urllib.parse

# akshare 可选; 没有也能跑核心逻辑
try:
    import akshare as ak
    HAS_AK = True
except ImportError:
    ak = None
    HAS_AK = False


# ---------- 数据层 (直连东方财富, urllib) ----------
def secid_of(code: str) -> str:
    """沪市(60/68/9开头) -> 1.xxx ; 深市(00/30开头) -> 0.xxx"""
    if code.startswith(("60", "68", "9")):
        return f"1.{code}"
    return f"0.{code}"


def fetch_kline_eastmoney(code: str, start: str, end: str):
    """直连 push2his.eastmoney.com 取日K (qfq前复权). 返回 list[dict] 或 None"""
    secid = secid_of(code)
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56",   # 日期,开,收,高,低,量(验证可用组合)
        "klt": "101",          # 日K
        "fqt": "1",            # 前复权
        "secid": secid,
        "beg": start,
        "end": end,
    }
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urllib.parse.urlencode(params)
    # 注意: 不能带 Referer(quote.eastmoney.com), 该接口会据此反爬断连
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(4):
        try:
            raw = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
            j = json.loads(raw)
            if j.get("data") and j["data"].get("klines"):
                rows = []
                for line in j["data"]["klines"]:
                    p = line.split(",")
                    # 东方财富顺序: 日期,开,收,高,低,量,额,振幅,涨%,涨跌额,换手
                    rows.append({
                        "日期": p[0],
                        "开盘": float(p[1]),
                        "收盘": float(p[2]),
                        "最高": float(p[3]),
                        "最低": float(p[4]),
                        "成交量": float(p[5]),
                    })
                return rows
        except Exception:
            time.sleep(2.0)   # 东方财富按请求随机限流, 间隔规避
            continue
    return None


def fetch_kline_sina(code: str):
    """新浪财经日K (兜底源, 不受东方财富限流影响). 返回 list[dict] 或 None"""
    market = "sh" if code.startswith(("60", "68", "9")) else "sz"
    url = (f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
           f"CN_MarketData.getKLineData?symbol={market}{code}&scale=240&ma=no&datalen=320")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                                "Referer": "https://finance.sina.com.cn/"})
    try:
        raw = urllib.request.urlopen(req, timeout=15).read().decode("gbk", "ignore")
        arr = json.loads(raw)
        rows = [{
            "日期": r["day"],
            "开盘": float(r["open"]),
            "收盘": float(r["close"]),
            "最高": float(r["high"]),
            "最低": float(r["low"]),
            "成交量": float(r["volume"]),
        } for r in arr]
        return rows
    except Exception:
        return None


def get_klines(code: str):
    """多源兜底: 东方财富优先, 失败转新浪"""
    end = datetime.date.today().strftime("%Y%m%d")
    start = (datetime.date.today() - datetime.timedelta(days=400)).strftime("%Y%m%d")
    rows = fetch_kline_eastmoney(code, start, end)
    if rows:
        return rows, "东方财富"
    rows = fetch_kline_sina(code)
    if rows:
        return rows, "新浪财经"
    return None, None


def spot_akshare(code: str):
    if not HAS_AK:
        return None
    try:
        spot = ak.stock_zh_a_spot_em()
        r = spot[spot["代码"] == code]
        if not r.empty:
            rr = r.iloc[0]
            return dict(name=rr["名称"], last=float(rr["最新价"]), chg=float(rr["涨跌幅"]))
    except Exception:
        return None
    return None


def northbound_akshare():
    if not HAS_AK:
        return None
    try:
        flow = ak.stock_hsgt_fund_flow_summary_em()
        if flow is not None and not flow.empty:
            nb = flow[flow["名称"].str.contains("北向", na=False)]
            if not nb.empty:
                return nb.iloc[0]
    except Exception:
        return None
    return None


# ---------- 分析层 ----------
def lev_by_atr(atrpct):
    if atrpct < 3:
        return 3, "低波动"
    if atrpct < 5:
        return 2, "中波动"
    if atrpct < 8:
        return 1.5, "高波动"
    return 1, "极高波动"


def swing_points(highs, lows, n, look=2, win=45):
    sh, sl = [], []
    end = min(win, n - 2)
    for i in range(2, end):
        if highs[i] >= max(highs[i - look:i]) and highs[i] >= max(highs[i + 1:i + look + 1]):
            sh.append((i, highs[i]))
        if lows[i] <= min(lows[i - look:i]) and lows[i] <= min(lows[i + 1:i + look + 1]):
            sl.append((i, lows[i]))
    return sh, sl


def limit_pct(code: str) -> float:
    if code.startswith("30") or code.startswith("688"):
        return 0.20
    return 0.10


def name_to_code(name: str):
    if name.isdigit() and len(name) == 6:
        return name
    if HAS_AK:
        try:
            spot = ak.stock_zh_a_spot_em()
            hit = spot[spot["名称"].str.contains(name, na=False)]
            if not hit.empty:
                return hit.iloc[0]["代码"]
        except Exception:
            pass
    return None


def analyze(code: str):
    print("=" * 70)
    print(f"  A股 {code}")
    print("=" * 70)

    sp = spot_akshare(code)
    if sp:
        print(f"  名称 {sp['name']} | 现价 {sp['last']:.2f} | 今日 {sp['chg']:+.2f}%")
        last = sp["last"]
    else:
        print("  现货行情: 未获取(可选增强), 改用K线末值")
        last = None

    rows, src = get_klines(code)
    if not rows:
        print("  K线获取失败(东方财富+新浪均不可用)")
        return
    print(f"  数据源: {src}")
    rows.sort(key=lambda x: x["日期"])
    dates = [r["日期"] for r in rows]
    opens = [r["开盘"] for r in rows]
    closes = [r["收盘"] for r in rows]
    highs = [r["最高"] for r in rows]
    lows = [r["最低"] for r in rows]
    n = len(closes)
    if last is None:
        last = closes[0]
    print(f"  K线 {n} 根 (起始 {dates[0]} ~ {dates[-1]})")

    s20, s50 = sum(closes[:20]) / 20, sum(closes[:50]) / 50
    print(f"  SMA20 {s20:.2f} | SMA50 {s50:.2f} | 价格{'高于' if last > s20 else '低于'}SMA20")

    gains, losses = [], []
    for i in range(14):
        ch = closes[i] - closes[i + 1]
        gains.append(max(ch, 0)); losses.append(max(-ch, 0))
    ag, al = sum(gains) / 14, sum(losses) / 14
    rsi = 100 - 100 / (1 + ag / al) if al else 100
    tag = "(超买)" if rsi >= 70 else "(超卖)" if rsi <= 30 else "(中性)"
    print(f"  RSI14 {rsi:.1f} {tag}")

    trs = []
    for i in range(14):
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i + 1]), abs(lows[i] - closes[i + 1])))
    atr = sum(trs) / 14
    atrp = atr / last * 100
    print(f"  ATR14 {atr:.2f}  ({atrp:.2f}% of price)")

    hi60, lo60 = max(highs[:60]), min(lows[:60])
    hi20, lo20 = max(highs[:20]), min(lows[:20])
    print(f"  60日高 {hi60:.2f} 低 {lo60:.2f} | 20日高 {hi20:.2f} 低 {lo20:.2f}")
    print(f"  距60日高 {(last - hi60) / hi60 * 100:+.2f}%")

    sh, sl = swing_points(highs, lows, n)
    sh_str = ", ".join(f"{dates[i][5:]}@{v:.2f}" for i, v in sh[:5])
    sl_str = ", ".join(f"{dates[i][5:]}@{v:.2f}" for i, v in sl[:5])
    print(f"\n  摆动高点(阻力): {sh_str}")
    print(f"  摆动低点(支撑): {sl_str}")

    h10 = max(highs[1:11])
    lp = limit_pct(code)
    at_limit = (highs[0] >= closes[1] * (1 + lp) - 1e-6)
    trig = round(h10 * 1.004, 2)
    stop = round(trig - 1.0 * atr, 2)
    r = trig - stop
    lev, ltag = lev_by_atr(atrp)
    print(f"\n  ---- 突破追单参数 ----")
    print(f"  近10日高 {h10:.2f} (距现价 {(h10 - last) / last * 100:+.2f}%)")
    if at_limit:
        print(f"  ⚠ 今日触及涨停(±{lp*100:.0f}%), 突破需次日跳空确认; 触发设在涨停价上方")
    print(f"  触发     {trig:.2f}   (近10日高 +0.4%)")
    print(f"  止损     {stop:.2f}   (1ATR, 风险 {r / trig * 100:.2f}%)")
    print(f"  TP1 (2R) {trig + 2 * r:.2f}  (+{2 * r / trig * 100:.2f}%)")
    print(f"  TP2 (3R) {trig + 3 * r:.2f}  (+{3 * r / trig * 100:.2f}%)")
    print(f"  距触发还需涨 {(trig - last) / last * 100:+.2f}%")
    budget = 0.02 if atrp < 6 else 0.015
    notional = budget / (r / trig)
    print(f"  建议杠杆 {lev}x ({ltag}) | 账户10万参考: 名义 {100000 * notional:.0f}, 保证金 {100000 * notional / lev:.0f} (风险预算{budget*100:.1f}%)")
    print(f"  各杠杆下: " + " | ".join(
        f"{L}x 止损-{r / trig * 100 * L:.0f}% TP1+{2 * r / trig * 100 * L:.0f}%" for L in (1, 1.5, 2, 3)))

    print("\n  ---- A股 专属提示 ----")
    print(f"  • T+1 制度: 当日买入次日才可卖出, 追突破当日无法止损离场, 仓位需更保守")
    print(f"  • 涨跌停: 该板块限制 ±{lp*100:.0f}%, 封板时流动性枯竭, 追单需等开板/次日")
    nb = northbound_akshare()
    if nb is not None:
        print(f"  • 北向资金(今日): 净流入 {nb.get('资金净流入', 'n/a')} (沪股通 {nb.get('沪股通', 'n/a')} / 深股通 {nb.get('深股通', 'n/a')})")
    else:
        print("  • 北向资金: akshare不可用, 未获取")
    return dict(code=code, last=last, atrp=atrp, rsi=rsi, trig=trig, stop=stop, hi60=hi60)


if __name__ == "__main__":
    args = sys.argv[1:] or ["600519"]
    codes = []
    for a in args:
        c = name_to_code(a)
        if c is None:
            print(f"!! 无法解析标的: {a}")
            continue
        codes.append(c)
    if not codes:
        sys.exit(1)
    for c in codes:
        print()
        analyze(c)
        print()
