import asyncio
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types


# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("code-eval-mcp")

server = Server("code-eval-prompt")


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """利用可能なリソースを一覧表示"""
    return [
        types.Resource(
            uri="flow://overview",
            name="Flow Overview",
            description="Confluence設計とコードベースを突合するための、収集〜評価の指揮用プロンプト",
            mimeType="text/plain",
        )
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """リソースの内容を読み取り"""
    if uri == "flow://overview":
        return """あなたは「設計遵守チェック」の指揮役。次の3ステップで進めます。

[段階]
1) get_confluence: Confluence設計書を取得し要件を抽出
   1-1) getAccessibleAtlassianResources で resourceType="confluence" を列挙し cloudId 決定
   1-2) メイン/サブページの本文・添付を取得し、要件/非機能/IF仕様/設定を抽出

2) scan_codebase: ローカルコードを依存追跡で走査し実装事実を収集
   2-1) 初期ファイル: hint_files があれば優先。無ければ project_root から主要ファイルを自動検出
   2-2) import/require を解析し依存関係を再帰追跡（dynamic import/lazy loadも考慮）
   2-3) list_files/search_files で不足を補完（除外: node_modules, .git, dist, build, .next, coverage）

3) evaluate_impl: 要件と実装を突合し pass/partial/fail と改善案を提示
   出力順: A 仕様要約 / B 実装サマリ / C 不一致一覧 / D リスク / E 改善提案 / F 追加質問"""
    
    raise ValueError(f"Unknown resource: {uri}")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """利用可能なツールを一覧表示"""
    return [
        types.Tool(
            name="generate_flow_overview",
            description="Confluence設計とコードベースを突合するための、収集〜評価の指揮用プロンプトを生成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "main_page": {
                        "type": "string",
                        "description": "Confluence のメイン設計ページの URL か ID"
                    },
                    "subpages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "サブページ一覧"
                    },
                    "project_root": {
                        "type": "string",
                        "default": ".",
                        "description": "ローカルコードの探索起点"
                    },
                    "hint_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "初期読込のヒントとなるファイル群"
                    },
                    "dependency_depth": {
                        "type": "integer",
                        "default": 2,
                        "description": "依存関係を辿る最大深さ"
                    }
                },
                "required": ["main_page"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """ツールの呼び出しを処理"""
    if name == "generate_flow_overview":
        main_page = arguments.get("main_page")
        subpages = arguments.get("subpages", [])
        project_root = arguments.get("project_root", ".")
        hint_files = arguments.get("hint_files", [])
        dependency_depth = arguments.get("dependency_depth", 2)
        
        sub = ", ".join(subpages) if subpages else "（なし）"
        hints = ", ".join(hint_files) if hint_files else "（なし）"
        
        prompt = f"""あなたは「設計遵守チェック」の指揮役。次の3ステップで進めます。

【対象情報】
- メインページ: {main_page}
- サブページ: {sub}
- project_root: {project_root}
- 初期読込ヒントファイル: {hints}
- 依存関係の最大深さ: {dependency_depth}

[段階]
1) get_confluence: Confluence設計書を取得し要件を抽出
   1-1) getAccessibleAtlassianResources で resourceType="confluence" を列挙し cloudId 決定
   1-2) メイン/サブページの本文・添付を取得し、要件/非機能/IF仕様/設定を抽出

2) scan_codebase: ローカルコードを依存追跡で走査し実装事実を収集
   2-1) 初期ファイル: hint_files があれば優先。無ければ project_root から主要ファイルを自動検出
   2-2) import/require を解析し **最大深さ {dependency_depth}** で再帰追跡（dynamic import/lazy loadも考慮）
   2-3) list_files/search_files で不足を補完（除外: node_modules, .git, dist, build, .next, coverage）

3) evaluate_impl: 要件と実装を突合し pass/partial/fail と改善案を提示
   出力順: A 仕様要約 / B 実装サマリ / C 不一致一覧 / D リスク / E 改善提案 / F 追加質問"""
        
        return [types.TextContent(type="text", text=prompt)]
    
    raise ValueError(f"Unknown tool: {name}")


async def main():
    """メイン関数 - サーバーを起動"""
    logger.info("Starting code-eval-mcp server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="code-eval-prompt",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
