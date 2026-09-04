#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指数价格警报（边沿触发，防刷屏）
- 拉 Yahoo 实时价：标普500(^GSPC) / 纳指100(^NDX) / 日经225(^N225)
- 仅在「触发态首次翻转」时推 PushPlus，平时静默
- 关键位来自 2026-09-02 布局分析（9/16 FOMC + 9/18 BOJ 前观望）

用法:
  python index_alert.py                 # 检查一次（命中才推）
  python index_alert.py --test          # 发一条测试推送（验证送达，不依赖触发）
  python index_alert.py --token X       # 覆盖 PushPlus token
"""
import json
import os
import sys
import datetime
import urllib.request
import urllib.parse

UA = {"User-Agent": "Mozilla/5.0"}

# token 默认走环境变量，缺省回退到项目已知 token（与 gold-monitor 一致）
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "8c7bf61a6ded40b7bf8c80b6ab68f719")

SYMS = {
    "S&P500": "^GSPC",
    "NDX100": "^NDX",
    "Nikkei225": "^N225",
    "NVDA": "NVDA",
}

# (id, 指数名, 方向, 阈值, 触发文案)
ALERTS = [
    # 标普500：ma50=7566(撑) / ma20=7713(压) / 买区 7267–7100
    ("sp_buyzone",  "S&P500",   "<=", 7267,  "🟢 标普500 跌入买区(7267–7100)，可关注分批布局"),
    ("sp_bottom",   "S&P500",   "<=", 7100,  "🔴 标普500 触及买区下沿7100（最后支撑），破位不接"),
    ("sp_reclaim",  "S&P500",   ">=", 7713,  "🟢 标普500 收回 MA20(7713)，短线转强信号"),
    # 纳指100：ma50=29244(压)
    ("ndx_reclaim", "NDX100",   ">=", 29244, "🟢 纳指100 收回 MA50(29244)，可重新关注"),
    # 日经225：ma20=66400(压) / 恐慌买区 61434–60000
    ("nk_panic",    "Nikkei225","<=", 61434, "🟢 日经225 跌入恐慌买区(61434–60000)，可关注"),
    ("nk_bottom",   "Nikkei225","<=", 60000, "🔴 日经225 触及恐慌区下沿60000（极端位置）"),
    ("nk_reclaim",  "Nikkei225",">=", 66400, "🟢 日经225 收回 MA20(≈66400)，布局信号出现"),
    # NVDA（美股永续 3-5x）：ma20=219 / ma50=209 / ma200=196 / 3月高228
    ("nvda_longzone","NVDA",   "<=", 219,  "🟢 NVDA 回踩 MA20(219) 进入多区，可关注分批接"),
    ("nvda_ma50",    "NVDA",   "<=", 209,  "🟢 NVDA 回踩 MA50(209) 首选多区，止损196下"),
    ("nvda_ma200lost","NVDA",  "<=", 196,  "🔴 NVDA 跌破 MA200(196)，多区失效/反手空信号"),
    ("nvda_breakout","NVDA",   ">=", 228,  "🟢 NVDA 突破 3月高(228)，打开上行空间"),
]

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index_alert_state.json")


def fetch_last(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d"
    d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read())
    closes = [c for c in d["chart"]["result"][0]["indicators"]["quote"][0]["close"] if c is not None]
    return closes[-1]


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

    # 拉实时价
    prices = {}
    for name, s in SYMS.items():
        try:
            prices[name] = fetch_last(s)
        except Exception as e:
            print(f"[!] {name} 拉取失败: {e}", file=sys.stderr)
            prices[name] = None

    state = load_state()
    fired = []
    for aid, idx, op, lvl, text in ALERTS:
        p = prices.get(idx)
        if p is None:
            continue
        cur = (p <= lvl) if op == "<=" else (p >= lvl)
        prev = state.get(aid, {}).get("triggered", False)
        if cur and not prev:
            fired.append((idx, p, text))
        state.setdefault(aid, {})["triggered"] = bool(cur)
        state.setdefault(aid, {})["last_price"] = p
    save_state(state)

    # 价格快照行
    snap = "\n".join(
        f"- {n}：**{p:.2f}**" for n, p in prices.items() if p is not None
    )

    if do_test:
        content = (
            f"# 指数警报·测试推送（{ts} 北京）\n\n"
            f"{snap}\n\n> 脚本运行正常，后续触及关键位将自动推送。\n"
            f"> 关键位：标普买区 7267/7100、收回 7713；纳指收回 29244；"
            f"日经恐慌区 61434/60000、收回 66400。"
        )
        print(pushplus(token, "指数警报·测试", content))
        return

    if not fired:
        print(f"[{ts}] 无触发，静默。价格: " + ", ".join(f"{n}={p:.0f}" for n, p in prices.items() if p))
        return

    lines = [f"# 指数价格警报（{ts} 北京）\n"]
    lines.append(snap + "\n")
    for idx, p, text in fired:
        lines.append(f"- {text}（现价 **{p:.2f}**）")
    lines.append("\n> 数据：Yahoo Finance 实时。仅提示，不构成交易建议。")
    content = "\n".join(lines)
    resp = pushplus(token, "指数价格警报", content)
    print(f"[{ts}] 推送 {len(fired)} 条: {resp}")


if __name__ == "__main__":
    main()
