"""多资产量化分析工具包 — 统一入口 (元技能路由)
一个命令分析任意标的, 自动识别资产类别并路由到对应模块:

  加密 (永续)  -> crypto/   : 突破扫描 + HyperLiquid 链上验证 + 条件单
  A股 (6位代码) -> ashare/   : 突破扫描(A股专属层) + 多源K线
  美股/其他     -> us_stocks/: TradingAgents-CN 共识决策(LLM引擎)

用法:
  python analyze.py HYPE              # 加密
  python analyze.py 600519           # A股
  python analyze.py SNDK             # 美股(LLM共识)
  python analyze.py HYPE-USDT-SWAP 300750 BTC

注意: 跑前建议 unset HTTPS_PROXY/HTTP_PROXY (沙箱/代理环境 akshare/requests 走代理会失败;
核心K线用 urllib 直连不受影响)。
"""
import sys
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
VENV = os.environ.get(
    "TOOLKIT_VENV",
    r"C:\Users\1\.workbuddy\binaries\python\envs\default\Scripts\python.exe")

CRYPTO_KNOWN = {"BTC", "ETH", "SOL", "HYPE", "ENA", "UNI", "TRUMP", "DOGE", "PEPE", "WIF", "BONK", "NEAR", "INJ"}


def classify(t: str) -> str:
    t = t.upper()
    if t.endswith("-USDT-SWAP") or t in CRYPTO_KNOWN or t.split("-")[0] in CRYPTO_KNOWN:
        return "crypto"
    if t.isdigit() and len(t) == 6:
        return "ashare"
    return "us_stocks"


def run(venv, script, args):
    cmd = [venv, os.path.join(HERE, script)] + args
    print(f"\n$ {' '.join(cmd)}\n")
    subprocess.run(cmd, check=False)


def main():
    tickers = sys.argv[1:] or ["HYPE"]
    for t in tickers:
        kind = classify(t)
        print("\n" + "=" * 70)
        print(f"  ▶ {t}  →  路由到 [{kind}]")
        print("=" * 70)
        if kind == "crypto":
            sym = t if t.endswith("-USDT-SWAP") else f"{t.upper()}-USDT-SWAP"
            run(VENV, "crypto/breakout_scan.py", [sym])
            run(VENV, "crypto/onchain_hl.py", [t.upper().split("-")[0]])
        elif kind == "ashare":
            run(VENV, "ashare/breakout_scan_ashare.py", [t])
        else:  # us_stocks
            run(VENV, "us_stocks/run_consensus.py", [t.upper()])


if __name__ == "__main__":
    main()
