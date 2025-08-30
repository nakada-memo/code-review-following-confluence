# Code Evaluation MCP Server

このMCPサーバーは、Confluence設計書とコードベースを照合するためのツールとリソースを提供します。

## 機能

### ツール
- `generate_flow_overview`: 設計遵守チェックのためのプロンプトを生成

### リソース
- `flow://overview`: 基本的な設計遵守チェックのフロー説明

## 設定方法

### 1. Cline設定ファイルへの追加

Clineの設定ファイル（通常は`~/.cline/config.json`または`%APPDATA%\Cline\config.json`）に以下を追加：

```json
{
  "mcpServers": {
    "code-eval-prompt": {
      "command": "python",
      "args": ["C:/Users/misim/project/code-review-following-confluence/mcp_server/server.py"],
      "cwd": "C:/Users/misim/project/code-review-following-confluence"
    }
  }
}
```

### 2. VS Code settings.json への追加（代替方法）

`.vscode/settings.json` に以下を追加：

```json
{
  "cline.mcpServers": {
    "code-eval-prompt": {
      "command": "python",
      "args": ["./mcp_server/server.py"],
      "cwd": "."
    }
  }
}
```

## 使用方法

### ツールの呼び出し例

```javascript
// Cline内でMCPツールを使用
use_mcp_tool({
  "server_name": "code-eval-prompt",
  "tool_name": "generate_flow_overview",
  "arguments": {
    "main_page": "https://yourcompany.atlassian.net/wiki/spaces/PROJECT/pages/123456789/Design+Document",
    "subpages": [
      "https://yourcompany.atlassian.net/wiki/spaces/PROJECT/pages/987654321/API+Specification"
    ],
    "project_root": "./src",
    "hint_files": ["./src/main.py", "./src/config.py"],
    "dependency_depth": 3
  }
})
```

### リソースへのアクセス例

```javascript
// 基本フローの取得
access_mcp_resource({
  "server_name": "code-eval-prompt",
  "uri": "flow://overview"
})
```

## 実行確認

サーバーが正常に動作するか確認：

```bash
cd mcp_server
python server.py
```

サーバーが起動し、標準入力を待機する状態になれば正常です（Ctrl+Cで停止）。

## トラブルシューティング

### よくある問題

1. **ImportError**: `mcp`パッケージがインストールされていない
   ```bash
   pip install mcp>=0.1.0
   ```

2. **パス関連エラー**: 絶対パスを使用するか、相対パスを正しく設定

3. **権限エラー**: Pythonの実行権限を確認

### デバッグ

ログレベルを調整してデバッグ情報を確認：

```python
logging.basicConfig(level=logging.DEBUG)
```

## パラメータ説明

### generate_flow_overview ツール

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| main_page | string | ✓ | Confluenceのメイン設計ページのURLまたはID |
| subpages | array | | 関連するサブページのリスト |
| project_root | string | | ローカルコードの探索起点（デフォルト: "."） |
| hint_files | array | | 初期読み込みのヒントファイル |
| dependency_depth | integer | | 依存関係を辿る最大深さ（デフォルト: 2） |
