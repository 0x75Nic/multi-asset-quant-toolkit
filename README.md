# 多资产量化分析工具包 (Multi-Asset Quant Toolkit)

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

```bash
unset HTTPS_PROXY HTTP_PROXY
```

## 统一方法学

详见 [`shared/methodology.md`](shared/methodology.md)：均线 / RSI / ATR / 摆动高低点 /
突破触发=近10日高×1.004 / 止损=1ATR / 目标=2R,3R / 杠杆按 ATR 分档。
三模块算法完全一致，仅杠杆上限与资产专属层不同。

## 数据可靠性

- 加密：OKX + HyperLiquid 官方 API，免费、可信
- A股：东方财富（主）+ 新浪（兜底），直连
- tradingbeats.xyz 的「24h 清算地址榜」是**占位假数据**，已内置过滤器整体剔除；聚合清算/Top10 大户可信

非投资建议，自负盈亏。
