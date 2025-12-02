# MCP LLM Interaction Sample
# This sample demonstrates how to interact with an LLM using the MCP protocol

# import uvicorn
import json
import os
from typing import Dict, Any
from fastapi import FastAPI
from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.types import TextContent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_agent
from langchain.messages import AIMessage
from langchain_openai import ChatOpenAI
import asyncio
from typing import List, Dict      
from mcp.client.stdio import get_default_environment

# 서버 구성 정의
servers = [
    # {
    #     "name": "math",
    #     "params": StdioServerParameters(
    #         command="python", 
    #         args=["math_server.py"]
    #     )
    # },
    # {
    #     "name": "database",
    #     "params": StdioServerParameters(
    #         command="python", 
    #         args=["db_server.py"]
    #     )
    # }
    {
      "name": "local-mcp-server",
      "params": StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "d:/test"],
        # command="C:/Windows/System32/cmd.exe /C \"npx -y @modelcontextprotocol/server-filesystem d:/test\"",
        transport="stdio",
        # env={**get_default_environment(), "MY_API_KEY": "my_api_key"},
      )
    }    
]

async def connect_to_server(server_config):
    """단일 MCP 서버에 연결하고 도구를 로드합니다."""
    name = server_config["name"]
    params = server_config["params"]
    
    # read, write = await stdio_client(params).__aenter__()
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
    
            tools = await load_mcp_tools(session)
            return {
                "name": name,
                "session": session,
                "tools": tools,
                "cleanup": lambda: asyncio.gather(
                    session.__aexit__(None, None, None),
                    stdio_client(params).__aexit__(None, None, None)
                )
            }

async def run_multi_server_agent():
    # 모든 서버에 연결
    # connections = await asyncio.gather(
    #     *[connect_to_server(server) for server in servers]
    # )

    server_config = servers[0]

    name = server_config["name"]
    params = server_config["params"]

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
    
            tools = await load_mcp_tools(session)
            connections = [{
                "name": name,
                "session": session,
                "tools": tools,
                "cleanup": lambda: asyncio.gather(
                    session.__aexit__(None, None, None),
                    stdio_client(params).__aexit__(None, None, None)
                )
            }]
    
            try:
                # 모든 서버에서 모든 도구 수집
                all_tools = []
                for connection in connections:
                    all_tools.extend(connection["tools"])
                
                # 모든 도구로 에이전트 생성
                model = ChatOpenAI(
                    base_url="......",  # Changed to local endpoint
                    api_key=".......",
                    model="........")
                agent = create_agent(model, all_tools)
                
                # 여러 서버를 사용할 수 있는 복잡한 쿼리로 에이전트 실행
                response = await agent.ainvoke({
                    "messages": "*.py 목록을 알려 줘. 한글로 답변해 줘."
                })
                
                return response
    
            finally:
                # 모든 연결 정리
                for connection in connections:
                    await connection["cleanup"]()
                pass

# app = FastAPI()

# 다중 서버 에이전트 실행
if __name__ == "__main__":
    result = asyncio.run(run_multi_server_agent())
    content = ""
    for msg in result["messages"]:
        if type(msg) is AIMessage:
            content += msg.content + "\n"
    print(content)
    
    # uvicorn.run("sample_app:app", host="0.0.0.0", port=8000)
