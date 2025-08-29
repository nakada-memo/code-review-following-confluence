# pip install mcp
from mcp.server.fastmcp import FastMCP

app = FastMCP("design-eval-director")

# docstring にパラメータ説明を書いておくとクライアントで見やすい
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
    - main_files: 重要ファイル（優先的に確認したい相対パス）
    """
    sub = ", ".join(subpages or [])
    files = ", ".join(main_files or [])
    return f"""
あなたは設計遵守チェックの指揮役です。
**Atlassian公式の Confluence MCP サーバ**のみを使って設計書を取得し、
ローカルコードを静的に見て「設計どおりか」を簡潔に判定してください。

# 入力
- Confluence メイン: {main_page}
- サブページ: {sub or "(なし)"}
- プロジェクトルート: {project_root}
- 重要ファイル: {files or "(なし)"}

# ツール利用の方針（厳守）
- Confluence 情報取得は Atlassian公式の Confluence MCP ツールのみ（例: search/get_page/get_content）。
- ローカル解析はクライアントのファイル系ツール（glob/read）を使う。
- 外部Web/APIの直接呼び出しや新規認証要求はしない。

# 出力
1) 設計の主要要求（箇条書き）
2) 実装の判定: pass / partial / fail（根拠となるファイル名・行範囲をできる範囲で）
3) 直近の改善提案（最小差分での修正ポイント）
"""

if __name__ == "__main__":
    # stdout は MCP プロトコル専用。ログは logging か stderr を使うこと
    app.run()
