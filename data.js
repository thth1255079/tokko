/* ============================================================
   共有データファイル（data.js）
   トップページと岩戸ログの両方がこのファイルを読む。
   ここを1箇所直せば全ページに反映される。
   ============================================================ */

/* ── 研究カテゴリ ──
   photo: img/ 内のタイル写真。無ければSVGの意匠が表示される */
const CATS = [
  { id:"tsuki", name:"月研究", photo:"img/cat-tsuki.jpg",
    desc:"月メジャースタンドスティル・月暦・月読命・環状列石" },
  { id:"shio",  name:"海民研究", photo:"img/cat-shio.jpg",
    desc:"塩ハイウェイ・布良・黒潮ネットワーク・海人族" },
  { id:"fuin",  name:"封印構造研究", photo:"img/cat-fuin.jpg",
    desc:"月読命封印・地名封印・禁足地・龍形地形研究" },
  { id:"world", name:"世界岩戸研究", photo:"img/cat-world.jpg",
    desc:"サグラダ・ストーンヘンジ・ソロヴェツキー・世界聖地の岩戸構造" },
  { id:"iwato", name:"地震ログ", photo:"img/cat-iwato.jpg", href:"iwato-log.html",
    desc:"天城16方位モデルによる地震と神格の対応分析" },
  { id:"field", name:"現地調査ログ", photo:"img/cat-field.jpg",
    desc:"現地調査・実測・写真・考察を時系列で記録" },
  { id:"chiba", name:"千葉という場所", photo:"img/cat-chiba.jpg",
    desc:"貝塚・麻賀多十八社・印旛沼・地名語源" },
  { id:"kami",  name:"隠蔽された神々", photo:"img/cat-kami.jpg",
    desc:"記紀が消した神々——ツクヨミ・フツヌシ・アマツミカボシ" },
];

/* ── 活動報告・研究記録 ──
   新しい報告はこの配列の先頭に追加。
   layer:"L1"(青)/"L2"(橙)/"L3"(赤)、plan:true で「予定」表示
   photos:[{src:"img/xxx.jpg", cap:"説明"}]  files:[{href:"pdf/xxx.pdf", label:"名前"}] */
const REPORTS = [
  { date:"2026-07-22", plan:true,
    title:"大湯環状列石にて月の北端出を観測（予定）",
    cats:["tsuki","field"], layer:"L1",
    body:"18.6年周期・月大停止の終盤にあたる北端月の出を、大湯環状列石で実地観測する。夜行バスで前夜発、当日鹿角花輪着。観測結果は帰着後に本欄とnoteで報告予定。",
    link:"", photos:[], files:[] },
  { date:"2026-06-26",
    title:"ENE 57°帯（鹿島軸）の静穏、69日で終了",
    cats:["iwato"], layer:"L2",
    body:"4月18日から続いたENE 57°帯の地震静穏が6月26日に破れた。経過の詳細は岩戸ログに記載。",
    link:"iwato-log.html", photos:[], files:[] },
  { date:"2026-06-25",
    title:"ベネズエラM7.5ダブレットと岩手M6.9の26分同期を記録",
    cats:["iwato"], layer:"L1",
    body:"ヤラクイ州のM7.2/M7.5（天城からNNE 32.85°–34.96°）の26分後に岩手M6.9（NNE 28.91°）。同一方位帯での同期として岩戸ログに記録。国外震源のため世界神話層を併記。",
    link:"iwato-log.html", photos:[], files:[] },
  { date:"2026年前半",
    title:"麻賀多十八社の方位確認を完了",
    cats:["chiba"], layer:"L1",
    body:"麻賀多神社18社の天城方位が46.67°–52.32°の帯に収まることを確認（惣社48.77°・奥宮49.97°・佐倉50.48°）。干拓前の印旛沼の形状との関係はL3仮説として別稿で展開。",
    link:"", photos:[], files:[] },
  { date:"2026年前半",
    title:"富神明神社（山形）の方位確認",
    cats:["world"], layer:"L1",
    body:"天城→富神明神社16.36°、天城→富神山16.46°（差0.1°）を計算で確認。縄文環状列石中央部に建立され、鳥居は富神山方向（北東53°）を向く。現地未訪問——実地確認は今後の課題。",
    link:"", photos:[], files:[] },
  { date:"2026年前半",
    title:"論考シリーズ「隠蔽された神々」開始",
    cats:["kami"], layer:"L3",
    body:"記紀が消した神々を追う全10回シリーズ。第1回「ふるべが起動している」公開。以後、フツヌシ、アマツミカボシと続く予定。",
    link:"https://note.com/fancy_sable4582", photos:[], files:[] },
];

/* ── 地震ログ（岩戸ログ本体） ──
   トップの「地震ログ 最新3件」表と iwato-log.html の両方に反映される。
   band: 16方位帯 / "■要確認" は朱枠表示 */
const LOGS = [
  {
    date:"2026-06-26",
    title:"ENE 57°帯、六十九日の沈黙が破れる",
    band:"ENE",
    deities:["タケミカヅチ"],
    layer:"L2",
    epicenter:"■要確認",
    mag:"■要確認",
    depth:"■要確認",
    bearing:"ENE 57° 帯（鹿島・香取軸）",
    memo:"4月18日から69日間続いたENE 57°帯（鹿島＝タケミカヅチ軸）の地震静穏が6月26日に終了。静穏期間の起点は箭挿神社参拝日と同日（L1：日付一致の記録。L3：関連の解釈は本文にて）。",
    note:"https://note.com/tokko_geo",
    photos:[], files:[]
  },
  {
    date:"2026-06-25",
    title:"ベネズエラM7.5ダブレットと岩手M6.9の26分同期",
    band:"NNE",
    deities:["世界神話層"],
    layer:"L1",
    epicenter:"ベネズエラ・ヤラクイ州／岩手県沖",
    mag:"M7.2・M7.5（ダブレット）／M6.9",
    depth:"■要確認",
    bearing:"NNE 32.85°–34.96°（ヤラクイ）／NNE 28.91°（岩手）",
    memo:"6月24–25日、ヤラクイ州でM7.2/M7.5のダブレット。天城からの方位はNNE帯。その26分後に岩手M6.9（NNE 28.91°）が発生し、同一方位帯での同期として記録。震源が国外のため世界神話層（タイノ／カリブ）を併記。",
    note:"https://note.com/tokko_geo",
    photos:[], files:[]
  },
  {
    date:"2026-04-01",
    title:"スカイツリー全復旧の6分後、茨城県南部M5.0",
    band:"ENE",
    deities:["タケミカヅチ"],
    layer:"L1",
    epicenter:"茨城県南部",
    mag:"M5.0",
    depth:"■要確認",
    bearing:"■要確認（ENE帯・要再計算）",
    memo:"4月1日、東京スカイツリーの全エレベーター復旧の6分後に茨城県南部でM5.0。時刻の近接をL1として記録（因果の主張はしない）。",
    note:"https://note.com/tokko_geo",
    photos:[], files:[]
  }
];

/* ── 地図用の地点データ ──
   ※表示用の概略座標。L1計算には各自の確定座標を使うこと。
   type: "origin"（天城）/ "world" / "jp" */
const AMAGI_LL = [34.920, 139.018];
const MAP_SITES = [
  { name:"天城山（起点）", ll:AMAGI_LL, type:"origin" },
  // 世界（NNW帯ほか）
  { name:"ストーンヘンジ", ll:[51.179, -1.826], type:"world", note:"NNW 336.65°" },
  { name:"エーヴベリー",   ll:[51.428, -1.854], type:"world", note:"NNW帯" },
  { name:"カルナック",     ll:[47.584, -3.078], type:"world", note:"NNW帯" },
  { name:"サグラダ・ファミリア", ll:[41.404, 2.174], type:"world", note:"NNW 329.05°" },
  { name:"ソロヴェツキー諸島",   ll:[65.03, 35.71], type:"world", note:"NNW 332.79°" },
  // 国内
  { name:"出雲大社", ll:[35.402, 132.685], type:"jp", note:"W 266°" },
  { name:"鹿島神宮", ll:[35.968, 140.631], type:"jp", note:"ENE 57°" },
  { name:"香取神宮", ll:[35.886, 140.529], type:"jp", note:"NE 54°軸" },
  { name:"諏訪大社", ll:[36.075, 138.114], type:"jp", note:"NNW 326°" },
  { name:"大湯環状列石", ll:[40.272, 140.789], type:"jp", note:"月MajStandstill軸" },
  { name:"黒又山", ll:[40.283, 140.796], type:"jp", note:"大湯→48.3°" },
  { name:"加曽利貝塚", ll:[35.635, 140.155], type:"jp", note:"NE 54°軸／月MajN" },
  { name:"麻賀多神社（惣社）", ll:[35.756, 140.253], type:"jp", note:"48.77°" },
  { name:"富神山", ll:[38.243, 140.263], type:"jp", note:"16.46°・現地未訪問" },
];

/* ── 画像ギャラリー ──
   フィールドワーク写真をここに登録すると「最近追加された画像」に並ぶ。
   例: { src:"img/oyu-01.jpg", cap:"大湯・野中堂日時計状組石" } */
const IMAGES = [
];
