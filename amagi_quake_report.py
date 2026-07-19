#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 天城起点 地震自動解析レポート
# ================================
#
# やること:
# 1. P2P地震情報API(日本の地震データ、無料・APIキー不要)から
# 直近(または指定日)の地震一覧を取得
# 2. 各地震の震源について、天城(34.920N, 139.018E)からの
# 大円方位角・距離・16方位を計算
# 3. あらかじめ登録してある「確定軸(L1)」との一致(許容誤差3°)を自動判定
# 4. 結果をテキストレポートとして出力(コンソール表示 + ファイル保存)

import argparse
import json
import math
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

AMAGI = (34.920, 139.018)

DIRS16 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
          "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

CONFIRMED_AXES = [
    ("ENE57度軸(鹿島・香取/タケミカヅチ・フツヌシ)", 57.0, 3.0, "岩戸ログ中核軸"),
    ("NE45度軸(香取・江ノ島・熱田)", 45.0, 3.0, "NE45度corridor/貝塚"),
    ("W277度軸(出雲・難波宮)", 277.0, 3.0, "国譲り軸"),
    ("NNW337度軸(ストーンヘンジ・糸魚川・戸隠)", 337.0, 3.0, ""),
    ("NNE19度軸(封印された神々クラスタ)", 19.0, 3.0, ""),
    ("WNW292度軸(メッカ)", 292.0, 3.0, ""),
]

DRAGON_SITES = [
    ("布施弁天", 39.13, 2.0),
    ("龍神社(海神)", 44.42, 2.0),
    ("龍腹寺", 47.02, 2.0),
    ("龍角寺", 47.82, 2.0),
    ("龍正院", 48.35, 2.0),
    ("芝山", 55.71, 2.0),
    ("龍尾寺", 56.18, 2.0),
    ("銚子・銚港神社", 60.85, 2.0),
    ("玉前", 67.05, 2.0),
]

ALL_KNOWN_POINTS = CONFIRMED_AXES + DRAGON_SITES


def bearing(lat1, lon1, lat2, lon2):
    lat1r, lon1r, lat2r, lon2r = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2r - lon1r
    x = math.sin(dlon) * math.cos(lat2r)
    y = (math.cos(lat1r) * math.sin(lat2r)
         - math.sin(lat1r) * math.cos(lat2r) * math.cos(dlon))
    theta = math.atan2(x, y)
    return (math.degrees(theta) + 360) % 360


def distance_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1r, lon1r, lat2r, lon2r = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = (math.sin(dlat / 2) ** 2
         + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def nearest_16dir(b):
    idx = int((b + 11.25) // 22.5) % 16
    return DIRS16[idx]


def match_confirmed_axes(b):
    hits = []
    for name, center, tol, *rest in ALL_KNOWN_POINTS:
        diff = min(abs(b - center), 360 - abs(b - center))
        if diff <= tol:
            note = rest[0] if rest else ""
            hits.append((name, diff, note))
    return sorted(hits, key=lambda x: x[1])


P2P_QUAKE_API = "https://api.p2pquake.net/v2/history"
P2P_QUAKE_CODE = 551


def fetch_quakes(limit=100, debug=False):
    limit = max(1, min(limit, 100))
    url = f"{P2P_QUAKE_API}?codes={P2P_QUAKE_CODE}&limit={limit}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "amagi-quake-report/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"[エラー] 地震データの取得に失敗しました: {e}", file=sys.stderr)
        return []

    data = json.loads(raw)
    if debug:
        print(json.dumps(data[:1], ensure_ascii=False, indent=2))
    return data


def _parse_coord(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    sign = 1.0
    head = s[0]
    if head in ("N", "E"):
        s = s[1:]
    elif head in ("S", "W"):
        sign = -1.0
        s = s[1:]
    try:
        return sign * float(s)
    except ValueError:
        return None


def _parse_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().rstrip("km").strip()
    try:
        return float(s)
    except ValueError:
        return None


def parse_quake(item):
    try:
        eq = item.get("earthquake")
        if not eq:
            return None
        hypo = eq.get("hypocenter") or {}
        lat = _parse_coord(hypo.get("latitude"))
        lon = _parse_coord(hypo.get("longitude"))
        if lat is None or lon is None:
            return None
        if lat < -90 or lat > 90 or lon < -180 or lon > 180:
            return None
        return {
            "time": eq.get("time"),
            "place": hypo.get("name", "不明"),
            "lat": lat,
            "lon": lon,
            "depth": _parse_number(hypo.get("depth")),
            "mag": _parse_number(hypo.get("magnitude")),
            "max_scale": eq.get("maxScale"),
        }
    except (KeyError, TypeError, AttributeError):
        return None


SCALE_MAP = {
    10: "1", 20: "2", 30: "3", 40: "4",
    45: "5弱", 50: "5強", 55: "6弱", 60: "6強", 70: "7",
}


def scale_to_str(scale):
    return SCALE_MAP.get(scale, "不明") if scale is not None else "不明"


def build_report(quakes, days, min_mag):
    lines = []
    lines.append("=" * 60)
    lines.append(f"天城起点 地震解析レポート  (対象: 直近{days}日間, M{min_mag}以上)")
    lines.append(f"生成時刻: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("=" * 60)

    count = 0
    for item in quakes:
        q = parse_quake(item)
        if q is None:
            continue
        if q["mag"] is None or q["mag"] < min_mag:
            continue

        b = bearing(AMAGI[0], AMAGI[1], q["lat"], q["lon"])
        d = distance_km(AMAGI[0], AMAGI[1], q["lat"], q["lon"])
        d16 = nearest_16dir(b)
        hits = match_confirmed_axes(b)

        count += 1
        lines.append("")
        lines.append(f"■ {q['time']}  {q['place']}")
        lines.append(f"   M{q['mag']}  最大震度{scale_to_str(q['max_scale'])}  "
                      f"深さ{q['depth']}km")
        lines.append(f"   天城からの方位角: {b:.2f}°({d16})  距離: {d:.0f}km")
        if hits:
            for name, diff, note in hits:
                lines.append(f"   ★一致: {name}  (差{diff:.2f}°) {note}")
        else:
            lines.append(f"   一致する確定軸: なし")

    lines.append("")
    lines.append("-" * 60)
    lines.append(f"該当件数: {count}件")
    lines.append("-" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="天城起点 地震自動解析レポート")
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--min-mag", type=float, default=1.0)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--json-out", type=str, default=None)
    args = parser.parse_args()

    quakes = fetch_quakes(limit=args.limit, debug=args.debug)
    if not quakes:
        print("地震データを取得できませんでした。ネットワーク接続、"
              "またはAPIレスポンス構造の変更を確認してください。")
        sys.exit(1)

    report = build_report(quakes, days=args.days, min_mag=args.min_mag)
    print(report)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n[保存しました] {args.out}")

    if args.json_out:
        results = []
        for item in quakes:
            q = parse_quake(item)
            if q is None or q["mag"] is None or q["mag"] < args.min_mag:
                continue
            b = bearing(AMAGI[0], AMAGI[1], q["lat"], q["lon"])
            d = distance_km(AMAGI[0], AMAGI[1], q["lat"], q["lon"])
            hits = match_confirmed_axes(b)
            results.append({
                "time": q["time"],
                "place": q["place"],
                "mag": q["mag"],
                "depth": q["depth"],
                "max_scale": scale_to_str(q["max_scale"]),
                "bearing": round(b, 2),
                "dir16": nearest_16dir(b),
                "distance_km": round(d, 1),
                "matches": [{"name": n, "diff": round(diff, 2), "note": note}
                            for n, diff, note in hits],
            })
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "quakes": results,
        }
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"\n[JSON保存しました] {args.json_out}")


if __name__ == "__main__":
    main()
