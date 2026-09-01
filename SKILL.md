---
name: multi-asset-quant-toolkit
description: 多资产(加密/A股/美股)突破追单分析工具包。输入任意标的自动识别类别, 输出突破追单参数(触发/止损/止盈/杠杆/仓位) + 资产专属验证(链上/涨跌停/LLM共识)。适用于"分析下XXX""XXX适合建仓吗""算下XXX的追单参数"。
---

# 多资产量化分析工具包

一套统一的突破追单分析框架, 覆盖 **加密 / A股 / 美股**。这是 WorkBuddy 里的**元技能(Skill Pack)**,
对外发 GitHub 时叫 multi-asset quant toolkit。它不是自动交易 Agent, 而是分析能力。

## 何时用

- 用户说"分析下 XXX""XXX 适合建仓/做多吗""算下 XXX 的追单/突破参数"
- 需要跨资产(加密/A股/美股)统一方法论, 而非零散脚本

## 路由逻辑(自动)

`analyze.py` 按标的自动分类:
- 加密永续: 以 `-USDT-SWAP` 结尾, 或已知币代号(HYPE/BTC/ETH/SOL/ENA/UNI/TRUMP...)
- A股: 6 位纯数字代码 (600519 / 300750)
- 美股/其他: 其余 → TradingAgents-CN 共识引擎

## 调用方式

```bash
# 统一入口(推荐)
python analyze.py HYPE          # 加密
python analyze.py 600519        # A股
python analyze.py SNDK          # 美股

# 或分模块直接调
python crypto/breakout_scan.py HYPE-USDT-SWAP
python crypto/onchain_hl.py HYPE
python crypto/conditional_order.py HYPE-USDT-SWAP --trig 87.15 --stop 81.26 --tp1 98.92 --tp2 104.81 --size 100 --lev 3
python ashare/breakout_scan_ashare.py 600519
CONSENSUS_ROUNDS=3 TRADINGAGENTS_HOME=/path/to/TradingAgents-CN-main python us_stocks/run_consensus.py HYPE
```

## 沙箱/代理注意

若系统有 `HTTPS_PROXY`(如 SakuraCat 7897), akshare/requests 走代理会失败; 核心 K线 用 urllib 直连不受影响。运行前 `unset HTTPS_PROXY HTTP_PROXY`。
另: 东方财富 push2his 接口**不可带 Referer**(反爬断连); 新浪兜底源解决限流。

## 关键事实(分析时必须告诉用户)

1. **tradingbeats.xyz 的「24h 清算地址榜」是假数据**(0x00...0011-0019 等差序列), 整体剔除; 聚合清算/Top10 大户可信。
2. **美股/加密 LLM 引擎的「卖出」≠ 做空**: 读成"非买点/回避"(UNI 卖出后被涨破打脸的教训)。
3. **杠杆上限**: 加密≤5x、A股≤3x; 按 ATR% 分档(详见 shared/methodology.md)。
4. 非投资建议, 自负盈亏。

## 模块索引

| 目录 | 内容 |
|---|---|
| `crypto/` | OKX 突破扫描 + HyperLiquid 链上验证 + OKX 条件单生成 + tradingbeats 假数据过滤 |
| `ashare/` | A股 突破扫描(多源K线: 东财+新浪; T+1/涨跌停±10%/±20%/北向资金) |
| `us_stocks/` | TradingAgents-CN 共识包装器(去非确定性翻转) |
| `shared/` | 统一方法学(唯一事实来源) |
