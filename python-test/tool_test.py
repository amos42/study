#%%capture --no-stderr
#%pip install python-dotenv bs4 langchain langchain-community langchain-openai


import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain.messages import AIMessage
from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker
from langchain_core.prompts import PromptTemplate
import glob
from fastapi import FastAPI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from fastapi.middleware.cors import CORSMiddleware
from langchain_chroma import Chroma
from chromadb import HttpClient
import uvicorn
import dotenv
from langchain_community.tools.file_management import WriteFileTool

dotenv.load_dotenv()

prompt_template = """다음 문서들을 참고하여 질문에 답해라.

문서들:
{context}

질문: {messages}

답변:"""

# URL = "postgresql://catalog:password@localhost/catalog_db"
engine = create_engine(url=os.getenv("DB_URL"), echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)
inspector = inspect(engine)

client = HttpClient(
    # settings=client_settings
    host="localhost",
    port=9000,
    # ssl=False
)    

embeddings = OpenAIEmbeddings(base_url=os.getenv("EMBEDDINGS_API_BASE"),
                              api_key=os.getenv("EMBEDDINGS_API_KEY"), 
                              model=os.getenv("EMBEDDINGS_API_MODEL"))

vector_db = Chroma(
    embedding_function=embeddings,
    collection_name="data_migrate_db",
    client=client
)

@tool
def tool_list_files(path: str, pattern: str, recursive: bool) -> list[str]:
    """특정 디렉토리 속의 파일의 목록을 얻는다.

    Args:
        path: 디렉토리
        pattern: 와일드카드(*, ?, **)를 포함한 파일 목록 패턴. (예제. 서브디렉토리 포함시, './**/*.txt')
        recursive: 자식 디렉토리 포함 여부
    """

    return glob.glob(os.path.join(path, pattern), recursive=recursive)

@tool
def tool_list_schema_names() -> list[str]:
    """DB schema 목록을 얻는다.

    Args:
    """
    return inspector.get_schema_names()

@tool
def tool_list_tables(schema: str = "public") -> list[str]:
    """DB 테이블 목록을 얻는다.

    Args:
        schema: 스키마 이름. 디폴트는 public
    """

    return inspector.get_table_names(schema=schema)

@tool
def tool_get_table_info(table_name: str, schema: str = "public") -> list:
    """DB 테이블의 상세 컬럼 정보를 얻는다.

    Args:
        table: 테이블 이름
        schema: 스키마 이름. 디폴트는 public
    """

    lst = inspector.get_columns(table_name, schema=schema)
    return lst

@tool
def tool_get_db_record(table_name: str, schema: str = "public", count: int = 3) -> list:
    """DB 테이블에서 레코드를 읽는다.

    Args:
        table: 테이블 이름
        schema: 스키마 이름. 디폴트는 public
        count: 읽을 레코드 갯수. 디폴트는 3
    """

    metadata = MetaData()
    table = Table(table_name, metadata, schema=schema, autoload_with=engine)

    lst = []
    with SessionLocal.begin() as session:
        records = session.query(table).limit(count).all()
        for r in records:
            lst.append(r)
    return lst

@tool
def tool_search_vector_db(query: str, k: int = 2) -> list:
    """벡터 DB에서 쿼리와 관련성이 높은 문서들을 검색하여 결과를 리스트로 가져 온다.
       벡터 DB는 테이블 스펙 및 참고 문서를 담고 있다.

    Args:
        query (str): 검색 쿼리 텍스트
        k (int): 검색 결과 상위 몇 개를 가져올지. 기본값은 2

    Returns:
        List[Document]: 검색 결과 리스트. 만약 결과가 없다면 빈 list
    """

    lst = vector_db.similarity_search(query, k)
    if len(lst) == 0:
        lst = [""]
    return lst

# @tool
# def tool_write_text_file(filename: str, content: str):
#     """문자열 컨텐츠를 실제 파일로 저장한다. (인코딩: UTF-8)

#     Args:
#         filename: 저장할 파일명
#         content: 텍스트 데이터
#     """

#     with open(filename, "w", encoding="utf-8") as file:
#         file.write(content)
#         file.flush()
#         os.fsync(file.fileno())

def _format_docs(docs):
    return "\n\n---\n\n".join(d.page_content for d in docs)

write_tool = WriteFileTool(root_dir="d:/test")

class DataMigrate:
    def __init__(self):
        self.llm = ChatOpenAI(openai_api_base=os.getenv("OPENAI_API_BASE"), model_name=os.getenv("OPENAI_API_MODEL"))
        tools = [tool_list_files,
                 tool_list_schema_names,
                 tool_list_tables,
                 tool_get_table_info,
                 tool_get_db_record,
                 tool_search_vector_db,
                 write_tool]
        self.agent = create_agent(self.llm, tools=tools)
        retriever = vector_db.as_retriever(search_kwargs={"k": 4})
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "messages"]
        )
        self.chain = (
            {
                "context": (lambda x: x["input"] if isinstance(x, dict) else x) | retriever | _format_docs,
                "messages": lambda x: x["input"] if isinstance(x, dict) else x
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
    
    def query(self, msg: list[str]) -> str:
        # 리스트를 문자열로 변환
        result = self.agent.invoke(input={"messages": msg})
        # query_text = " ".join(msg) if isinstance(msg, list) else msg
        # result = self.chain.invoke(input={"input": query_text})
        # return result
        content = ""
        for msg in result["messages"]:
            if type(msg) is AIMessage:
                content += msg.content + "\n"
        return content

# engine.dispose()

# app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     expose_headers=["*"]
# )

# @app.get("/")
# async def read_root():
#     return {"Hello": "World"}

# @app.post("/")
# async def write_root():
#     content = dm.query([
#         "DB의 public 스키마의 catalog 관련 테이블들을 분석해서 그 분석 결과와 상세한 설명을 파일로 저장해 줘.",
#         "데이터의 기본 포맷은 markdown 텍스트이고, 저장할 디렉토리는 d:/test/output/이며, 파일 확장자는 .md이다.",
#         "한글로 답해 줘. 꼭 파일을 생성해야만 해."
#     ])
#     return content

# if __name__ == "__main__":
#     uvicorn.run("data_migrate:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    dm = DataMigrate()

    content = dm.query([
        "DB의 public 스키마의 catalog 관련 테이블들을 분석해서 그 분석 결과와 상세한 설명 문서를 만들어 줘.",
        "테이블을 분석할 때, 해당 테이블에 대한 스펙 및 참고 정보를 벡터 DB로부터 찾아서 만약 내용이 존재한다면 이를 바탕으로 설명을 보강해 줘.",
        "필요하다면 테이블의 레코드를 적당량(약 3개 전후)를 읽어내서 그 값을 분석에 이용할 수 있어.",
        "필드의 설명을 표로 만들 땐 요약 내용인 short와 상세한 내용인 long을 표시 실어 줘.",
        "데이터의 기본 포맷은 markdown 텍스트이고, 이를 파일로 저장해 줘. 저장할 디렉토리는 d:/test/output/이며, 파일 확장자는 .md이다.",
        "한글로 답해 줘.",
        "결과물을 반드시 tool을 이용해 실제 파일로 저장해 줘.",
    ])
    print(content)

    # print(inspector.get_schema_names())
    # print(inspector.get_table_names(schema="public"))
    # print(inspector.get_columns("ToolListTables", schema="public"))
