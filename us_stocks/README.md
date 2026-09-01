# 美股 / 共用 LLM 决策引擎 (TradingAgents-CN 包装)

美股与加密的 LLM 终裁**共用同一个引擎** `TradingAgents-CN`
（多智能体：市场/新闻/情绪/基本面分析 → 辩论 → 风险经理 → 组合经理）。
本目录不复制框架本体，只提供**共识包装器 + 已落地修复的文档**。

## 已落地的修复（在 TradingAgents-CN 的 `run_hype_sndk.py` 中）

| 问题 | 修复 | 状态 |
|---|---|---|
| deep 角色走 SiliconFlow DeepSeek-V3 太贵 | 默认改 `Qwen/Qwen2.5-72B-Instruct`；`SF_DEEP_MODEL` 若含 deepseek/v3 **强制拒绝回退 Qwen**（防误调） | ✅ 已锁定 |
| 加密标的跑无意义的 social/fundamentals 分析师 | 加密只跑 market+news；美股跑 market+news+fundamentals，关 social | ✅ |
| **非确定性**（同标的结论翻转） | `run_consensus.py` 连跑 N 次取多数票 | ✅ 本目录提供 |
| embeddings 接口 401 (SiliconFlow) | 自动降级，不阻断主分析（主 chat 调用全 200） | ⚠ 已知、无害 |
| 框架给「卖出」被误读为做空信号 | 校准：读成「非买点/回避」，绝不当做空（UNI 卖出后被涨破打脸的教训） | 📌 使用须知 |

## 用法

```bash
# 1) 直接跑单标的 (框架原生)
cd $TRADINGAGENTS_HOME && .venv/Scripts/python.exe run_hype_sndk.py HYPE SNDK

# 2) 共识模式 (推荐, 滤掉非确定性翻转)
TRADINGAGENTS_HOME=/path/to/TradingAgents-CN-main \
CONSENSUS_ROUNDS=3 \
python run_consensus.py HYPE
```

`run_consensus.py` 会连跑 N 次、解析每份报告 dict、对 action 取多数票、
target_price 取中位、confidence/risk 取均值，并标注「是否存在分歧」。

## 卖出语义校准（重要使用须知）

TradingAgents 的 `action` 字段含义：
- **买入 / 持有** → 直接按字面
- **卖出** → 框架在超买/弱势时给「卖出」，应读成 **「现在不是买点 / 回避」**，
  **绝不等同于去做空**。历史案例：UNI 给「卖出/目标5.25」，事后涨破 5.25，
  若反手做空会浮亏。加密与美股通用此校准。

## 报告格式（可机器解析）

`data/reports/ta_<TICKER>_<DATE>.md` 为单行 Python dict：
```python
{'action': '买入', 'target_price': 86.0, 'confidence': 0.8, 'risk_score': 0.3, 'reasoning': '...', 'model_info': '...'}
```
`run_consensus.py` 用 `ast.literal_eval` 解析。

非投资建议，自负盈亏。
