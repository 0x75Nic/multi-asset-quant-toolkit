#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密破位警报（边沿触发，防刷屏）
- 拉 OKX 实时价：BTC / BOME / INJ 永续
- 仅在「触发态首次翻转」时推 PushPlus，平时静默
- 关键位来自 2026-09-04 分析：BTC 今日支撑 77000 / MA20 75594 / MA50 68768

用法:
  python crypto_alert.py                 # 检查一次（命中才推）
  python crypto_alert.py --test          # 发一条测试推送（验证送达，不依赖触发）
  python crypto_alert.py --token X       # 覆盖 PushPlus token
"""
import json
import os
import sys
import datetime
import urllib.request
import urllib.parse

UA = {"User-Agent": "Mozilla/5.0"}

# token 默认走环境变量，缺省回退到项目已知 token（与 gold-monitor / index_alert 一致）
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "8c7bf61a6ded40b7bf8c80b6ab68f719")

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crypto_alert_state.json")


def okx(u):
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read())


def fetch_last(inst):
    return float(okx(f"https://www.okx.com/api/v5/market/ticker?instId={inst}")["data"][0]["last"])


def compute_ma20(inst):
    c = okx(f"https://www.okx.com/api/v5/market/candles?instId={inst}&bar=1D&limit=60")["data"]
    cl = [float(x[4]) for x in c][::-1]
    return sum(cl[-20:]) / 20


# (id, instId, label, op, level_or_None_for_dynamicMA20, 触发文案)
ALERTS = [
    ("btc_break_77k", "BTC-USDT-SWAP",  "BTC",  "<=", 77000,  "🔴 BTC 跌破 77000 今日支撑，短空信号触发（目标 MA20 75594 / MA50 68768）"),
    ("btc_ma20",      "BTC-USDT-SWAP",  "BTC",  "<=", 75594,  "🔴 BTC 跌破 MA20(75594)，空头加速"),
    ("btc_ma50",      "BTC-USDT-SWAP",  "BTC",  "<=", 68768,  "🔴 BTC 跌破 MA50(68768)，深度破位，板块转空确认"),
    ("bome_ma20",     "BOME-USDT-SWAP", "BOME", "<=", None,   "🟡 BOME 跌破 MA20，弱势币转弱（做空弹性标的）"),
    ("inj_ma20",      "INJ-USDT-SWAP",  "INJ",  "<=", None,   "🟡 INJ 跌破 MA20，弱势币转弱（做空弹性标的）"),
]


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(s):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)


def pushplus(token, title, content):
    url = (
        "http://www.pushplus.plus/send"
        f"?token={token}&title={urllib.parse.quote(title)}"
        f"&content={urllib.parse.quote(content)}&template=markdown"
    )
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")


def main():
    do_test = "--test" in sys.argv
    token = PUSHPLUS_TOKEN
    if "--token" in sys.argv:
        token = sys.argv[sys.argv.index("--token") + 1]

    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    ts = now.strftime("%Y-%m-%d %H:%M")

    # 拉实时价（去重 instId）
    insts = list({a[1] for a in ALERTS})
    prices = {}
    for inst in insts:
        try:
            prices[inst] = fetch_last(inst)
        except Exception as e:
            print(f"[!] {inst} 拉取失败: {e}", file=sys.stderr)
            prices[inst] = None

    state = load_state()
    fired = []
    for aid, inst, label, op, level, text in ALERTS:
        p = prices.get(inst)
        if p is None:
            continue
        # 动态阈值（弱币 MA20 每次计算）
        lvl = compute_ma20(inst) if level is None else level
        cur = (p <= lvl) if op == "<=" else (p >= lvl)
        prev = state.get(aid, {}).get("triggered", False)
        if cur and not prev:
            fired.append((label, p, lvl, text))
        state.setdefault(aid, {})["triggered"] = bool(cur)
        state.setdefault(aid, {})["last_price"] = p
        state.setdefault(aid, {})["last_level"] = round(lvl, 6)
    save_state(state)

    # 价格快照行
    label_of = {a[1]: a[2] for a in ALERTS}
    snap = "\n".join(
        f"- {label_of.get(inst, inst)}：**{p:.6g}**" for inst, p in prices.items() if p is not None
    )

    if do_test:
        content = (
            f"# 加密破位警报·测试推送（{ts} 北京）\n\n"
            f"{snap}\n\n> 脚本运行正常，后续 BTC 跌破 77000 / MA20 / MA50 或弱势币转弱将自动推送。\n"
            f"> 关键位：BTC 支撑 77000、MA20 75594、MA50 68768；弱势币 BOME/INJ 跌破 MA20 预警。"
        )
        print(pushplus(token, "加密破位警报·测试", content))
        return

    if not fired:
        print(f"[{ts}] 无破位触发，静默。价格: " + ", ".join(
            f"{label_of.get(i,i)}={p:.0f}" for i, p in prices.items() if p))
        return

    lines = [f"# 加密破位警报（{ts} 北京）\n"]
    lines.append(snap + "\n")
    for label, p, lvl, text in fired:
        lines.append(f"- {text}（现价 **{p:.6g}**，阈值 {lvl:.6g}）")
    lines.append("\n> 数据：OKX 实时。仅提示，不构成交易建议。")
    content = "\n".join(lines)
    resp = pushplus(token, "加密破位警报", content)
    print(f"[{ts}] 推送 {len(fired)} 条: {resp}")


if __name__ == "__main__":
    main()
