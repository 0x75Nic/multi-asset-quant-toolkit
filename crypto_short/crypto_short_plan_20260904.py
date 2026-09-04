#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 加密短空触发阶梯图 (以 BTC 为代表, 2026-09-04)"""
import os
os.makedirs("charts", exist_ok=True)

# 数据 (OKX 实时 + Yahoo 宏观, 2026-09-04 11:30 拉取)
BTC = 80790      # 现价
H30 = 81320      # 30d高 / 14d高
SUP_24 = 77050   # 24h低 = 今日支撑
MA20 = 75594
MA50 = 68768

W, H = 680, 560
TOP, BOT = 70, 500
hi, lo = H30, MA50
def y(p): return BOT - (p - lo) / (hi - lo) * (BOT - TOP)

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 560" font-family="Segoe UI, Microsoft YaHei, sans-serif">')
svg.append(f'<rect width="680" height="560" fill="#0f1420"/>')

# 标题
svg.append(f'<text x="34" y="36" fill="#fff" font-size="20" font-weight="700">加密短空触发阶梯图 · BTC 代表 (2026-09-04)</text>')
svg.append(f'<text x="34" y="56" fill="#9aa4b2" font-size="13">现价 {BTC:,} · 反弹至近期高位 · 非农今晚 20:30 北京时间公布</text>')

# 网格
for p in [H30, SUP_24, MA20, MA50]:
    yy = y(p)
    svg.append(f'<line x1="40" y1="{yy}" x2="640" y2="{yy}" stroke="#2a3242" stroke-width="1" stroke-dasharray="4 4"/>')
    svg.append(f'<text x="644" y="{yy+4}" fill="#7d8694" font-size="11">{p:,}</text>')

# 不空区 (高位) 背景
svg.append(f'<rect x="40" y="{y(H30)}" width="600" height="{y(SUP_24)-y(H30)}" fill="#3a2a2a" opacity="0.35"/>')
svg.append(f'<text x="300" y="{(y(H30)+y(SUP_24))/2}" fill="#ff8a8a" font-size="14" font-weight="700" text-anchor="middle">❌ 逆势摸顶区 (现价附近, 不空)</text>')

# 顺空区 背景
svg.append(f'<rect x="40" y="{y(MA20)}" width="600" height="{y(MA50)-y(MA20)}" fill="#1f3a2a" opacity="0.4"/>')
svg.append(f'<text x="300" y="{(y(MA20)+y(MA50))/2}" fill="#7ee0a0" font-size="13" font-weight="700" text-anchor="middle">✅ 顺空目标区 (破位后看这里)</text>')

# 关键位节点
nodes = [
    (H30, "#ff6b6b", "30d / 14d 高位 81,320", y(H30)),
    (BTC, "#ffd166", f"现价 {BTC:,} (反弹高位, 不空)", y(BTC)),
    (SUP_24, "#ffa94d", f"今日支撑 / 24h低 {SUP_24:,} ← 短空触发线", y(SUP_24)),
    (MA20, "#4dd0e1", f"MA20 {MA20:,} (空第一目标)", y(MA20)),
    (MA50, "#7ee0a0", f"MA50 {MA50:,} (空第二目标)", y(MA50)),
]
for p, col, lbl, yy in nodes:
    svg.append(f'<circle cx="340" cy="{yy}" r="6" fill="{col}" stroke="#0f1420" stroke-width="2"/>')
    anchor = "end" if p >= SUP_24 else "start"
    tx = 330 if p >= SUP_24 else 350
    svg.append(f'<text x="{tx}" y="{yy-12 if p>=SUP_24 else yy+20}" fill="{col}" font-size="12.5" font-weight="600" text-anchor="{anchor}">{lbl}</text>')

# 短空路径箭头
ay = y(SUP_24); by = y(MA20); cy = y(MA50)
svg.append(f'<path d="M 340 {ay} C 400 {ay+20}, 400 {by-20}, 340 {by}" fill="none" stroke="#ff6b6b" stroke-width="2.5" marker-end="url(#arr)"/>')
svg.append(f'<path d="M 340 {by} C 400 {by+20}, 400 {cy-20}, 340 {cy}" fill="none" stroke="#ff6b6b" stroke-width="2.5" marker-end="url(#arr)"/>')

# 资金费 / 宏观注脚
svg.append(f'<text x="34" y="528" fill="#9aa4b2" font-size="12">多空拥挤度: BTC资金费+8.4%(温和) · ETH/HYPE/PEPE/BONK +11%(略偏多不过热) · SOL -0.4%(中性)</text>')
svg.append(f'<text x="34" y="546" fill="#9aa4b2" font-size="12">宏观: 10Y {4.76}(边际回落) · VIX 14.3(低位) · DXY 99.0 → 无系统性杀跌驱动, 非农决定方向</text>')

svg.append('<defs><marker id="arr" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b6b"/></marker></defs>')
svg.append('</svg>')

with open("charts/crypto_short_20260904.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg))
print("saved charts/crypto_short_20260904.svg")
