#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日美指数布局阶梯图：基于 Yahoo 实时位 + 双央行日历(9/16 FOMC, 9/18 BOJ)。"""
import os

COL = {"red": "#E24B4A", "gray": "#888780", "blue": "#378ADD", "green": "#639922", "purple": "#7F77DD"}
FILL = {"red": "#FCEBEB", "blue": "#E6F1FB", "green": "#EAF3DE"}

def make_chart(path, title, current, levels, zones, decision):
    prices = [l[1] for l in levels] + [current]
    PMAX = max(prices) + 200
    PMIN = min(prices) - 500
    YTOP, YBOT = 72.0, 472.0
    SCALE = (YBOT - YTOP) / (PMAX - PMIN)
    def y(p): return YTOP + (PMAX - p) * SCALE
    parts = []
    parts.append(f'<svg viewBox="0 0 710 560" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{title}">')
    parts.append(f'<title>{title}</title>')
    for ph, pl, fill in zones:
        parts.append(f'<rect x="120" y="{y(ph):.1f}" width="290" height="{y(pl)-y(ph):.1f}" fill="{FILL[fill]}"/>')
    for label, price, color, style in levels:
        dash = ' stroke-dasharray="5,3"' if style == "dash" else ""
        w = "2.4" if (color in ("green", "red", "blue") and style == "line") else "1.5"
        parts.append(f'<line x1="120" y1="{y(price):.1f}" x2="410" y2="{y(price):.1f}" stroke="{COL[color]}" stroke-width="{w}"{dash}/>')
        tc = COL[color] if color != "gray" else "#2C2C2A"
        parts.append(f'<text x="96" y="{y(price)+4:.1f}" font-size="13" text-anchor="end" fill="{tc}">{price:,.0f}</text>')
        parts.append(f'<text x="420" y="{y(price)+4:.1f}" font-size="12.5" fill="#2C2C2A">{label}</text>')
    # 现价标记（紫虚线已在 levels 中）
    parts.append(f'<text x="350" y="26" font-size="15" font-weight="600" fill="#2C2C2A" text-anchor="middle">{title}</text>')
    # 决策框
    by = 500
    for i, t in enumerate(decision):
        col = "#E24B4A" if i == 0 else "#2C2C2A"
        fw = "600" if i == 0 else "400"
        size = "13" if i == 0 else "12"
        parts.append(f'<text x="120" y="{by+i*17:.1f}" font-size="{size}" font-weight="{fw}" fill="{col}">{t}</text>')
    parts.append('</svg>')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print("WROTE", path)


# ===== 标普500 =====
make_chart(
    "charts/idx_sp500_20260902.svg",
    "标普500 布局阶梯（现 7631 / 9-16 FOMC 前）",
    7631.47,
    [
        ("7799 3月高(阻力背景)", 7798.99, "gray", "dash"),
        ("7713 MA20 阻力/确认线", 7712.85, "blue", "line"),
        ("7631 现价", 7631.47, "purple", "dash"),
        ("7566 MA50 支撑", 7565.89, "green", "line"),
        ("7267 3月低/买区下沿", 7266.99, "green", "dash"),
        ("7100 更深买区", 7100.0, "green", "dash"),
    ],
    [(7799, 7713, "red"), (7713, 7566, "blue"), (7566, 7100, "green")],
    [
        "决策：等 9/16 FOMC 落地，不抢跑",
        "① 守住 7566(MA50) 且重上 7713(MA20) = 多信号",
        "② 或砸至 7267-7100 企稳 = 分批买区",
        "③ 破 7100 不接，等 7000 整数/止跌K线",
        "风险：Fed 偏鹰加息=9/16 前压制造句",
    ],
)

# ===== 日经225 =====
make_chart(
    "charts/idx_nikkei_20260902.svg",
    "日经225 布局阶梯（现 64326 / 9-18 BOJ 前）",
    64325.64,
    [
        ("72366 3月高(阻力背景)", 72366.34, "gray", "dash"),
        ("66948 MA50 阻力", 66947.79, "gray", "line"),
        ("66397 MA20 阻力/确认线", 66396.84, "blue", "line"),
        ("64326 现价", 64325.64, "purple", "dash"),
        ("61434 3月低/买区下沿", 61434.19, "green", "dash"),
        ("60000 心理买区", 60000.0, "green", "dash"),
    ],
    [(72366, 66397, "red"), (66397, 61434, "blue"), (61434, 60000, "green")],
    [
        "决策：最弱，不接飞刀，等 9/18 BOJ 落地",
        "① BOJ 加息≈100%定价，日债10Y 3.0%新高",
        "② 等 61434-60000 恐慌企稳 或 重上 66400",
        "③ 日元走强+加息= exporter/科技承压",
        "风险：双均线下方+逼近3月低，下行未止",
    ],
)
