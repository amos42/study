from typing import Annotated
from fastmcp import FastMCP
import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
# from langchain_classic.storage import LocalFileStore
# from langchain_classic.embeddings import CacheBackedEmbeddings
# from chromadb import HttpClient
import dotenv

# dotenv.load_dotenv(dotenv_path="../")
dotenv.load_dotenv()


EMBEDDINGS_API_KEY = os.getenv("EMBEDDINGS_API_KEY")
EMBEDDINGS_API_BASE = os.getenv("EMBEDDINGS_API_BASE")
EMBEDDINGS_API_MODEL = os.getenv("EMBEDDINGS_API_MODEL", "BAAI/bge-m3")

collection_name = "common_api_library"
persist_dir = ".chromadb"

embeddings = OpenAIEmbeddings(model=EMBEDDINGS_API_MODEL, api_key=EMBEDDINGS_API_KEY, base_url=EMBEDDINGS_API_BASE, tiktoken_enabled=False)

# 로컬 파일 저장소 설정 - ".cache" 폴더에 캐시 파일 저장
# store = LocalFileStore(".cache")

# 캐시를 지원하는 임베딩 생성
# cached_embedder = CacheBackedEmbeddings.from_bytes_store(
#     underlying_embeddings=embeddings,  # 실제 임베딩을 수행할 모델
#     document_embedding_cache=store,  # 캐시를 저장할 저장소
#     namespace=collection_name,  # 모델별로 캐시를 구분하기 위한 네임스페이스
#     key_encoder="sha256",
#     query_embedding_cache=True
# )    

# client = HttpClient(
#     host="localhost",
#     port=9000,
#     # ssl=False
# )    

vector_db = Chroma(
    embedding_function=embeddings,
    collection_name=collection_name,
    # client=client
    persist_directory=persist_dir
)

mcp = FastMCP("MyServer")


@mcp.tool(name="search_funcs")
async def tool_search_funcs(
        func_desc: Annotated[str, "함수 설명"]
    ) -> list:
    """
    사내 공용 라이브러리에서 설명과 관련이 높은 함수들의 목록과 설명을 리턴한다.

    args:
      func_desc: 함수의 설명

    result: 함수의 원형과 설명
    """
    # return vectordb.similarity_search_with_score(func_desc)
    return vector_db.similarity_search(func_desc)
    # return vectordb.similarity_search_with_relevance_scores(query=func_desc, score_threshold=0.8)


@mcp.prompt(name="make_code")
async def tool_make_code(
       lang: Annotated[str, "분류코드"],
       code_desc: Annotated[str, "작성하고자 하는 코드 명세"]
    ) -> str:
    """Generates a user message asking for an explanation of a topic."""
    if lang == "C":
        return f"""나는 사내에서 운영하기 위한 '{lang}'언어 프로젝트를 진행 중인 개발자이다.
    사내 공용 라이브러리에 이용 가능한 함수들이 제공되며, 최대한 이 함수들을 재활용해서 중복 코드를 없애도록 할 것이다.
    사내 공용 라이브러리에 포함 된 함수들의 정보는 vecotr-db에 저장되어 있으며, tool을 이용해 열람할 수 있다.
    '{code_desc}' 코드를 작성해 줘."""
    else:
        return code_desc


@mcp.resource(uri="data://config")
async def get_config() -> dict:
    """Provides the application configuration."""
    return {"theme": "dark", "version": "1.0"}


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=3000)
