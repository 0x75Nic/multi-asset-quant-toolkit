"""OKX 条件单(计划委托)参数生成器
把突破扫描的 触发/止损/止盈 转成 OKX 可提交的 trigger 订单参数。
输出: 人类可读计划 + OKX REST API 就绪的 JSON 数组(复制即提交)。

用法:
  python conditional_order.py HYPE-USDT-SWAP --trig 87.15 --stop 81.26 --tp1 98.92 --tp2 104.81 --size 100 --lev 3
  python conditional_order.py BTC-USDT-SWAP --trig 87000 --stop 81000 --tp1 95000 --tp2 100000 --size 0.5 --td cross
  # 也可从突破扫描导出的 json 读入:
  python conditional_order.py HYPE-USDT-SWAP --json params.json --size 100
"""
import sys
import json
import argparse


def build(inst, trig, stop, tp1, tp2, size, lev, td, px_buffer=0.001):
    """返回 3 个 OKX trigger 订单 dict: 突破买入 / 止损 / 止盈1 / 止盈2"""
    # 突破买入: 当最新价 >= trig 触发, 限价单买入(略高于触发价)
    buy = {
        "instId": inst, "tdMode": td, "side": "buy", "ordType": "trigger",
        "sz": str(size), "triggerPx": f"{trig:.4f}",
        "orderPx": f"{trig*(1+px_buffer):.4f}",
        "tgtCcy": "cont", "reduceOnly": False,
        "tag": "breakout_buy",
    }
    # 止损: 当最新价 <= stop 触发, 限价卖出(略低于止损价), 仅减仓
    sl = {
        "instId": inst, "tdMode": td, "side": "sell", "ordType": "trigger",
        "sz": str(size), "triggerPx": f"{stop:.4f}",
        "orderPx": f"{stop*(1-px_buffer):.4f}",
        "tgtCcy": "cont", "reduceOnly": True,
        "tag": "stop_loss",
    }
    orders = [buy, sl]
    # 止盈(可选, 可多个)
    for k, tp in [("TP1", tp1), ("TP2", tp2)]:
        if tp:
            orders.append({
                "instId": inst, "tdMode": td, "side": "sell", "ordType": "trigger",
                "sz": str(size), "triggerPx": f"{tp:.4f}",
                "orderPx": f"{tp*(1-px_buffer):.4f}",
                "tgtCcy": "cont", "reduceOnly": True,
                "tag": f"take_profit_{k}",
            })
    return orders


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inst")
    ap.add_argument("--trig", type=float)
    ap.add_argument("--stop", type=float)
    ap.add_argument("--tp1", type=float, default=None)
    ap.add_argument("--tp2", type=float, default=None)
    ap.add_argument("--size", type=float, required=True, help="合约张数")
    ap.add_argument("--lev", type=float, default=3)
    ap.add_argument("--td", default="cross", choices=["cross", "isolated"])
    ap.add_argument("--json", help="从突破扫描导出的 json 读 trig/stop/tp1/tp2")
    a = ap.parse_args()

    if a.json:
        with open(a.json) as f:
            p = json.load(f)
        a.trig, a.stop, a.tp1, a.tp2 = p.get("trig"), p.get("stop"), p.get("tp1"), p.get("tp2")

    if not (a.trig and a.stop):
        print("缺少 --trig / --stop (或从 --json 读取失败)")
        sys.exit(1)

    orders = build(a.inst, a.trig, a.stop, a.tp1, a.tp2, a.size, a.lev, a.td)

    print("=" * 62)
    print(f"  OKX 条件单  {a.inst}  | 杠杆 {a.lev}x | 保证金模式 {a.td}")
    print("=" * 62)
    print(f"  ① 突破买入 : 最新价 ≥ {a.trig:.4f} 触发, 限价买入 {a.size} 张")
    print(f"  ② 止损     : 最新价 ≤ {a.stop:.4f} 触发, 限价卖出(减仓)")
    if a.tp1:
        print(f"  ③ 止盈TP1  : 最新价 ≥ {a.tp1:.4f} 触发, 限价卖出(减仓)")
    if a.tp2:
        print(f"  ④ 止盈TP2  : 最新价 ≥ {a.tp2:.4f} 触发, 限价卖出(减仓)")
    print("-" * 62)
    print("  OKX API 就绪 JSON (POST /api/v5/trade/batch-orders):")
    print(json.dumps({"orders": orders}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
