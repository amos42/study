import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.messages import AIMessage


async def test_connection():
    # 테스트용으로 간단한 MCP 서버 연결 시도
    params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "d:/test"],
        transport="stdio",
    )
    
    print("Attempting to connect to MCP server...")
    async with stdio_client(params) as (read, write):
        print("stdio_client succeeded")
        
        async with ClientSession(read, write) as session:
            print("Session created")
            
            await session.initialize()
            print("Session initialized successfully")

            tools = await load_mcp_tools(session)
            print("Tools loaded successfully")
            
            # 모든 도구로 에이전트 생성
            model = ChatOpenAI(
                base_url="....",
                api_key="....",
                model="....")
            print("model initialized successfully")

            agent = create_agent(model, tools)
            print("agent created successfully")
            
            # 여러 서버를 사용할 수 있는 복잡한 쿼리로 에이전트 실행
            response = await agent.ainvoke({
                "messages": "최상위 디렉토리 내의 *.py 목록을 알려 줘. 한글로 답변해 줘."
            })

            # print(response)    
            return response

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    # print(result)
    content = ""
    for msg in result["messages"]:
        if type(msg) is AIMessage:
            content += msg.content + "\n"
    print(content)
