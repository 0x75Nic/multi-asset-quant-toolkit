"""tradingbeats.xyz 数据交叉验证 + 假数据过滤器
重要事实: tradingbeats 是 JS 单页应用, 核心数字(价格/OI/成交额)来自 HyperLiquid 官方 API,
真实可用; 但「24h 清算地址排行榜」是**占位假数据**:
  - 地址序列整齐: 0x00...0011, 0x00...0012, ... 0x00...0019
  - 金额每次精确递减 $17.5K ($265K → $125K)
  - 时间均匀: 刚刚 / 1小时前 / ... / 8小时前
本模块: 提供假数据检测器 + 排行榜清洗 + 页面文本真实指标提取。

用法(配合 WebFetch 读页面文本后清洗):
  python tradingbeats_validate.py page_text.txt
  python tradingbeats_validate.py            # 读 stdin
  # 或直接调用函数:
  #   from tradingbeats_validate import clean_leaderboard, extract_real_metrics
"""
import sys
import re


# ---------- 假数据检测器 ----------
FAKE_ADDR_RE = re.compile(r"^0x0{6,}(1[1-9])$")  # 0x00...0011 ~ 0x00...0019


def is_fake_entry(addr: str, amount: float = None, prev_amount: float = None) -> bool:
    """判断一条清算记录是否假数据。"""
    if FAKE_ADDR_RE.match(addr or ""):
        return True
    # 金额精确等差递减 $17.5K 也是假数据特征
    if amount is not None and prev_amount is not None:
        if abs((prev_amount - amount) - 17500) < 1:
            return True
    return False


def clean_leaderboard(entries):
    """entries: list[dict(addr, amount, time)] -> 只留真实记录, 并标出被剔除数"""
    cleaned, dropped = [], 0
    prev = None
    for e in entries:
        if is_fake_entry(e.get("addr"), e.get("amount"), prev):
            dropped += 1
            continue
        cleaned.append(e)
        prev = e.get("amount")
    return cleaned, dropped


# ---------- 真实指标提取 ----------
def extract_real_metrics(text: str) -> dict:
    """从页面文本(WebFetch 结果)正则提取真实聚合指标。返回 dict。"""
    out = {}
    pats = {
        "price": r"(?:标记价|Mark Price|Price)\D*?([\d,]+\.?\d*)",
        "oi": r"未平仓[^\d]*?\$?([\d.]+)\s*([BM])",
        "vol24h": r"24[HH]?\s*成交额[^\d]*?\$?([\d.]+)\s*([BM])",
        "liq_long": r"多头清算[^\d]*?\$?([\d.]+)\s*([BM])",
        "liq_short": r"空头清算[^\d]*?\$?([\d.]+)\s*([BM])",
        "top10_long": r"Top\s*10[^$]*多头[^\d]*?\$?([\d.]+)\s*([BM])",
        "top10_short": r"Top\s*10[^$]*空头[^\d]*?\$?([\d.]+)\s*([BM])",
    }
    for k, p in pats.items():
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = float(m.group(1).replace(",", ""))
            unit = m.group(2) if len(m.groups()) > 1 and m.group(2) else ""
            out[k] = val * (1e9 if unit == "B" else 1e6 if unit == "M" else 1)
    return out


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    print("=" * 60)
    print("  tradingbeats 交叉验证")
    print("=" * 60)
    metrics = extract_real_metrics(text)
    if metrics:
        print("  提取到的真实聚合指标:")
        for k, v in metrics.items():
            print(f"    {k}: {v:,.0f}")
    else:
        print("  未从文本提取到指标(页面结构可能变动, 建议人工核对)")

    # 演示: 内置一段已知假数据, 验证过滤器
    demo = [
        {"addr": "0x0000000000000000000000000000000000000011", "amount": 265000, "time": "刚刚"},
        {"addr": "0x0000000000000000000000000000000000000012", "amount": 247500, "time": "1小时前"},
        {"addr": "0xAbCdEf1234567890aBcDeF1234567890aBcDeF12", "amount": 182000, "time": "3小时前"},
        {"addr": "0x0000000000000000000000000000000000000019", "amount": 125000, "time": "8小时前"},
    ]
    cleaned, dropped = clean_leaderboard(demo)
    print(f"\n  假数据过滤演示: 输入 {len(demo)} 条, 剔除假数据 {dropped} 条, 保留真实 {len(cleaned)} 条")
    print("  ⚠ 结论: tradingbeats 的「24h清算地址榜」应整体视为占位, 仅聚合清算分布/Top10大户可信")


if __name__ == "__main__":
    main()
