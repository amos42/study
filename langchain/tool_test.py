# %%capture --no-stderr
# %pip install python-dotenv bs4 langchain langchain-community langchain-openai

import os
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
import dotenv

dotenv.load_dotenv()

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")

@tool
def tool_op_sharp(a: int, b: int) -> int:
    """두 숫자의 # 연산을 수행해서 결과값을 얻는다. (ex. a # b = result)

    Args:
        a, b: 입력 숫자 값
    Result:
        a # b 한 연산 결과값
    """
    return a * b

llm = ChatOpenAI(
    model=OPENAI_API_MODEL,
    base_url=OPENAI_API_BASE,
    temperature=0.1
)

tools = [
    tool_op_sharp,
]
agent = create_agent(llm, tools=tools)

prompt_t = [
    "모든 메시지는 한글로 표시한다.",
    "모르는 연산이면 모른다고 답하고, 임의로 추측을 하지 않는다.",
    "{input}"
]

def _extract_final_message(result):
    msgs = result.get('messages', []) if isinstance(result, dict) else []
    outmsgs = ""
    for msg in msgs:
        if isinstance(msg, AIMessage):
            outmsgs += msg.content
    return outmsgs

chain = (ChatPromptTemplate.from_messages(prompt_t) | llm | StrOutputParser())
chain_and_tool = (ChatPromptTemplate.from_messages(prompt_t) | agent | RunnableLambda(_extract_final_message))
 
if __name__ == "__main__":
    query = "2 # 3의 값은?"

    content1 = llm.invoke(query)
    print("\n== 답변 (no tool) ==")
    print(content1.content)
    print("=======================")

    content2 = chain.invoke({"input": query})
    print("\n== 답변 (using chain) ==")
    print(content2)
    print("=======================")

    # content3 = agent.invoke({"messages": [{"role": "user", "content": query}]})
    content3 = agent.invoke({"messages": [query]})
    print("\n== 답변 (using tool) ==")
    print(_extract_final_message(content3))
    print("=======================")

    content4 = chain_and_tool.invoke({"input": query})
    print("\n== 답변 (using chain & tool) ==")
    print(content4)
    print("=======================")
