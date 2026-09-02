#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黄金实时快照 + 技术位简报 + 价格阶梯图，可选推送 PushPlus。
用法:
  python gold_snapshot.py                            # 仅打印报告
  python gold_snapshot.py --push --token X           # 推送（token 不硬编码）
  python gold_snapshot.py --extra-file nfp.txt       # 合并宏观补充
  python gold_snapshot.py --chart                    # 生成阶梯图 SVG 到 ./charts
  python gold_snapshot.py --chart --chart-dir E:/.../charts
  python gold_snapshot.py --push --token X --chart-link https://raw.../x.svg  # 报告内嵌图
"""
import json
import sys
import base64
import urllib.request
import urllib.error
import urllib.parse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gold_signals

INST = "XAU-USDT-SWAP"
ZONE_LO = 4300.0
ZONE_HI = 4698.8
UA = {"User-Agent": "Mozilla/5.0"}

# 方案决策位（来自分析报告，硬编码）
DEC_BASE = [
    ("4520 止损 SL·空破趋势", 4520.0, "red", "line"),
    ("4499 0.5 Fib·中线阻力", 4499.0, "gray", "dash"),
    ("4463 0.382 Fib·空上沿", 4463.0, "gray", "dash"),
    ("4440 空入场区（反弹至此空）", 4440.0, "blue", "line"),
    ("4325 多入场区（限价挂单）", 4325.0, "green", "line"),
    ("4300 多空目标/关键支撑", 4300.0, "green", "dash"),
    ("4260 多止损/下破不补", 4260.0, "red", "line"),
]


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def fetch():
    t = get(f"https://www.okx.com/api/v5/market/ticker?instId={INST}")["data"][0]
    cand = get(f"https://www.okx.com/api/v5/market/candles?instId={INST}&bar=1D&limit=20")["data"]
    fr = get(f"https://www.okx.com/api/v5/public/funding-rate?instId={INST}")["data"][0]
    oi = get(f"https://www.okx.com/api/v5/public/open-interest?instId={INST}")["data"][0]
    return t, cand, fr, oi


def fib(p):
    return ZONE_LO + (ZONE_HI - ZONE_LO) * p


def build_report(t, cand, fr, oi):
    last = float(t["last"])
    high24 = float(t["high24h"])
    low24 = float(t["low24h"])
    hi20 = max(float(r[2]) for r in cand)
    lo20 = min(float(r[3]) for r in cand)
    fr_annual = float(fr["fundingRate"]) * 3 * 365 * 100
    oi_xau = float(oi.get("oiCcy", oi.get("oi", 0)))
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    ts = now.strftime("%Y-%m-%d %H:%M")

    def pct(a, b):
        return (a - b) / b * 100

    L = []
    L.append(f"# 黄金实时快照（{ts} 北京）")
    L.append("")
    L.append(f"**现价：{last:.1f}**  ｜ 24h 区间 {low24:.1f}–{high24:.1f}")
    L.append(f"20日高 {hi20:.1f} ／ 20日低 {lo20:.1f}")
    L.append(f"资金费年化 ≈ {fr_annual:.1f}%（多头{'偏拥挤' if fr_annual>30 else '中性'}） ｜ OI ≈ {oi_xau/1e4:.1f}万 XAU 合约")
    L.append("")
    L.append("## 斐波技术位（区间 4300→4698.8）")
    for name, lv in [
        ("阻力 0.236", fib(0.764)),
        ("阻力 0.382", fib(0.618)),
        ("阻力 0.5", fib(0.5)),
        ("支撑 0.786", fib(0.214)),
        ("支撑 0.886 / 起涨点", fib(0.114)),
        ("中线买点区下沿", 4200.0),
    ]:
        d = pct(last, lv)
        tag = "▲上方" if d > 0 else "▼下方"
        L.append(f"- {name}：**{lv:.1f}**（现价 {tag} {abs(d):.1f}%）")
    L.append("")
    L.append("## 短线判断")
    if last < fib(0.214):
        L.append("- 已跌破 0.786 支撑，逼近 4300 大支撑；非农前偏弱，谨慎接多。")
    elif last < fib(0.5):
        L.append("- 处于 0.786 支撑与 0.5 半分位之间，短线偏弱但未破关键支撑。")
    else:
        L.append("- 反弹至半分位上方，短线有所修复。")
    L.append("")
    L.append("_数据来源：OKX XAU-USDT-SWAP 公开 API_")
    return "\n".join(L)


# ---- 价格阶梯图 ----
PMAX, PMIN = 4525.0, 4260.0
YTOP, YBOT = 60.0, 460.0
SCALE = (YBOT - YTOP) / (PMAX - PMIN)


def y(p):
    return YTOP + (PMAX - p) * SCALE


COLORS = {"red": "#E24B4A", "gray": "#888780", "blue": "#378ADD", "green": "#639922", "purple": "#7F77DD"}
FILLS = {"red": "#FCEBEB", "blue": "#E6F1FB", "green": "#EAF3DE"}


def build_chart(last, outdir="charts"):
    os.makedirs(outdir, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    fname = "xau_latest.svg"
    path = os.path.join(outdir, fname)
    items = DEC_BASE[:4] + [(f"{last:.0f} 现价", last, "purple", "dash")] + DEC_BASE[4:]
    parts = []
    parts.append('<svg viewBox="0 0 680 520" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="XAU 多空方案阶梯">')
    parts.append('<title>XAU 多空方案阶梯</title>')
    parts.append(f'<rect x="120" y="{y(PMAX):.1f}" width="260" height="{y(4460)-y(PMAX):.1f}" fill="{FILLS["red"]}"/>')
    parts.append(f'<rect x="120" y="{y(4460):.1f}" width="260" height="{y(4440)-y(4460):.1f}" fill="{FILLS["blue"]}"/>')
    parts.append(f'<rect x="120" y="{y(4440):.1f}" width="260" height="{y(4325)-y(4440):.1f}" fill="{FILLS["green"]}"/>')
    parts.append(f'<rect x="120" y="{y(4325):.1f}" width="260" height="{y(PMIN)-y(4325):.1f}" fill="{FILLS["red"]}"/>')
    for label, price, color, style in items:
        dash = ' stroke-dasharray="5,3"' if style == "dash" else ""
        w = "2" if style == "line" else "1.5"
        parts.append(f'<line x1="120" y1="{y(price):.1f}" x2="380" y2="{y(price):.1f}" stroke="{COLORS[color]}" stroke-width="{w}"{dash}/>')
        tc = COLORS[color] if color != "gray" else "#2C2C2A"
        parts.append(f'<text x="90" y="{y(price)+4:.1f}" font-size="13" text-anchor="end" fill="{tc}">{price:.0f}</text>')
        parts.append(f'<text x="390" y="{y(price)+4:.1f}" font-size="13" fill="#2C2C2A">{label}</text>')
    parts.append('<defs><marker id="ad" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#378ADD"/></marker><marker id="au" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto"><path d="M0,10 L10,5 L0,0 Z" fill="#639922"/></marker></defs>')
    parts.append(f'<path d="M 240 {y(4450):.1f} L 240 {y(4300):.1f}" stroke="#378ADD" stroke-width="2" fill="none" marker-end="url(#ad)"/>')
    parts.append(f'<path d="M 300 {y(4325):.1f} L 300 {y(4408):.1f}" stroke="#639922" stroke-width="2" fill="none" marker-end="url(#au)"/>')
    parts.append(f'<text x="340" y="{y(4370):.1f}" font-size="12" fill="#378ADD">做空目标 4300</text>')
    parts.append(f'<text x="245" y="{y(4366):.1f}" font-size="12" fill="#639922">多 TP1 4408</text>')
    parts.append(f'<text x="250" y="20" font-size="15" font-weight="500" fill="#2C2C2A" text-anchor="middle">XAU 多空方案阶梯（现价 {last:.0f} / 非农前）</text>')
    parts.append('</svg>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return path


def pushplus(token, title, content):
    url = (
        "http://www.pushplus.plus/send"
        f"?token={token}&title={urllib.parse.quote(title)}"
        f"&content={urllib.parse.quote(content)}&template=markdown"
    )
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")


# ---- 用 GitHub 当图床：上传 SVG，返回 raw 链接 ----
def upload_chart_github(svg_path, gh_token, repo="0x75Nic/multi-asset-quant-toolkit", branch="master"):
    api = f"https://api.github.com/repos/{repo}/contents"
    fname = os.path.basename(svg_path)
    remote_path = f"gold-monitor/charts/{fname}"
    url = f"{api}/{remote_path}"
    with open(svg_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    # 若已存在则取 SHA 以便覆盖
    sha = None
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {gh_token}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            sha = json.load(r).get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    body = {"message": f"chore: update chart {fname}", "content": content}
    if sha:
        body["sha"] = sha
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Authorization": f"Bearer {gh_token}", "Content-Type": "application/json"},
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        json.load(r)
    # 优先返回 GitHub Pages 链接（微信内可直接显示图），raw 作备用
    return f"https://0x75nic.github.io/multi-asset-quant-toolkit/{remote_path}"


if __name__ == "__main__":
    do_push = "--push" in sys.argv
    do_chart = "--chart" in sys.argv
    do_upload = "--upload-chart" in sys.argv
    token = None
    if "--token" in sys.argv:
        token = sys.argv[sys.argv.index("--token") + 1]
    elif do_push:
        token = os.environ.get("PUSHPLUS_TOKEN")
    gh_token = None
    if "--gh-token" in sys.argv:
        gh_token = sys.argv[sys.argv.index("--gh-token") + 1]
    elif do_upload:
        gh_token = os.environ.get("GITHUB_TOKEN")
    chart_dir = sys.argv[sys.argv.index("--chart-dir") + 1] if "--chart-dir" in sys.argv else "charts"

    t, cand, fr, oi = fetch()
    last = float(t["last"])
    report = build_report(t, cand, fr, oi)

    # 宏观 + 持仓量化信号（Yahoo 宏观代理 + CFTC COT + FRED 真实利率）
    try:
        cd = os.path.dirname(os.path.abspath(__file__))
        macro = gold_signals.fetch_macro()
        cot = gold_signals.fetch_cot(cd)
        # FRED 真实利率：--fred-key 传参可覆盖；默认走 gold_signals.FRED_API_KEY（内置免费 key）
        fred = gold_signals.fetch_fred_dfii10(
            sys.argv[sys.argv.index("--fred-key") + 1] if "--fred-key" in sys.argv else None
        )
        report += "\n\n---\n\n" + gold_signals.build_signal_block(macro, cot, fred)
    except Exception as e:
        print("[!] 宏观信号生成失败:", e, file=sys.stderr)

    if "--extra-file" in sys.argv:
        ef = sys.argv[sys.argv.index("--extra-file") + 1]
        try:
            with open(ef, encoding="utf-8") as f:
                extra = f.read().strip()
            if extra:
                report += "\n\n---\n\n" + extra
        except Exception as e:
            print("[!] extra-file 读取失败:", e, file=sys.stderr)

    chart_path = None
    chart_url = None
    if do_chart:
        chart_path = build_chart(last, chart_dir)
        print("CHART_FILE=" + chart_path)
        if do_upload:
            if not gh_token:
                print("\n[!] 未提供 GITHUB_TOKEN，跳过图上传", file=sys.stderr)
            else:
                chart_url = upload_chart_github(chart_path, gh_token)
                print("CHART_URL=" + chart_url)
                report += (
                    f"\n\n## 方案阶梯图\n"
                    f"![XAU 多空方案阶梯图]({chart_url})\n\n"
                    f"> 如微信内未直接显示，可点击链接用浏览器打开"
                )

    if "--chart-link" in sys.argv:
        link = sys.argv[sys.argv.index("--chart-link") + 1]
        report += f"\n\n![黄金方案图]({link})"

    print(report)

    if do_push:
        if not token:
            print("\n[!] 未提供 PUSHPLUS_TOKEN，跳过推送", file=sys.stderr)
            sys.exit(1)
        resp = pushplus(token, "黄金实时快照", report)
        print("\n[PushPlus]", resp)
