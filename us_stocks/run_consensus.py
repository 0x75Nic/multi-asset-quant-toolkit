"""共用 LLM 引擎 (TradingAgents-CN) — 共识包装器
非侵入式解决框架非确定性: 同一标的连跑 N 次 (默认3), 对 action 取多数票,
target_price 取中位, confidence/risk_score 取均值, 输出共识结论。

为何需要: TradingAgents 多智能体辩论, 即便 temperature=0, 上游辩论历史每次不同,
同标的结论会翻转 (ENA 买→持有→买, UNI 买→卖)。共识投票把"偶发翻转"滤掉。

依赖: 本机已部署 TradingAgents-CN (默认 E:\\软件下载\\TradingAgents-CN-main)
配置: 环境变量 TRADINGAGENTS_HOME 指向框架目录; CONSENSUS_ROUNDS 设轮数(默认3)

用法:
  python run_consensus.py HYPE
  python run_consensus.py SNDK NVDA
  CONSENSUS_ROUNDS=5 python run_consensus.py HYPE
"""
import os
import sys
import ast
import json
import subprocess
import datetime
from collections import Counter

HOME = os.environ.get("TRADINGAGENTS_HOME", r"E:\软件下载\TradingAgents-CN-main")
RUN_SCRIPT = "run_hype_sndk.py"
N = int(os.environ.get("CONSENSUS_ROUNDS", "3"))


def _venv_python():
    p = os.path.join(HOME, ".venv", "Scripts", "python.exe")
    return p if os.path.exists(p) else "python"


def run_once(ticker: str):
    """跑一次框架, 读取并解析报告 dict。返回 dict 或 None。"""
    cmd = [_venv_python(), RUN_SCRIPT, ticker]
    try:
        subprocess.run(cmd, cwd=HOME, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"  [warn] {ticker} 第次运行失败: {e}")
        return None
    date = datetime.date.today().strftime("%Y-%m-%d")
    path = os.path.join(HOME, "data", "reports", f"ta_{ticker}_{date}.md")
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("{") and "action" in line:
                    return ast.literal_eval(line)
    except Exception:
        return None
    return None


def consensus(ticker: str):
    print("=" * 64)
    print(f"  共识分析  {ticker}  (跑 {N} 轮)")
    print("=" * 64)
    decs = [d for d in (run_once(ticker) for _ in range(N)) if d]
    if not decs:
        print("  全部运行失败, 无共识")
        return
    print(f"  有效轮数 {len(decs)}/{N}:")
    for i, d in enumerate(decs, 1):
        print(f"    轮{i}: {d['action']} | 目标 {d.get('target_price')} | 置信 {d.get('confidence')} | 风险 {d.get('risk_score')}")

    actions = [d["action"] for d in decs]
    majority, cnt = Counter(actions).most_common(1)[0]
    targets = [d["target_price"] for d in decs if isinstance(d.get("target_price"), (int, float))]
    confs = [d["confidence"] for d in decs if isinstance(d.get("confidence"), (int, float))]
    risks = [d["risk_score"] for d in decs if isinstance(d.get("risk_score"), (int, float))]

    med_t = sorted(targets)[len(targets) // 2] if targets else None
    print("-" * 64)
    print(f"  ★ 共识动作 : {majority}  ({(cnt/len(decs)*100):.0f}% 投票一致)")
    if med_t is not None:
        print(f"  ★ 共识目标 : {med_t}")
    if confs:
        print(f"  ★ 平均置信 : {sum(confs)/len(confs):.2f}")
    if risks:
        print(f"  ★ 平均风险 : {sum(risks)/len(risks):.2f}")
    # 分歧警示
    if cnt < len(decs):
        print(f"  ⚠ 存在分歧 ({len(decs)-cnt} 轮不一致), 共识置信打折, 建议人工复核")
    return dict(action=majority, target=med_t,
                confidence=sum(confs)/len(confs) if confs else None,
                risk=sum(risks)/len(risks) if risks else None)


if __name__ == "__main__":
    tickers = sys.argv[1:] or ["HYPE"]
    for t in tickers:
        print()
        consensus(t.upper())
        print()
