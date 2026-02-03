import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
# from langchain_classic.storage import LocalFileStore
# from langchain_classic.embeddings import CacheBackedEmbeddings
# from chromadb import HttpClient
import dotenv

dotenv.load_dotenv(dotenv_path="../")

EMBEDDINGS_API_KEY = os.getenv("EMBEDDINGS_API_KEY")
EMBEDDINGS_API_BASE = os.getenv("EMBEDDINGS_API_BASE")
EMBEDDINGS_API_MODEL = os.getenv("EMBEDDINGS_API_MODEL")

def load_db(collection_name: str = "sample_collection", persist_dir: str = ".chromadb"):
    embeddings = OpenAIEmbeddings(model=EMBEDDINGS_API_MODEL, api_key=EMBEDDINGS_API_KEY, base_url=EMBEDDINGS_API_BASE, tiktoken_enabled=False)

    # 로컬 파일 저장소 설정 - ".cache" 폴더에 캐시 파일 저장
    # store = LocalFileStore(".cache")

    # 캐시를 지원하는 임베딩 생성
    # cached_embedder = CacheBackedEmbeddings.from_bytes_store(
    #     underlying_embeddings=embeddings,  # 실제 임베딩을 수행할 모델
    #     document_embedding_cache=store,  # 캐시를 저장할 저장소
    #     namespace=collection_name,  # 모델별로 캐시를 구분하기 위한 네임스페이스
    #     query_embedding_cache=True
    # )    

    # client = HttpClient(
    #     host="localhost",
    #     port=9000,
    #     # ssl=False
    # )    

    vector_db = Chroma(
        # embedding_function=cached_embedder,
        embedding_function=embeddings,
        collection_name=collection_name,
        # client=client
        persist_directory=persist_dir
    )

    return vector_db

# 벡터 DB 검색 기능 구현
def search_vector_db(vectordb: Chroma, query_text, top_k=3):
    """
    벡터 DB에서 유사한 텍스트 검색

    Args:
        query_text (str): 검색 쿼리 텍스트
        top_k (int): 검색 결과 상위 몇 개를 가져올지

    Returns:
        List[Document]: 검색 결과
    """
    return vectordb.similarity_search_with_score(query_text)

db_dir = ".chromadb"
collection_name = "common_api_library"

print("인덱스 로드 중...")
vectordb = load_db(collection_name, db_dir)

# 샘플 검색 쿼리 실행
query = "로그인 함수"
results = search_vector_db(vectordb, query)

# 검색 결과 출력
print("검색 쿼리:", query)
idx = 1
for result, score in results:
    print(f"=============================\n* {idx}: 유사성:{score}")
    print(f"결과. {result.page_content}")
    idx += 1
