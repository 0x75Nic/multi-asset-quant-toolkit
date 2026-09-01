# A股 突破追单扫描器

复用加密突破扫描的方法学（近 20 日摆动高点 / ATR 止损 / R:R 目标 / 按波动率定杠杆），
叠加 A股 专属层：**T+1 提醒 / 涨跌停突破判定 / 北向资金 / 板块联动**。

## 用法

```bash
pip install akshare          # 仅现货行情/北向等增强项需要; 核心K线不依赖
python breakout_scan_ashare.py 600519              # 贵州茅台
python breakout_scan_ashare.py 300750 600519       # 多只
python breakout_scan_ashare.py 比亚迪              # 名称模糊匹配(需 akshare)
```

## 数据源（多源兜底）

| 源 | 用途 | 说明 |
|---|---|---|
| 东方财富 `push2his.eastmoney.com` | 日K(前复权) 主源 | 直连 urllib; **不可带 Referer**(反爬断连); 偶发按请求限流 |
| 新浪财经 `money.finance.sina.com.cn` | 日K 兜底 | 东方财富被限流时自动切换; 返回 gbk 编码 |
| akshare | 现货行情 / 北向资金 | 可选增强; 失败不致命, 自动回退 K线末值 |

> 沙箱/代理环境注意: 若系统设了 `HTTPS_PROXY`(如 SakuraCat 7897), akshare(requests) 会走代理失败;
> 核心 K线 用 urllib 直连, 运行前 `unset HTTPS_PROXY HTTP_PROXY` 即可。

## 输出

现价 / 均线 / RSI / ATR / 60日高低 / 摆动高低点 / **突破追单参数**(触发·止损·TP1/TP2·杠杆·仓位)
+ A股 专属提示(T+1 / 涨跌停 ±10%或±20% / 北向资金)。

## 与加密扫描的方法学一致性

| 指标 | 算法 | 一致 |
|---|---|---|
| 均线 | SMA20 / SMA50 | ✅ |
| RSI | 14 期 Wilder 平滑 | ✅ |
| ATR | 14 期 True Range 均值 | ✅ |
| 触发 | 近 10 日高 × 1.004 (突破 0.4%) | ✅ |
| 止损 | 触发价 − 1 ATR | ✅ |
| 目标 | TP1 = +2R, TP2 = +3R | ✅ |
| 杠杆 | 按 ATR% 分档(加密 1.5–5x / A股 1–3x, 波动更小) | 分档不同, 逻辑同 |

非投资建议，自负盈亏。
