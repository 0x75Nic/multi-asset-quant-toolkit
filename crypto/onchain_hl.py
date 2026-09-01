"""HyperLiquid 链上指标分析
直连 HL 官方 API (api.hyperliquid.xyz/info, POST metaAndAssetCtxs)
输出: 标记价 / 预言机价 / 资金费率(年化) / 未平仓(OI USD+币) / 24h成交额
交叉验证: 若 OKX 同标的永续存在, 一并拉取比对
用法: python onchain_hl.py HYPE
      python onchain_hl.py BTC HYPE ETH
"""
import sys
import json
import urllib.request
import urllib.parse


def hl_meta():
    req = urllib.request.Request(
        "https://api.hyperliquid.xyz/info",
        data=json.dumps({"type": "metaAndAssetCtxs"}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    d = json.loads(urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore"))
    return d[0], d[1]


def okx_ticker(inst):
    u = f"https://www.okx.com/api/v5/market/ticker?instId={inst}"
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore"))
        return d["data"][0]
    except Exception:
        return None


def analyze(coin: str, meta, ctxs):
    idx = {a["name"]: i for i, a in enumerate(meta["universe"])}
    if coin not in idx:
        print(f"  !! HL 无此标的: {coin}")
        return
    i = idx[coin]
    c = ctxs[i]
    mp = float(c["markPx"])
    oi = float(c["openInterest"])
    fr = float(c["funding"])
    fr_ann = fr * 24 * 365 * 100
    oi_usd = oi * mp
    vol = float(c.get("dayNtlVlm", 0))
    prev = float(c.get("prevDayPx", mp))
    chg = (mp - prev) / prev * 100 if prev else 0

    print("=" * 60)
    print(f"  HyperLiquid 链上  {coin}")
    print("=" * 60)
    print(f"  标记价   {mp:.4f}  | 预言机 {c.get('oraclePx')} | 24h {chg:+.2f}%")
    print(f"  资金费率 1h {fr:.6f}  → 年化 {fr_ann:+.2f}%   ({'多头拥挤' if fr_ann>30 else '空头拥挤' if fr_ann<-30 else '中性'})")
    print(f"  未平仓   {oi:.2f} {coin}  ≈ ${oi_usd/1e9:.3f}B")
    print(f"  24h成交额 ${vol/1e9:.3f}B")
    print(f"  中价 {c.get('midPx')} | 最低挂单 {c.get('impactPxs')}")

    # OKX 交叉验证
    okx_sym = f"{coin}-USDT-SWAP"
    ot = okx_ticker(okx_sym)
    if ot:
        ol = float(ot["last"])
        diff = (ol - mp) / mp * 100
        print(f"  [交叉] OKX {okx_sym} 现价 {ol:.4f}  与HL偏差 {diff:+.3f}%  {'✅' if abs(diff)<0.3 else '⚠ 偏离偏大'}")
        try:
            of = float(ot.get("fundingRate", 0))
            print(f"  [交叉] OKX 资金费率年化 {of*3*365*100:+.2f}%")
        except Exception:
            pass
    else:
        print("  [交叉] OKX 无同标的永续, 跳过")
    return dict(coin=coin, markPx=mp, fr_ann=fr_ann, oi_usd=oi_usd, vol=vol)


if __name__ == "__main__":
    coins = sys.argv[1:] or ["HYPE"]
    meta, ctxs = hl_meta()
    for c in coins:
        print()
        analyze(c.upper(), meta, ctxs)
        print()
