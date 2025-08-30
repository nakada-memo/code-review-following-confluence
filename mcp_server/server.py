from mcp.server.fastmcp import FastMCP

app = FastMCP("code-eval-prompt")

# ──────────────────────────────────────────────────────────────────────────────
# ① 全体の流れ（オーケストレーション用の短指示）
# ──────────────────────────────────────────────────────────────────────────────
@app.prompt()
def flow_overview(
    main_page: str,
    subpages: list[str] | None = None,
    project_root: str = ".",
    entry_files: list[str] | None = None,
) -> str:
    sub = ", ".join(subpages or [])
    files = ", ".join(entry_files or [])
    return f"""
あなたは「設計遵守チェック」の指揮役。以下の5段階で進めます。

[入力]
- confluence_main: {main_page}
- confluence_subpages: {sub or "(なし)"}
- project_root: {project_root}
- entry_files: {files or "(なし)"}

[段階]
1) get_confluence: Confluence設計書を取得し要件を抽出
2) scan_discover: entry_filesを起点に依存関係をたどり候補ファイル集合を特定（本文は読まない）
3) scan_harvest: 候補集合から評価に必要なだけ本文を読み、実装事実を収集
4) evaluate_impl: 要件と実装の突合で pass/partial/fail 判定
5) suggest_fixes: 最小差分での改善提案を作成

[出力形式]
各段階は JSON で出力し、次段への入力に渡す:
- get_confluence → {{ "requirements": [...], "nonfuncs": [...], "io_specs": [...], "configs": [...] }}
- scan_discover → {{ "seeds": [...], "candidate_files": [...], "dep_edges": [...], "notes": [...] }}
- scan_harvest → {{ "impl_facts": [...], "dep_edges": [...], "configs_found": [...], "coverage_estimate": ... }}
- evaluate_impl → {{ "verdict": "pass|partial|fail", "evidence": [...], "gaps": [...] }}
- suggest_fixes → {{ "patch_plan": [...], "risk_notes": [...] }}

次の段階に進んでください: get_confluence
""".strip()


# ──────────────────────────────────────────────────────────────────────────────
# ② Confluence 内容取得（短指示 + 出力スキーマ固定）
# ──────────────────────────────────────────────────────────────────────────────
@app.prompt()
def get_confluence(
    main_page: str,
    subpages: list[str] | None = None,
) -> str:
    sub = ", ".join(subpages or [])
    return f"""
目的: Confluence設計書から要件を抽出する。

制約:
- Atlassian公式 Confluence MCP ツールのみを使用すること
- 新規認証要求や外部Web/API直呼びはしない

手順(簡潔):
1) getAccessibleAtlassianResources で resourceType="confluence" を列挙し対象 cloudId を決定
2) メインページを解決:
   - IDなら getPageById(cloudId, pageId)
   - URLなら resolvePageIdFromUrl → getPageById
   - タイトルなら searchPages → pageId → getPageById
3) サブページ（あれば）も同様に取得
4) 本文から以下を抽出（短文・粒度一定）:
   - requirements: 機能要件 (動詞+対象+条件)
   - nonfuncs: 非機能要件 (可用性/性能/監査/エラー方針等)
   - io_specs: IF仕様（エンドポイント/スキーマ/例外/コード/HTTP）
   - configs: 設定・フラグ（キー, 既定値, 範囲）

出力(JSON, keys厳守):
{{
  "requirements": ["..."],
  "nonfuncs": ["..."],
  "io_specs": [{{"path":"...","method":"GET|POST|...","request":"...","response":"...","errors":["..."]}} ],
  "configs": [{{"key":"...","default":"...","range":"...","source_page":"...#h-..."}}]
}}

入力:
- main: {main_page}
- subs: {sub or "(なし)"}
""".strip()

# ──────────────────────────────────────────────────────────────────────────────
# ③ コード走査（依存追跡・規約探索・広域フォールバック）
# ──────────────────────────────────────────────────────────────────────────────
@app.prompt()
def scan_discover(
    project_root: str = ".",
    entry_files: list[str] | None = None,
) -> str:
    files = ", ".join(entry_files or [])
    return f"""
目的:
- entry_files を手掛かりに依存関係を静的に“発見”し、本文を読まずに候補ファイル一覧を作る（entry_filesは出発点であり上限ではない）。

前提/制約:
- 解析対象: TS/JS/TSX、Python、Java など
- 読み取りはヘッダ/宣言/import/require/dynamic import/exports/ルーティング定義など**参照情報に限定**（本文の関数内部は読まない）
- 規約ディレクトリでの補完探索: routes/, controllers/, services/, repositories/, migrations/, schemas/, middlewares/
- 除外: node_modules, .git, dist, build

手順(簡潔):
① seeds を確定: entry_files（なければ規約ディレクトリの代表ファイルをseedに追加）
② 各seedの参照情報を抽出し、依存先パスを正規化（エイリアス/tsconfig paths/webpack alias 等を解決）
③ 依存先をキューに積み、**本文を読まず**参照情報のみを再帰辿り（最大幅/深さにガード）
④ ルータ→コントローラ→サービス→リポジトリ→マイグレーションなどの**規約鎖**で未カバー領域を補完
⑤ 到達したファイルパスを candidate_files として列挙、依存辺 dep_edges を付与

出力(JSON, keys厳守):
{{
  "seeds": [{files or ""}],
  "candidate_files": ["rel/or/abs/path1.ts", "..."],
  "dep_edges": [{{"from":"A.ts","to":"B.ts","via":"import|dynamic|ioc|route","lines":"12-18","reason":"export used by ..."}}],
  "notes": ["alias=@app/* を src/* に解決", "深さガード depth<=6 で停止 など"]
}}
""".strip()


# ──────────────────────────────────────────────────────────────────────────────
# ③ コード走査（依存追跡・規約探索・広域フォールバック）
# ──────────────────────────────────────────────────────────────────────────────
@app.prompt()
def scan_harvest(
    project_root: str = ".",
    candidate_files: list[str] | None = None,
    requirements: list[str] | None = None,
    max_files: int | None = None,           # 例: None=自動、整数なら上限
    breadth_fallback: bool = True,          # 足りなければ周辺依存を少しだけ拡張可
) -> str:
    cands = ", ".join(candidate_files or [])
    reqs = "; ".join(requirements or [])
    return f"""
目的:
- candidate_files から**評価に必要なだけ**本文を開いて実装事実を収集し、評価入力の最終スキーマを組み立てる。

入力:
- candidate_files: [{cands or "(なし)"}]
- requirements(hint): {reqs or "(なし)"}
- project_root: {project_root}
- max_files: {max_files if max_files is not None else "(auto)"}
- breadth_fallback: {breadth_fallback}

読取方針:
- 優先順位: requirements に整合するIF/処理/設定周辺 → 依存の起点/終端 → テスト対象/マイグレーション
- 収集点: ファイル/シンボル、I/O(HTTP/DB/FS/Queue)、例外/ログ/リトライ/Tx、設定キー参照
- via 由来と行範囲を付与。dep_edges は必要に応じて補完/精緻化
- フォールバック: 必要証跡が欠ける場合のみ、近傍依存を限定的に拡張（breadth_fallback=true）

出力(JSON, keys厳守):
{{
  "impl_facts": [{{"file":"...","symbol":"...","lines":"12-48","notes":"...","io":{{"path":"...","method":"..."}},"errors":["..."],"logs":["..."],"retries":{{"policy":"..."}}, "tx":"required|supports|none"}}],
  "dep_edges": [{{"from":"A.ts:foo","to":"B.ts:bar","via":"import|dynamic|ioc|route","lines":"...","reason":"..."}} ],
  "configs_found": [{{"key":"...","file":"...","lines":"...","default?":true}} ],
  "coverage_estimate": 0.0,
  "read_files": ["..."],      # 実際に本文を開いたファイル
  "skipped_files": ["..."],   # 候補だが未読（閾値/不要判断）
  "stop_reason": "enough_evidence|max_files_reached|exhausted"
}}
""".strip()


# ──────────────────────────────────────────────────────────────────────────────
# ④ 実装評価（突合・判定・最小差分の提案）
# ──────────────────────────────────────────────────────────────────────────────
@app.prompt()
def evaluate_impl() -> str:
    return """
目的: Confluence抽出結果と実装事実を突合し、判定と改善案を出す。

入力(JSON想定):
{
  "confluence": {
    "requirements": [...],
    "nonfuncs": [...],
    "io_specs": [...],
    "configs": [...]
  },
  "code": {
    "impl_facts": [...],
    "dep_edges": [...],
    "configs_found": [...],
    "coverage_estimate": 0.0
  }
}

判定軸(最小語彙):
- 仕様準拠: 要件/IF/エラー/設定が一致しているか
- リスク: 境界値/例外/同時実行/タイムアウト/部分失敗/キャッシュ/時刻/ロケール/永続化整合
- エラ処理: 例外→ログ→伝播→リトライ/バックオフ
- 性能/スケール: N+1, 同期I/O, 大応答, 再計算, キャッシュ戦略

出力(JSON):
{
  "verdict": "pass" | "partial" | "fail",
  "evidence": [
    {"why":"...", "trail": ["A.ts:foo(10-20) -> B.ts:bar(5-12)", "config.yml:keyX"], "matches":["req#3","io:/v1/items GET"] }
  ],
  "gaps": [
    {"req":"...", "missing":"...", "suspected_place":"...", "note":"..."}
  ],
  "patch_plan": [
    {"file":"...", "lines?":"...", "edit":"追加/修正の要点(最小差分)", "test":"テスト観点"}
  ],
  "risk_notes": ["..."]
}
""".strip()


if __name__ == "__main__":
    app.run()
