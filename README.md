# Confluence設計書ベースのコードレビューMCPサーバー

Confluenceの設計書に沿ってコードレビューを行うMCPサーバーです。既存のConfluence MCPサーバーと連携して、設計書の内容とローカルのコード実装を比較・分析し、品質向上のための提案を行います。

## 導入手順

### 前提条件
- python、nodeが使える環境であること
- clineをインストールしていること
- clineが使える状態であること

### 1. mcp-remoteのインストール
```bash
npm install -g mcp-remote
```

### 2. cline_mcp_settings.jsonの編集
clineの設定ファイルを開き、まずは`atlassian mcp server`の導入をします
接続するかvscodeを開き直すかするとatlassianの認証ページが開かれたはずです
confluenceへのアクセス許可をしてacceptしてください
```json
{
  "mcpServers": {
    "atlassian": {
      "autoApprove": [],
      "disabled": false,
      "timeout": 60,
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.atlassian.com/v1/sse"
      ],
      "env": {},
      "transportType": "stdio"
    }
  }
}
```

### 3. code-eval-mcpの設定
依存関係をインストール
```bash
pip install -r requirements.txt
```

### 4. パッケージのインストール
```bash
pip install -e .
```

### 5. cline_mcp_settings.jsonへの追記
先ほどのatlassianを追加した設定ファイルにさらに追記し、最終的に以下のようになります
```json
{
  "mcpServers": {
    "atlassian": {
      "autoApprove": [],
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.atlassian.com/v1/sse"
      ],
      "env": {}
    },
    "code-eval-prompt": {
      "autoApprove": [],
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "python",
      "args": [
        "<絶対パス>/code-review-following-confluence/mcp_server/server.py"
      ],
      "env": {}
    }
  }
}
```

## 使用方法
clineで以下のプロンプトを入力してください
```
server_name: code-eval-prompt  
tool_name: generate_flow_overview
arguments: {
  "main_page": "173735938",
  "subpages": [
    "207519745",
    "167706625"
  ],
  "project_root": "<絶対パス>\project\kaonamae-nodejs",
  "hint_files": [
    "controllers\common\life.ts", 
    "services\common\lifeService.ts"
  ],
  "dependency_depth": 3
}
```

### パラメータ説明
- `main_page`: confluenceの設計書のメインとなるページ(URL全体ではなくページIDが良い気がします)
- `subpages`: `main_page`のほかに読み込ませたいページ
- `project_root`: ローカルにあるプロジェクトルート
- `hint_files`: 今回評価したいファイルのヒント
- `dependency_depth`: どこまで依存関係を辿るかの数字
