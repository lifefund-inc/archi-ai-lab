# HANDOVER — 建築AIラボ

## 1. 今回やったこと

### プラットフォーム構築（ゼロから完成・デプロイまで）
- 「建築AIラボ（Archi AI Lab）」という建築AI経営研究会のナレッジプラットフォームを新規構築
- AI活用100本ノックの事例データ（`rewritten_100.json`）をWebプラットフォーム化
- GitHub Pagesにデプロイ済み: https://hakuto-t.github.io/archi-ai-lab/

### データ変換
- `build_web_data.py` — 元データ `rewritten_100.json` → `cases.json`, `filters.json`, `stats.json` に変換するスクリプト
  - 部署名を一般名に正規化（アドバイザー課→営業、建設課→施工管理 等）
  - ツール名のカンマ分割、フェーズ/目的の抽出、検索インデックス生成、年間削減時間の推計
- 元データの場所: `../AI事例100本ノック/_data/rewritten_100.json`

### SPA本体（`index.html` 1ファイル完結）
- **技術スタック**: Alpine.js + Intersectプラグイン（CDN）、CSS変数によるデザインシステム、ビルド不要
- **ヘッダー**: ロゴ120px、建築AIラボ48px（Zen Kaku Gothic New）、グラデーション文字、100事例カウントアップアニメーション
- **ヘッダー自動隠し**: 下スクロールでスライドアウト、上スクロールで即復帰（position:fixed + translate方式、ARRCHサイトと同じ挙動）
- **検索**: リアルタイム150msデバウンス、クリアボタン付き
- **フィルター**: 5軸（ツール/業務フェーズ/活用目的/部署/削減時間）、初期全展開、一括開閉ボタン、フィルター連動件数
- **カード**: 4列グリッド、フェーズ別グラデーションアクセントバー、マウス追従グローエフェクト、説明文2行表示
- **表示切替**: グリッド⇔リスト
- **セクション見出し**: 業務フェーズ順表示時にフェーズ名+件数のヘッダー挿入
- **モーダル**: 課題→解決策→成果の3ステップナビ、プロンプト表示/コピー、利用者の声
- **いいね機能**: localStorageベース、ハートボタン、いいね順ソート対応
- **URLパラメータ連動**: フィルター状態がURLに反映（共有・ブックマーク対応）
- **favicon**: ロゴの「AI」部分をトリミングして生成

### 変更したファイル
- `建築AIラボ/index.html` — SPA本体
- `建築AIラボ/build_web_data.py` — データ変換スクリプト
- `建築AIラボ/data/cases.json` — 変換済み事例データ（100件）
- `建築AIラボ/data/filters.json` — フィルターマスター
- `建築AIラボ/data/stats.json` — 統計データ
- `建築AIラボ/assets/logo_transparent.png` — ロゴ画像
- `建築AIラボ/assets/favicon-32.png`, `favicon-192.png`, `apple-touch-icon.png` — favicon

---

## 2. 判断・決定したこと

- **React/Next.jsを不採用**: 100件・年4回更新の静的サイトにビルドパイプラインはオーバーエンジニアリング。Alpine.js（CDN）でビルド不要に
- **ネーミング**: 「AI活用100本ノック」→「建築AIラボ」に変更。事例がどんどん増えるプラットフォームなので「100本」に縛られない名前に
- **デザイン方向**: ユーザー（40-60代建築会社経営者）の好みを踏まえ、白背景+日本的クリーンUI。ダークモードは不要と判断
- **部署名の一般化**: 社内部署名（アドバイザー課等）を一般名（営業等）に変換。`build_web_data.py` の `DEPT_NORMALIZE` で管理
- **いいね機能**: 現時点はlocalStorageで個人単位。全ユーザー共有ランキングにするにはFirebase等のバックエンド追加が必要
- **GitHub Pages**: 新規リポジトリ `hakuto-t/archi-ai-lab`、`gh-pages` ブランチからデプロイ

---

## 3. まだ終わっていないこと

### 高優先度
- **四半期更新のワークフロー確立**: 新しい `rewritten_100.json` が来た時の更新手順をスキル化
  - 手順: `rewritten_100.json` を差し替え → `py build_web_data.py` → `git add . && git commit && git push`
- **最新の修正をデプロイ**: ヘッダーの建築AIラボ48px化などローカルの最新変更がまだpushされていない

### 中優先度
- **いいね機能のバックエンド化**: Firebase/Supabase等で全ユーザー共有のランキングに
- **フッターの統計セクション**: ツール別利用割合バーチャートなど
- **OGP/SNSシェア対応**: og:image, og:title等のメタタグ追加
- **独自ドメイン対応**: GitHub PagesのCNAME設定

### 低優先度
- **旧フォルダの削除**: `CURSOR_PJ/AIナレッジバンクWEBプラットフォーム/` がまだ残っている（手動削除してOK）
- **PWA対応**: manifest.json追加でスマホアプリ風に

---

## 4. やって失敗したこと（繰り返さないために）

- **Alpine.jsでネストした`<template x-if>`**: `<template x-for>` の中に `<template x-if>` をネストするとカードが表示されなくなった。解決策: セクションヘッダーとカードを別々の `x-for` ループにし、CSS `order` プロパティで並び順を制御
- **ヘッダーのスクロール隠し（Alpine.jsリアクティブ方式）**: Alpine.jsの `:class` バインディングでスクロール制御しようとしたが動作せず。解決策: ネイティブJSのscrollイベント + bodyへのクラス付与 + `translate: 0 -100%`（GPU対応）方式に変更。参考: https://firstlayout.net/scroll-down-and-scroll-up-with-javascript/
- **`x-intersect` プラグイン未追加**: Alpine.js本体だけではIntersect機能が使えない。`@alpinejs/intersect` のCDNを別途追加が必要
- **フォルダリネーム失敗**: Claude Codeの作業ディレクトリがフォルダ内にあるとロックされてリネームできない。`cp -r` でコピーして対応

---

## 5. 注意点・気づいたこと

- **データの元ファイル**: `../AI事例100本ノック/_data/rewritten_100.json` が元データ。このファイルは100本ノックスキルが生成する
- **`build_web_data.py` のパス**: `DATA_DIR` が相対パスで `../AI事例100本ノック/_data` を参照している。フォルダ構造を変えたらここも修正が必要
- **ローカルサーバー**: `file://` ではfetchがCORSエラーになるので `py -m http.server 8081` で確認する
- **Gitブランチ**: 現在 `gh-pages` ブランチで作業中。デプロイもこのブランチから
- **デザインの参考サイト**: SANKOU!, 81-web.com, サウナイキタイ, DeNA AI活用100本ノック有志サイトを参考にした
- **フォント**: 「建築AIラボ」のタイトルは `Zen Kaku Gothic New`（Google Fonts）、本文は `Noto Sans JP`
- **事例数が増える場合**: 100件を超えてもフロント側は問題なく動く。`build_web_data.py` が新データを変換すればOK。ただし数百件になったらページネーション検討
