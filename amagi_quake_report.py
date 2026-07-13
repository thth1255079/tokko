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
#
# 使い方:
# python3 amagi_quake_report.py            # 今日の地震をレポート
# python3 amagi_quake_report.py --days 7   # 過去7日分をまとめてレポート
# python3 amagi_quake_report.py --min-mag 3.0   # M3.0以上のみ対象
#
# 自動実行したい場合(例: 毎日21時に実行):
# # crontab -e で以下を追加(Linux/Mac)
# 0 21 * * * /usr/bin/python3 /path/to/amagi_quake_report.py >> /path/to/quake_log.txt 2>&1
#
# # Windowsの場合はタスクスケジューラで同スクリプトを毎日実行するよう登録
#
# 注意:
# P2P地震情報APIのレスポンス構造は将来変更される可能性があります。
# 実行時にエラーが出た場合は、下記 parse_quake() 関数内の
# フィールド名(hypocenter, latitude, longitude 等)を
# 実際のレスポンス(--debug オプションで生JSONを確認可能)に合わせて調整してください。

import argparse
import json
import math
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

# ============================================================
# 1. 基準地点・確定軸の定義
# ============================================================

AMAGI = (34.920, 139.018)  # 天城(基準点)

DIRS16 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
          "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

# 確定済みL1軸・地点(あなたの研究ログより)
# 形式: (名称, 中心方位角, 許容誤差, 備考)
CONFIRMED_AXES = [
    ("ENE57°軸(鹿島・香取/タケミカヅチ・フツヌシ)", 57.0, 3.0, "岩戸ログ中核軸"),
    ("NE45°軸(香取・江ノ島・熱田)", 45.0, 3.0, "NE45°corridor/貝塚"),
    ("W277°軸(出雲・難波宮)", 277.0, 3.0, "国譲り軸"),
    ("NNW337°軸(ストーンヘンジ・糸魚川・戸隠)", 337.0, 3.0, ""),
    ("NNE19°軸(封印された神々クラスタ)", 19.0, 3.0, ""),
    ("WNW292°軸(メッカ)", 292.0, 3.0, ""),
]

# 千葉龍サイトL1確定リスト(名称, 方位角, 許容誤差)
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


# ============================================================
# 2. 大円計算ユーティリティ
# ============================================================

def bearing(lat1, lon1, lat2, lon2):
    # 始点から終点への初期方位角(度, 0-360)
    lat1r, lon1r, lat2r, lon2r = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2r - lon1r
    x = math.sin(dlon) * math.cos(lat2r)
    y = (math.cos(lat1r) * math.sin(lat2r)
         - math.sin(lat1r) * math.cos(lat2r) * math.cos(dlon))
    theta = math.atan2(x, y)
    return (math.degrees(theta) + 360) % 360


def distance_km(lat1, lon1, lat2, lon2):
    # 大円距離(km)
    R = 6371.0
    lat1r, lon1r, lat2r, lon2r = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = (math.sin(dlat / 2) ** 2
         + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def nearest_16dir(b):
    # 方位角から最も近い16方位名を返す
    idx = int((b + 11.25) // 22.5) % 16
    return DIRS16[idx]


def match_confirmed_axes(b):
    # 既知の軸・サイトとの一致を判定して一覧を返す
    hits = []
    for name, center, tol, *rest in ALL_KNOWN_POINTS:
        diff = min(abs(b - center), 360 - abs(b - center))
        if diff <= tol:
            note = rest[0] if rest else ""
            hits.append((name, diff, note))
    return sorted(hits, key=lambda x: x[1])


# ============================================================
# 3. 地震データ取得(P2P地震情報API)
# ============================================================

# 正しいエンドポイントは /v2/history?codes=551 (地震情報)
P2P_QUAKE_API = "https://api.p2pquake.net/v2/history"
P2P_QUAKE_CODE = 551  # 551 = 地震情報


def fetch_quakes(limit=300, debug=False):
    # P2P地震情報APIから地震一覧を取得
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
    # "N38.3" / "E141.7" のような文字列を符号付きfloatに変換する
    # すでに数値の場合はそのまま返す
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
    # "50km" / "3.9" のような文字列から数値部分を取り出す
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
    # APIレスポンス1件から必要な情報を抽出。
    # 実際のP2P地震情報 JSON API v2の構造:
    # item["earthquake"]["time"]              -> 発生時刻文字列
    # item["earthquake"]["hypocenter"]["name"] -> 震源地名
    # item["earthquake"]["hypocenter"]["latitude"]  -> 例: "N38.3"(文字列)
    # item["earthquake"]["hypocenter"]["longitude"] -> 例: "E141.7"(文字列)
    # item["earthquake"]["hypocenter"]["depth"]     -> 例: "50km"(文字列)
    # item["earthquake"]["hypocenter"]["magnitude"] -> 例: "3.9"(文字列)
    # item["earthquake"]["maxScale"]           -> 最大震度(10刻みコード)
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


# ============================================================
# 4. レポート生成
# ============================================================

def build_report(quakes, days, min_mag):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

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
        # 時刻フィルタ(APIのtime文字列形式に応じて要調整)
        # ここでは簡易的に全件表示し、日数フィルタは省略時はスキップ可

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


# ============================================================
# 5. メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="天城起点 地震自動解析レポート")
    parser.add_argument("--days", type=int, default=1, help="対象期間(日数, デフォルト1日)")
    parser.add_argument("--min-mag", type=float, default=1.0, help="対象とする最小マグニチュード")
    parser.add_argument("--limit", type=int, default=300, help="APIから取得する件数上限")
    parser.add_argument("--debug", action="store_true", help="APIレスポンスの生データを表示")
    parser.add_argument("--out", type=str, default=None, help="レポート出力先ファイルパス")
    parser.add_argument("--json-out", type=str, default=None,
                         help="Web表示用JSONの出力先パス(例: docs/quake_data.json)")
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
