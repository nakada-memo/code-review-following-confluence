# MCPサーバー使用例

## 基本的な呼び出し方法

### 1. リソースの取得
フロー概要を取得する場合：

```
use_mcp_tool で以下のように呼び出します:

server_name: code-eval-prompt
tool_name: generate_flow_overview
arguments: {
  "main_page": "https://example.atlassian.net/wiki/pages/123456/Design"
}
```

または、リソースに直接アクセス：

```
access_mcp_resource で以下のように呼び出します:

server_name: code-eval-prompt
uri: flow://overview
```

### 2. 完全な設計遵守チェックの例

```
use_mcp_tool で以下のように呼び出します:

server_name: code-eval-prompt  
tool_name: generate_flow_overview
arguments: {
  "main_page": "https://yourcompany.atlassian.net/wiki/spaces/PROJECT/pages/123456789/システム設計書",
  "subpages": [
    "https://yourcompany.atlassian.net/wiki/spaces/PROJECT/pages/987654321/API仕様書",
    "https://yourcompany.atlassian.net/wiki/spaces/PROJECT/pages/555666777/データベース設計"
  ],
  "project_root": "./src",
  "hint_files": [
    "./src/main.py", 
    "./src/models/__init__.py",
    "./src/api/routes.py"
  ],
  "dependency_depth": 3
}
```

## 実際のワークフロー例

### Step 1: MCPサーバー経由でプロンプト生成
上記の`use_mcp_tool`コマンドを実行すると、設計遵守チェック用の詳細なプロンプトが生成されます。

### Step 2: 生成されたプロンプトに従って作業
生成されたプロンプトには以下の3段階の指示が含まれます：

1. **get_confluence**: Confluence設計書の取得と要件抽出
2. **scan_codebase**: ローカルコードの依存関係追跡
3. **evaluate_impl**: 要件と実装の突合・評価

### Step 3: 各段階での具体的なツール使用
- Confluence取得: `getAccessibleAtlassianResources`、`getConfluencePage`等
- コード分析: `list_files`、`read_file`、`search_files`等  
- 評価レポート: 分析結果のまとめと改善提案の生成

## 設定確認

VS Codeでこのプロジェクトを開き直すか、Clineを再起動してMCPサーバーが認識されることを確認してください。

正常に設定されている場合、Cline内で「use_mcp_tool」を使用する際に「code-eval-prompt」サーバーが選択肢に表示されます。
