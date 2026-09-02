"""
gold_signals.py — 黄金宏观 + 持仓量化信号（免 key 数据栈）
数据来源（全部免费、沙箱可拉）:
  - Yahoo Finance: GC=F(黄金期货) / ^TNX(10Y美债收益率, 实际利率代理) / DX-Y.NYB(美元指数)
  - CFTC 离散化 COT: fut_disagg_txt_YYYY.zip 解析 COMEX 黄金 Managed Money 净多(择时信号)
可选(内置 FRED 免费 key, 可 env FRED_API_KEY 覆盖): DFII10(10Y TIPS 真实利率)
设计: 纯标准库, 无第三方依赖; COT 周级缓存避免每次重下 1.6MB。
"""
import json
import os
import sys
import csv
import io
import zipfile
import datetime
import urllib.request

UA = {"User-Agent": "Mozilla/5.0"}
YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"
CFTC_ZIP = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
COT_CACHE = "cot_gold_cache.json"
GOLD_NAME = "GOLD - COMMODITY EXCHANGE INC."
# FRED 免费 api_key（用户自取；可设环境变量 FRED_API_KEY 覆盖）
FRED_API_KEY = os.environ.get("FRED_API_KEY", "c83a6b1be0c1dca6f9da060ef0b7c107")


def _get(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def fetch_yahoo(symbol):
    """返回某 symbol 的实时价; 失败返回 None"""
    try:
        url = f"{YAHOO_BASE}{symbol}?interval=1d&range=1d"
        d = json.loads(_get(url))
        return float(d["chart"]["result"][0]["meta"]["regularMarketPrice"])
    except Exception as e:
        print(f"[!] Yahoo {symbol} 拉取失败: {e}", file=sys.stderr)
        return None


def fetch_macro():
    """拉宏观代理: 金价/收益率/美元; 返回 dict"""
    out = {}
    out["gold_yahoo"] = fetch_yahoo("GC=F")
    out["yield_10y"] = fetch_yahoo("%5ETNX")      # ^TNX
    out["dxy"] = fetch_yahoo("DX-Y.NYB")
    return out


def _parse_cot_year(year, cache_dir):
    """下载并解析某年 COT 离散化 ZIP, 返回黄金最新数周 Managed Money 净多序列"""
    cache = os.path.join(cache_dir, COT_CACHE)
    # 周级缓存: 同一年只下一次
    if os.path.exists(cache):
        try:
            with open(cache, encoding="utf-8") as f:
                c = json.load(f)
            if c.get("year") == year and c.get("series"):
                return c["series"]
        except Exception:
            pass
    url = CFTC_ZIP.format(year=year)
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
    z = zipfile.ZipFile(io.BytesIO(data))
    txt = [n for n in z.namelist() if n.endswith(".txt")][0]
    rows = list(csv.reader(io.TextIOWrapper(z.open(txt), encoding="latin-1")))
    hdr, N = rows[0], len(rows[0])
    gold = [r for r in rows[1:] if len(r) == N and r[0].upper() == GOLD_NAME]
    gold.sort(key=lambda r: r[2])

    def nz(r, i):
        try:
            return int(r[i].strip().replace(",", "") or 0)
        except Exception:
            return 0

    iL, iS, iOI = 13, 14, 7  # Managed Money 多/空/总持仓
    series = []
    for r in gold:
        net = nz(r, iL) - nz(r, iS)
        oi = nz(r, iOI)
        series.append({"date": r[2], "net": net, "oi": oi, "pct": round(net / oi * 100, 1) if oi else 0})
    with open(cache, "w", encoding="utf-8") as f:
        json.dump({"year": year, "series": series}, f)
    return series


def fetch_cot(cache_dir="."):
    """返回黄金 COT 信号 dict; 失败返回 None"""
    try:
        yr = datetime.date.today().year
        series = _parse_cot_year(yr, cache_dir)
        if not series:
            return None
        last = series[-1]
        prev = series[-2] if len(series) > 1 else last
        five_ago = series[-5] if len(series) >= 5 else series[0]
        return {
            "date": last["date"],
            "net": last["net"],
            "pct_of_oi": last["pct"],
            "oi": last["oi"],
            "wk_change": last["net"] - prev["net"],
            "five_wk_change": last["net"] - five_ago["net"],
        }
    except Exception as e:
        print(f"[!] CFTC COT 拉取失败: {e}", file=sys.stderr)
        return None


def fetch_fred_dfii10(api_key=None):
    """FRED 10Y TIPS 真实利率(黄金第一驱动). 默认用内置 FRED_API_KEY, 可传参覆盖."""
    api_key = api_key or FRED_API_KEY
    try:
        url = (f"https://api.stlouisfed.org/fred/series/observations"
               f"?series_id=DFII10&api_key={api_key}&file_type=json"
               f"&sort_order=desc&limit=30")
        d = json.loads(_get(url))
        # DFII10 部分日期无值(值为 "."), 取最近一个有效数字
        for ob in d["observations"]:
            try:
                v = float(ob["value"])
                return v
            except (ValueError, TypeError):
                continue
        return None
    except Exception as e:
        print(f"[!] FRED DFII10 拉取失败: {e}", file=sys.stderr)
        return None


def build_signal_block(macro, cot, fred_real_rate=None):
    """把宏观+持仓拼成 markdown 信号块"""
    L = []
    L.append("## 宏观 & 持仓量化信号")
    # 实际利率
    if fred_real_rate is not None:
        rr = fred_real_rate
        L.append(f"- **真实利率(10Y TIPS, FRED)**: `{rr:.2f}%` {'↑利空黄金' if rr>1.5 else '↓利好黄金'}")
    elif macro.get("yield_10y"):
        y = macro["yield_10y"]
        L.append(f"- **10Y 美债收益率(实际利率代理)**: `{y:.2f}%` — 利率上行=黄金头风, 下行=支撑")
    if macro.get("dxy"):
        d = macro["dxy"]
        L.append(f"- **美元指数 DXY**: `{d:.2f}` — 美元弱=黄金支撑, 强=压制")
    if macro.get("gold_yahoo"):
        L.append(f"- **现货参照(Yahoo GC=F)**: `${macro['gold_yahoo']:.1f}`")
    # COT
    if cot:
        trend = "连续加多(动能强但拥挤)" if cot["five_wk_change"] > 0 else "连续减多(动能弱)"
        L.append(
            f"- **CFTC 持仓(至 {cot['date']})**: Managed Money 净多 `{cot['net']:,}` 张 "
            f"({cot['pct_of_oi']}% of OI), 近5周变动 `{cot['five_wk_change']:+,}` → {trend}"
        )
        if cot["pct_of_oi"] > 35:
            L.append("  ⚠️ 净多占比偏高, 回调时投机盘踩踏风险上升")
    return "\n".join(L)


if __name__ == "__main__":
    cd = os.path.dirname(os.path.abspath(__file__))
    print("== fetch macro ==")
    macro = fetch_macro()
    print(json.dumps(macro, ensure_ascii=False))
    print("== fetch COT ==")
    cot = fetch_cot(cd)
    print(json.dumps(cot, ensure_ascii=False))
    print("== signal block ==")
    print(build_signal_block(macro, cot))
