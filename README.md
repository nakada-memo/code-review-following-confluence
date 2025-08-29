# Confluence設計書ベースのコードレビューMCPサーバー

Confluenceの設計書に沿ってコードレビューを行うMCPサーバーです。既存のConfluence MCPサーバーと連携して、設計書の内容とローカルのコード実装を比較・分析し、品質向上のための提案を行います。

## 機能

### 主な機能
- **設計書分析**: Confluenceページから要件や仕様を抽出
- **コード整合性チェック**: 設計書とコードの整合性を検証
- **潜在的問題検出**: 想定外の挙動やセキュリティリスクを検出
- **スペルミスチェック**: 一般的なスペルミスを検出
- **改善提案**: コード品質向上のための提案を生成

### レビュー観点
1. **設計書通りの実装**: 機能要件、API仕様、データモデルの実装確認
2. **想定外挙動の検出**: エラーハンドリング不備、無限ループ、セキュリティ問題等
3. **スペルミス検出**: 変数名、コメント等の一般的なスペルミス
4. **コード品質**: TODOコメント、デバッグ用出力、ファイルサイズ等の品質指標

## インストール

### 前提条件
- Python 3.8+
- 既存のConfluence MCPサーバーが設定済み
- Confluenceへのアクセス権限

### 1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 2. パッケージのインストール
```bash
pip install -e .
```

## MCP設定

MCP設定ファイル（`cline_mcp_settings.json`）に以下を追加してください：

```json
{
  "mcpServers": {
    "confluence-code-review": {
      "command": "python",
      "args": ["/path/to/your/project/mcp_server/main.py"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## 使用方法

### 基本的な使用方法

#### 1. 設計書の分析
```python
# MCPツールとして使用
use_mcp_tool(
    server_name="confluence-code-review",
    tool_name="analyze_design_documents",
    arguments={
        "page_ids": ["12345", "67890"],
        "cloud_id": "your-cloud-id"
    }
)
```

#### 2. コードレビューの実行
```python
# MCPツールとして使用
use_mcp_tool(
    server_name="confluence-code-review", 
    tool_name="review_code_against_confluence",
    arguments={
        "main_design_page_id": "12345",
        "related_page_ids": ["67890", "11111"],
        "code_directory": "/path/to/your/code",
        "cloud_id": "your-cloud-id",
        "file_patterns": ["*.py", "*.js", "*.java"]
    }
)
```

### パラメータ説明

#### analyze_design_documents
- `page_ids`: 分析対象のConfluenceページIDリスト
- `cloud_id`: Atlassian Cloud ID

#### review_code_against_confluence  
- `main_design_page_id`: メイン設計書のConfluenceページID（必須）
- `related_page_ids`: 関連設計書のページIDリスト（オプション）
- `code_directory`: レビュー対象コードのディレクトリパス（必須）
- `cloud_id`: Atlassian Cloud ID（必須）
- `file_patterns`: 対象ファイルパターン（デフォルト: `["*.py", "*.js", "*.java", "*.ts", "*.jsx", "*.tsx"]`）

## レビュー結果の見方

### サマリー
- レビュー対象ファイル数
- 設計書との不整合件数
- 潜在的問題件数
- スペルミス件数
- 改善提案件数
- 総合評価（良好/要改善）

### 詳細結果
1. **設計書との整合性**: 要件や仕様の実装状況
2. **潜在的問題**: セキュリティやパフォーマンスのリスク
3. **スペルミス**: 変数名やコメントのスペルミス
4. **改善提案**: コード品質向上の提案

## カスタマイズ

### チェックパターンの追加

`check_potential_issues`メソッドでチェックパターンを追加できます：

```python
patterns = [
    (r"your_pattern", "カスタムメッセージ"),
    # 他のパターン...
]
```

### スペルチェック辞書の拡張

`check_spelling`メソッドで一般的なスペルミス辞書を拡張できます：

```python
common_typos = {
    "your_typo": "correct_spelling",
    # 他のスペルミス...
}
```

## 開発・デバッグ

### ローカルテスト
```bash
python mcp_server/main.py
```

### ログ出力
サーバーの動作確認は標準エラー出力で確認できます。

## トラブルシューティング

### 一般的な問題

1. **ディレクトリが存在しません**
   - `code_directory`パラメータが正しいか確認
   - ディレクトリの読み取り権限を確認

2. **Confluenceページの取得エラー**
   - `cloud_id`とページIDが正しいか確認
   - Confluence MCPサーバーが設定済みか確認

3. **ファイル読み込みエラー**
   - ファイルの文字エンコーディング（UTF-8）を確認
   - ファイルアクセス権限を確認

## 実装ノート

### Confluence連携
現在の実装では、サンプルの設計書内容を使用しています。実際の運用では：
- Confluence MCPサーバーの`getConfluencePage`ツールを使用
- 実際のConfluence APIとの連携を実装
- 認証・認可の仕組みを追加

### 拡張性
- 新しいプログラミング言語のサポート
- より高度な静的解析ツールとの連携
- カスタムルールの外部設定ファイル化

## ライセンス

MIT License

## 貢献

プルリクエストとイシューは歓迎します。大きな変更を行う前にイシューで議論していただくことをお勧めします。
