# 多资产量化分析工具包 (Multi-Asset Quant Toolkit)

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/0x75Nic/multi-asset-quant-toolkit/blob/master/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Stars](https://img.shields.io/github/stars/0x75Nic/multi-asset-quant-toolkit?logo=github)](https://github.com/0x75Nic/multi-asset-quant-toolkit)
[![Last Commit](https://img.shields.io/github/last-commit/0x75Nic/multi-asset-quant-toolkit)](https://github.com/0x75Nic/multi-asset-quant-toolkit)
[![Repo Size](https://img.shields.io/github/repo-size/0x75Nic/multi-asset-quant-toolkit)](https://github.com/0x75Nic/multi-asset-quant-toolkit)
[![资产](https://img.shields.io/badge/资产-加密%20%7C%20A股%20%7C%20美股-2ea44f)](#)
[![框架](https://img.shields.io/badge/框架-突破追单-FF781F)](#)

</div>

一套统一的**突破追单分析**框架，覆盖 **加密 / A股 / 美股** 三类资产。
输入任意标的 → 自动识别类别 → 输出突破追单参数（触发价 / 止损 / 止盈 / 杠杆 / 仓位）
+ 资产专属验证（链上 / 涨跌停 / LLM 共识）。


> 这不是一个自动交易 Agent，而是一套**分析能力**：帮你算清"在哪买、在哪砍、目标在哪、该上几倍杠杆"。


## 架构


```
multi-asset-quant-toolkit/
├── analyze.py                 # 统一入口(元技能路由): 自动识别 加密/A股/美股
├── crypto/                   # 加密: OKX 突破 + HyperLiquid 链上 + 条件单 + 假数据过滤
│   ├── breakout_scan.py
│   ├── onchain_hl.py
│   ├── conditional_order.py
│   └── tradingbeats_validate.py
├── ashare/                   # A股: 突破扫描(A股专属层) + 多源K线(东财/新浪)
│   └── breakout_scan_ashare.py
├── us_stocks/                # 美股/共用LLM引擎: TradingAgents-CN 共识包装器
│   └── run_consensus.py
├── shared/
│   └── methodology.md        # 统一方法学(唯一事实来源, 三模块同步)
└── requirements.txt
```


## 快速开始


```bash
pip install akshare            # 仅 A股 增强项(现货/北向)需要; 核心不依赖
python analyze.py HYPE         # 加密
python analyze.py 600519       # A股
python analyze.py SNDK         # 美股(LLM 共识)
```


## 各领域用法


```bash
# 加密: 突破扫描 + 链上验证
python crypto/breakout_scan.py HYPE-USDT-SWAP
python crypto/onchain_hl.py HYPE
# 把参数转成 OKX 条件单 JSON
python crypto/conditional_order.py HYPE-USDT-SWAP \
    --trig 87.15 --stop 81.26 --tp1 98.92 --tp2 104.81 --size 100 --lev 3


# A股: 突破扫描(自动多源K线)
python ashare/breakout_scan_ashare.py 600519
python ashare/breakout_scan_ashare.py 300750 600519


# 美股: TradingAgents-CN 共识(需先部署框架, 设 TRADINGAGENTS_HOME)
CONSENSUS_ROUNDS=3 TRADINGAGENTS_HOME=/path/to/TradingAgents-CN-main \
    python us_stocks/run_consensus.py HYPE
```


## 沙箱 / 代理环境注意


若系统设了 `HTTPS_PROXY`（如 SakuraCat 7897），`akshare`/`requests` 会走代理失败。
核心 K线 用 `urllib` 直连不受影响。运行前：
