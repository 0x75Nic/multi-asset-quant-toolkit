# -*- coding: utf-8 -*-
"""2026-09-05 非农后 · 入场观察阶梯图（BTC / XAU黄金 / NVDA+标普）

非农 8月新增 16.2万（预期 5.5万），失业率 4.1%，6/7月上修 5.5万。
9月加息概率升至 ~52-65%。下一催化剂：下周 CPI（决定 9/15-16 FOMC）+ BOJ 9/18。
"""
import os, json, urllib.request

UA = {"User-Agent": "Mozilla/5.0"}
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "charts")
os.makedirs(OUT_DIR, exist_ok=True)


def okx(u):
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read())


t = okx("https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT-SWAP")["data"][0]
BTC_H24, BTC_L24 = float(t["high24h"]), float(t["low24h"])

# ---------- 通用绘图 ----------
W, H = 680, 760
TOP, BOT = 46, H - 46
PAD_L, PAD_R = 158, 138


def build(title, sub, p_min, p_max, bands, grids, note, fname, out_h=H):
    b_top, b_bot = TOP, out_h - 46

    def y(p):
        return b_bot - (p - p_min) / (p_max - p_min) * (b_bot - b_top)

    L = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {out_h}" '
         f'font-family="Microsoft YaHei, sans-serif">',
         f'<rect x="0" y="0" width="{W}" height="{out_h}" fill="#f7f8fa"/>',
         f'<text x="{W/2}" y="26" text-anchor="middle" font-size="19" font-weight="800" fill="#182233">{title}</text>',
         f'<text x="{W/2}" y="44" text-anchor="middle" font-size="12.5" fill="#6b7280">{sub}</text>']

    for lo, hi, fill, label in bands:
        y1, y2 = y(hi), y(lo)
        L.append(f'<rect x="{PAD_L}" y="{y1:.1f}" width="{W-PAD_L-PAD_R}" height="{y2-y1:.1f}" '
                 f'fill="{fill}" opacity="0.9"/>')
        if label:
            L.append(f'<text x="12" y="{(y1+y2)/2+5:.1f}" font-size="14" font-weight="700" fill="#1a1a1a">{label}</text>')

    for p, name, tag, color in grids:
        yy = y(p)
        L.append(f'<line x1="{PAD_L}" y1="{yy:.1f}" x2="{W-PAD_R}" y2="{yy:.1f}" '
                 f'stroke="{color}" stroke-width="2.2"/>')
        L.append(f'<text x="{PAD_L-8}" y="{yy+5:.1f}" text-anchor="end" font-size="14.5" '
                 f'font-weight="800" fill="{color}">{p:,.4g}</text>')
        L.append(f'<text x="{W-PAD_R+8}" y="{yy+5:.1f}" font-size="13.5" font-weight="700" fill="{color}">{name}</text>')
        if tag:
            L.append(f'<text x="{W-PAD_R+8}" y="{yy+21:.1f}" font-size="11.5" fill="#6b7280">{tag}</text>')

    L.append(f'<text x="{W/2}" y="{out_h-14}" text-anchor="middle" font-size="11.5" fill="#9aa1ab">{note}</text>')
    L.append('</svg>')
    p = os.path.join(OUT_DIR, fname)
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("saved:", p)


# ---------- 1) BTC ----------
BTC_LAST, BTC_MA20, BTC_MA50 = 79477, 76341, 69060
build(
    "BTC 入场观察 · 非农后回落，等回踩 MA20",
    "BTC-USDT 永续 · 现价 79,477 ｜ 非农爆表后自 80,790 回落，仍守住 MA20",
    66000, 84000,
    [(BTC_MA20, 79000, "#d6f5dc", "回踩多区 76,300–79,000（MA20）"),
     (BTC_MA50, BTC_MA20, "#eaf7ee", "深度多区 69,060（MA50）"),
     (66000, BTC_MA50, "#fff0f0", "破位区"),
     (81000, 83500, "#e8f1ff", "")],
    [(83500, "前高压力", "突破才追", "#2563eb"),
     (BTC_H24, "24h 高", "", "#9aa1ab"),
     (BTC_LAST, "现价", "不追高", "#111827"),
     (79000, "多区上沿", "首接", "#16a34a"),
     (BTC_MA20, "MA20", "多空分界", "#16a34a"),
     (BTC_L24, "24h 低", "", "#9aa1ab"),
     (BTC_MA50, "MA50", "失效位", "#dc2626")],
    "策略：79,000–76,300 分批接多，止损 MA20 日线收破（约 75,800）；跌破 76,341 反手短空看 69,060。杠杆 2-3x",
    "entry_btc_20260905.svg")

# ---------- 2) 黄金 XAU ----------
XAU_LAST, XAU_MA20, XAU_MA50 = 4438.9, 4511.1, 4312.0
XAU_H24, XAU_L24 = 4497.8, 4369.7
build(
    "黄金 XAU 入场观察 · 非农跳水后等回踩 MA50",
    "XAU-USDT 永续 · 现价 4,438.9 ｜ 非农后自 4,497 跳水 70 美元，失守 MA20",
    4200, 4620,
    [(4340, 4380, "#d6f5dc", "首选多区 4,340–4,380（14日低+MA50上方）"),
     (4260, 4340, "#eaf7ee", "深度多区 4,260（原止损位翻支撑）"),
     (4200, 4260, "#fff0f0", "破位区"),
     (4511, 4620, "#e8f1ff", "")],
    [(4620, "压力", "", "#2563eb"),
     (XAU_MA20, "MA20", "站回才转强", "#2563eb"),
     (XAU_H24, "24h 高", "非农前高", "#9aa1ab"),
     (XAU_LAST, "现价", "不追不空", "#111827"),
     (XAU_L24, "24h 低", "回踩确认位", "#16a34a"),
     (4340, "多区下沿", "首接", "#16a34a"),
     (XAU_MA50, "MA50", "多头生命线", "#16a34a"),
     (4260, "失效位", "破则离场", "#dc2626")],
    "策略：4,340–4,380 分批接多，止损 4,260 下；站回 4,511(MA20) 才确认转强。CPI 前仓位减半",
    "entry_xau_20260905.svg")

# ---------- 3) 美股：NVDA + 标普 ----------
build(
    "美股入场观察 · NVDA 突破 / 标普卡在 MA20",
    "NVDA 230.94（3月新高）｜ 标普 7,724（贴 MA20 7,709）｜ 纳指 29,524",
    180, 250,
    [(210, 220, "#d6f5dc", "NVDA 回踩多区 210–220（MA50~MA20）"),
     (180, 196, "#fff0f0", "破位区（MA200 下）"),
     (231, 250, "#e8f1ff", "突破延续区")],
    [(250, "量度目标", "", "#2563eb"),
     (231.0, "3月高/突破位", "已突破，不追", "#2563eb"),
     (230.94, "NVDA 现价", "等回踩", "#111827"),
     (220.11, "NVDA MA20", "多区上沿", "#16a34a"),
     (210.58, "NVDA MA50", "首选多区", "#16a34a"),
     (196.68, "NVDA MA200", "失效位", "#dc2626"),
     (180, "极限支撑", "", "#9aa1ab")],
    "策略：NVDA 等回踩 220（MA20）或 210（MA50）分批多，止损 196 下。现价 231 已突破、不追高，杠杆 3-5x",
    "entry_us_20260905.svg", out_h=640)

# ---------- 4) 标普单独 ----------
build(
    "标普500 入场观察 · MA20 攻防战",
    "S&P 500 现价 7,724 ｜ MA20 7,709（贴身）｜ MA50 7,592 ｜ MA200 7,142",
    7000, 7900,
    [(7400, 7592, "#d6f5dc", "分批买区 7,400–7,592（MA50）"),
     (7000, 7400, "#eaf7ee", "深度买区（3月低 7,267）"),
     (7592, 7710, "#fffaf0", "攻防区"),
     (7710, 7900, "#e8f1ff", "")],
    [(7900, "压力", "", "#2563eb"),
     (7799, "3月高", "突破转强", "#2563eb"),
     (7724, "现价", "贴 MA20", "#111827"),
     (7710, "MA20", "多空分界", "#f59e0b"),
     (7592, "MA50", "买区上沿", "#16a34a"),
     (7400, "买区下沿", "分批接", "#16a34a"),
     (7142, "MA200", "极限支撑", "#dc2626")],
    "策略：守住 7,709(MA20) 且日线收在其上＝多信号；跌破则等 7,592/7,400 分批。FOMC 9/16 前仓位减半",
    "entry_spx_20260905.svg", out_h=640)
