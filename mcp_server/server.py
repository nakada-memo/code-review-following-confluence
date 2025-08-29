from mcp.server.fastmcp import FastMCP

app = FastMCP("code-eval-prompt")

@app.prompt()
def confluence_eval(
    main_page: str,
    subpages: list[str] | None = None,
    project_root: str = ".",
    main_files: list[str] | None = None,
) -> str:
    """
    Confluence の設計書とローカルコードから、設計遵守チェックを行うためのプロンプトを生成します。
    - main_page: メインのConfluenceページURLまたはタイトル
    - subpages: 関連サブページ
    - project_root: ローカルのプロジェクトルート（globの基準）
    - main_files: 起点ファイル（プロジェクト走査する際の起点となる相対パス）
    """
    sub = ", ".join(subpages or [])
    files = ", ".join(main_files or [])
    return f"""
あなたは設計遵守チェックの指揮役です。
**Atlassian公式の Confluence MCP サーバ**のみを使って設計書を取得し、
以下の手順に沿って「設計どおりか」を判定してください。

# 手順
1) 入力を確認し、Confluenceの対象サイトとページを特定する。
2) MCPツールを使って本文を取得する。
3) 本文から要件を抽出する。
4) ローカルコードを段階的に走査する：
   a) まず main_files を読み込む
   b) 次に依存関係を再帰的に追跡する（import/require、呼び出し関係、設定ファイル参照等）
   c) 追跡した全てのファイルを読み込む
   d) 要件カバー率を確認し、不足があれば project_root 配下を更に走査する
   **注意：main_files のみで終了してはならない。必ず関連ファイルまで走査すること**
5) レビュー観点に従って判定し、出力フォーマットに従って回答する。

# 入力
- Confluence メイン: {main_page}
- サブページ: {sub or "(なし)"}
- プロジェクトルート: {project_root}
- 起点ファイル（プロジェクト走査する際の起点となる相対パス）: {files or "(なし)"}

# ツール利用の方針（厳守）
- Confluence 情報取得は Atlassian公式の Confluence MCP ツールのみ（例: search/get_page/get_content）。
- ローカル解析はクライアントのファイル系ツール（glob/read/grep 等）を使う。
- **必要な依存関係は必ず追跡**すること（import/require、呼び出し関係、外部サービス呼出しなど）。影響範囲を把握したうえで根拠を提示する。
- 外部Web/APIの直接呼び出しや新規認証要求はしない。

# Confluence呼び出し順序（厳守）
1) **getAccessibleAtlassianResources** を呼び出し、`resourceType = "confluence"` のリソースから対象サイトの **cloudId** を決定する。
   - 複数ある場合は `url`/`name` が入力と整合するものを選択し、以降の呼び出しにその **cloudId** を用いる。
2) メインページを取得する。
   - `main_page` が **pageId** 形式なら: `getPageById(cloudId, pageId)`（または等価のAPI）で本文取得。
   - **URL** なら: 必要に応じて `resolvePageIdFromUrl(cloudId, url)` → `getPageById`。
   - **タイトル**のみなら: `searchPages(cloudId, title=..., spaceKey=... など)` で **pageId** を解決してから `getPageById`。
3) サブページ群があれば、各要素について 2) と同様に解決・取得する（ID優先、URL→解決、タイトル→検索→ID→取得）。
4) 取得した本文から要件を抽出して後続の突合評価へ進む。

# コード解析ポリシー
- **main_filesは解析の出発点**であり、**解析範囲の上限ではない**。
- 依存関係を**グラフ的に再帰追跡**する（import/require/dynamic import、ルータ登録、DI/IoC、テスト→対象コード、マイグレーション→エンティティ等）。
- **設定/環境依存**も辿る（env読込、設定YAML/JSON、Feature Flag、ミドルウェア連鎖）。
- フレームワークの**約束事の自動参照**（例: routes/, controllers/, services/, repositories/, migrations/, schemas/, middlewares/）。
- 依存追跡後も、**要件がカバーされない場合は project_root を広くグロブ走査**して該当実装をサーチ（node_modules, .git, dist, build` は除外）。

# スコープ拡張ルール
- いずれかに該当したら **main_files 以外へ拡張**:
  - 抽出要件の実装箇所が未発見／不十分
  - 横断要件（認証・認可・エラー方針・監査ログ・リトライ・トランザクション・Schema整合）が未確認
  - 参照先が外縁に到達（例: ルータ→コントローラ→サービス→リポジトリ→マイグレーション）
  
# レビュー観点
- **仕様準拠**：設計書（要件/IF仕様/エラー仕様/設定値）に対して、実装が一致しているか。
- **予期しない挙動のリスク**：境界値/例外/タイムアウト/同時実行/再試行/部分失敗/ネットワーク揺らぎ/キャッシュ不整合/時刻依存/ロケール依存/永続化の整合性などの観点で、想定外が起きうる箇所を洗い出す。
- **エラーハンドリング**：例外の握りつぶし、ログの粒度、ユーザー/呼び出し元への伝播方針、リトライ/バックオフ。
- **パフォーマンス/スケール**：N+1、不要な同期I/O、巨大レスポンス、無駄な再計算、キャッシュ戦略。

# 出力
1) 設計の概要（箇条書き）
2) 実装の判定: **pass / partial / fail**
   - 根拠: ファイル名・概ねの行範囲・依存関係の辿り方（例: A.py の関数 foo → B.py の bar → 設定 config.yml の値 X）
3) 直近の改善提案（最小差分での修正ポイント）
"""

if __name__ == "__main__":
    app.run()
