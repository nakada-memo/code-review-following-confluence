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
# 役割・目的
あなたは設計遵守チェックの指揮役です。Confluence設計書とローカルコードを比較し、設計遵守を判定してください。

# 入力パラメータ
- Confluence メイン: {main_page}
- サブページ: {sub or "(なし)"}
- プロジェクトルート: {project_root}
- 起点ファイル: {files or "(なし)"}

# 重要な制約（必ず遵守）
- Confluence情報取得はAtlassian公式のConfluence MCPツールのみ使用
- main_filesは解析の出発点であり、上限ではない
- 依存関係を必ず再帰的に追跡すること
- 外部Web/APIの直接呼び出しや新規認証要求は禁止

# 実行手順
## 1. Confluence設計書の取得
1) **getAccessibleAtlassianResources**を呼び出し、cloudIdを決定
   - resourceType = "confluence"のリソースから対象サイトを特定
   - 複数ある場合はurl/nameが入力と整合するものを選択
2) メインページを取得
   - pageId形式: getPageById(cloudId, pageId)で本文取得
   - URL形式: resolvePageIdFromUrl → getPageById
   - タイトル形式: searchPages → pageId解決 → getPageById
3) サブページがあれば同様に取得
4) 本文から要件を抽出

## 2. ローカルコード解析
1) main_filesを起点として読み込み開始
2) 依存関係をグラフ的に再帰追跡
   - import/require/dynamic import
   - ルータ登録、DI/IoC
   - テスト→対象コード
   - マイグレーション→エンティティ
   - 設定/環境依存（env、YAML/JSON、Feature Flag）
3) フレームワーク規約に基づく自動参照
   - routes/, controllers/, services/, repositories/
   - migrations/, schemas/, middlewares/
4) 要件カバー不足時はproject_root配下を広域走査
   - 除外: node_modules, .git, dist, build

## 3. スコープ拡張判定
以下に該当する場合は必ずmain_files以外へ拡張:
- 抽出要件の実装箇所が未発見/不十分
- 横断要件が未確認（認証・認可・エラー方針・監査ログ・リトライ・トランザクション・Schema整合）
- 参照先が外縁到達（ルータ→コントローラ→サービス→リポジトリ→マイグレーション）

## 4. レビュー評価
以下の観点で判定:
- **仕様準拠**: 設計書（要件/IF仕様/エラー仕様/設定値）との一致
- **予期しない挙動リスク**: 境界値/例外/タイムアウト/同時実行/再試行/部分失敗/ネットワーク揺らぎ/キャッシュ不整合/時刻依存/ロケール依存/永続化整合性
- **エラーハンドリング**: 例外処理、ログ粒度、伝播方針、リトライ/バックオフ
- **パフォーマンス/スケール**: N+1、不要同期I/O、巨大レスポンス、無駄再計算、キャッシュ戦略

# 出力形式
1) 設計の概要（箇条書き）
2) 実装の判定: **pass / partial / fail**
   - 根拠: ファイル名・行範囲・依存関係の辿り方
   - 例: A.py の関数foo → B.py のbar → 設定config.ymlの値X
3) 直近の改善提案（最小差分での修正ポイント）
"""

if __name__ == "__main__":
    app.run()
