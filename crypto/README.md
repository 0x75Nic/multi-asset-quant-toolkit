# 加密 突破追单 + 链上分析

四件套，覆盖「技术面突破扫描 → 链上验证 → 条件单落地」完整链路。

## 模块

| 脚本 | 数据源 | 作用 |
|---|---|---|
| `breakout_scan.py` | OKX 永续 | 突破追单参数(触发/止损/TP/杠杆/仓位), 复用统一方法学 |
| `onchain_hl.py` | HyperLiquid 官方 API | 链上指标: 标记价/预言机价/资金费率(年化)/OI/24h成交额, 与 OKX 交叉验证 |
| `tradingbeats_validate.py` | tradingbeats.xyz(文本) | 交叉验证 + **假数据过滤器**(剔除 0x00…0011-0019 等差假清算榜) |
| `conditional_order.py` | — | 把突破参数转 OKX 计划委托(trigger 订单) JSON, 复制即提交 |

## 用法

```bash
python breakout_scan.py HYPE-USDT-SWAP            # 突破扫描
python onchain_hl.py HYPE                         # 链上验证
python conditional_order.py HYPE-USDT-SWAP \
    --trig 87.15 --stop 81.26 --tp1 98.92 --tp2 104.81 --size 100 --lev 3
```

## 数据可靠性（重要）

tradingbeats.xyz 的**聚合清算分布 / Top10 大户**真实可信（与 HL 官方 API 逐项吻合）；
但其 **「24h 清算地址排行榜」是占位假数据**（地址 0x00…0011-0019 等差序列、金额每次精确递减 $17.5K、
时间均匀），用 `tradingbeats_validate.clean_leaderboard()` 整体剔除。核心数字请直接信 `onchain_hl.py` 的 HL API。

## 与 A股 模块的方法学一致性

突破扫描算法完全一致（均线/RSI/ATR/触发=近10日高×1.004/止损=1ATR/TP=2R,3R），
仅杠杆分档不同：加密 1.5–5x（波动大）、A股 1–3x（波动小）。

非投资建议，自负盈亏。
