#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NVDA 多空方案阶梯图（美股永续 · 3-5x）"""
import datetime, os

LAST = 224.41
PMAX, PMIN = 270.0, 188.0
YTOP, YBOT = 60.0, 470.0
SCALE = (YBOT - YTOP) / (PMAX - PMIN)

def y(p): return YTOP + (PMAX - p) * SCALE

COLORS = {"red": "#E24B4A", "gray": "#888780", "blue": "#378ADD", "green": "#639922", "purple": "#7F77DD"}
FILLS = {"red": "#FCEBEB", "blue": "#E6F1FB", "green": "#EAF3DE", "gray": "#F2F1ED"}

# (label, price, color, style)
DEC = [
    ("266 多目标(突破228量度)", 266.0, "green", "dash"),
    ("240 短线目标", 240.0, "green", "dash"),
    ("227.98 3月高 / 突破位", 227.98, "green", "line"),
    ("224.4 现价", LAST, "purple", "dash"),
    ("219 MA20 回踩支撑", 219.29, "green", "line"),
    ("209 MA50 首选多区", 209.28, "green", "line"),
    ("196 MA200 多止损 / 短目标", 196.27, "red", "line"),
]

def build(out="charts"):
    os.makedirs(out, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    path = os.path.join(out, "nvda_plan_20260903.svg")
    parts = []
    parts.append('<svg viewBox="0 0 680 520" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="NVDA 多空方案阶梯">')
    parts.append('<title>NVDA 多空方案阶梯</title>')
    # 多区 209-228
    parts.append(f'<rect x="120" y="{y(228):.1f}" width="260" height="{y(209)-y(228):.1f}" fill="{FILLS["green"]}"/>')
    # 观察区 196-209
    parts.append(f'<rect x="120" y="{y(209):.1f}" width="260" height="{y(196)-y(209):.1f}" fill="{FILLS["gray"]}"/>')
    # 突破区 228-270
    parts.append(f'<rect x="120" y="{y(270):.1f}" width="260" height="{y(228)-y(270):.1f}" fill="{FILLS["blue"]}"/>')
    for label, price, color, style in DEC:
        dash = ' stroke-dasharray="5,3"' if style == "dash" else ""
        w = "2" if style == "line" else "1.5"
        parts.append(f'<line x1="120" y1="{y(price):.1f}" x2="380" y2="{y(price):.1f}" stroke="{COLORS[color]}" stroke-width="{w}"{dash}/>')
        tc = COLORS[color] if color != "gray" else "#2C2C2A"
        parts.append(f'<text x="90" y="{y(price)+4:.1f}" font-size="13" text-anchor="end" fill="{tc}">{price:.0f}</text>')
        parts.append(f'<text x="390" y="{y(price)+4:.1f}" font-size="13" fill="#2C2C2A">{label}</text>')
    parts.append('<defs><marker id="ad" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#378ADD"/></marker><marker id="au" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto"><path d="M0,10 L10,5 L0,0 Z" fill="#639922"/></marker></defs>')
    parts.append(f'<path d="M 250 {y(219):.1f} L 250 {y(228):.1f}" stroke="#639922" stroke-width="2" fill="none" marker-end="url(#au)"/>')
    parts.append(f'<text x="258" y="{y(224):.1f}" font-size="12" fill="#639922">回踩MA20做多→228突破</text>')
    parts.append(f'<text x="250" y="20" font-size="15" font-weight="500" fill="#2C2C2A" text-anchor="middle">NVDA 多空方案阶梯（现价 {LAST:.0f} / 美股永续 3-5x）</text>')
    parts.append('</svg>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return path

if __name__ == "__main__":
    print(build())
