# -*- coding: utf-8 -*-
"""UNI 入场阶梯图（OKX UNI-USDT 永续）。"""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "charts", "uni_plan_20260903.svg")

# 关键位（OKX 实时，2026-09-03）
LAST      = 5.759
H24       = 6.365   # 24h 高点（插针）
R_BREAK   = 6.00    # 突破阻力 / 3月高区
MA20      = 4.357
BUY_HI    = 4.80    # 首选多区上沿（Fib 0.5）
BUY_LO    = 4.50    # 首选多区下沿
MA50      = 4.038
STOP      = 3.90    # 止损（MA50 下方）
MA200     = 3.510
T1        = 6.80
T2        = 7.50

W = 680
H = 860
TOP = 40
BOT = H - 40
PAD_L = 150
PAD_R = 130

# 价格范围映射
P_MAX = 7.6
P_MIN = 3.3
def y(p):
    return BOT - (p - P_MIN) / (P_MAX - P_MIN) * (BOT - TOP)

def band(p_lo, p_hi, fill, label, lx):
    y1 = y(p_hi); y2 = y(p_lo)
    out = [f'<rect x="{PAD_L}" y="{y1:.1f}" width="{W-PAD_L-PAD_R}" height="{y2-y1:.1f}" fill="{fill}" opacity="0.85"/>']
    if label:
        ty = (y1+y2)/2
        out.append(f'<text x="{lx}" y="{ty+5:.1f}" font-size="15" font-weight="700" fill="#1a1a1a">{label}</text>')
    return "\n".join(out)

lines = []
# 背景
lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Microsoft YaHei, sans-serif">')
lines.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#f7f8fa"/>')

# 标题
lines.append(f'<text x="{W/2}" y="28" text-anchor="middle" font-size="20" font-weight="800" fill="#182233">UNI 入场阶梯图 · UNI-USDT 永续</text>')

# 多区（绿）
lines.append(band(BUY_LO, BUY_HI, "#d6f5dc", "首选多区 4.50–4.80", 12))
lines.append(band(STOP, BUY_LO, "#eaf7ee", "", 12))
# 止损下（红淡）
lines.append(band(MA200, STOP, "#fff0f0", "", 12))
# 突破上方（蓝）
lines.append(band(R_BREAK, H24, "#e8f1ff", "", 12))

# 价格网格 + 标签
grids = [MA200, STOP, MA50, BUY_LO, BUY_HI, MA20, LAST, R_BREAK, H24, T1, T2]
for p in grids:
    yy = y(p)
    lines.append(f'<line x1="{PAD_L}" y1="{yy:.1f}" x2="{W-PAD_R}" y2="{yy:.1f}" stroke="#cfd6e0" stroke-width="1"/>')
    lines.append(f'<text x="{W-PAD_R+8}" y="{yy+4:.1f}" font-size="13" fill="#6b7280">{p:.3f}</text>')

# 标注各均线/关键位
def tag(p, text, color, dx=0):
    yy = y(p)
    lines.append(f'<text x="{PAD_L-10}" y="{yy+4:.1f}" text-anchor="end" font-size="12.5" font-weight="700" fill="{color}">{text}</text>')

tag(MA200, "MA200 3.51", "#9aa3b2")
tag(MA50,  "MA50 4.04",  "#2f9e57")
tag(MA20,  "MA20 4.36",  "#2f9e57")
tag(BUY_HI,"首选多区↑", "#1f8f4d")
tag(R_BREAK,"突破阻力 6.00", "#2b6fe0")
tag(H24,   "24h插针 6.37", "#9aa3b2")

# 现价线（红）
yc = y(LAST)
lines.append(f'<line x1="{PAD_L}" y1="{yc:.1f}" x2="{W-PAD_R}" y2="{yc:.1f}" stroke="#e23b3b" stroke-width="2.5"/>')
lines.append(f'<rect x="{PAD_L-2}" y="{yc-9:.1f}" width="{W-PAD_L-PAD_R+4}" height="18" fill="none" stroke="#e23b3b" stroke-width="1.5"/>')
lines.append(f'<text x="{W/2}" y="{yc-13:.1f}" text-anchor="middle" font-size="14" font-weight="800" fill="#e23b3b">现价 5.759（逼近3月高，超买）</text>')

# 计划箭头 / 标注
def mark(p, text, color, anchor="start", tx=None):
    yy = y(p)
    xx = tx if tx else (PAD_L + (W-PAD_L-PAD_R)/2)
    lines.append(f'<text x="{xx}" y="{yy+4:.1f}" text-anchor="{anchor}" font-size="12.5" font-weight="700" fill="{color}">{text}</text>')

# 突破多
lines.append(f'<text x="{W/2}" y="{y(R_BREAK)-8:.1f}" text-anchor="middle" font-size="13" font-weight="800" fill="#2b6fe0">↑ 突破多：收盘站上6.00 看 6.80 → 7.50</text>')
lines.append(f'<text x="{W/2}" y="{y(T1)+16:.1f}" text-anchor="middle" font-size="12" fill="#2b6fe0">目标 T1 6.80 / T2 7.50</text>')
# 回踩多
lines.append(f'<text x="{W/2}" y="{y(BUY_HI)-6:.1f}" text-anchor="middle" font-size="13" font-weight="800" fill="#1f8f4d">← 首选多：回踩 4.50–4.80 分批接</text>')
lines.append(f'<text x="{W/2}" y="{y(BUY_LO)+16:.1f}" text-anchor="middle" font-size="11.5" fill="#2f9e57">更强买点 MA50 4.04；止损 3.90 下</text>')
# 现价提示
lines.append(f'<text x="{W/2}" y="{y(LAST)+20:.1f}" text-anchor="middle" font-size="12" font-weight="700" fill="#e23b3b">⚠ 现价追高：比MA20高32%，回撤风险大，不推荐</text>')
# 空
lines.append(f'<text x="{W/2}" y="{y(STOP)-6:.1f}" text-anchor="middle" font-size="12" fill="#b23b3b">仅跌破 4.04(MA50) 才反手空 → 3.51(MA200)</text>')

# 底部说明
lines.append(f'<text x="{W/2}" y="{H-14}" text-anchor="middle" font-size="11.5" fill="#6b7280">数据：OKX UNI-USDT 永续 · 2026-09-03 · 杠杆建议 2–3x（非25x）· 非农9/4 / FOMC 9/16 前减半仓</text>')

lines.append('</svg>')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("saved", OUT)
