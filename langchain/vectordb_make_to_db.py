import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_classic.storage import LocalFileStore
from langchain_community.storage import RedisStore
from langchain_classic.storage import InMemoryByteStore
from langchain_classic.embeddings import CacheBackedEmbeddings
# from chromadb import HttpClient
import hashlib
import dotenv

dotenv.load_dotenv()

EMBEDDINGS_API_KEY = os.getenv("EMBEDDINGS_API_KEY")
EMBEDDINGS_API_BASE = os.getenv("EMBEDDINGS_API_BASE")
EMBEDDINGS_API_MODEL = os.getenv("EMBEDDINGS_API_MODEL")

def build_or_load_db(docs_dir: str, collection_name = "common_api_library", persist_dir: str = ".chromadb", chunk_size: int = 2000, chunk_overlap: int = 50):
    embeddings = OpenAIEmbeddings(base_url=EMBEDDINGS_API_BASE,
                                api_key=EMBEDDINGS_API_KEY, 
                                model=EMBEDDINGS_API_MODEL,
                                tiktoken_enabled=False) # OpenAI에 없는 커스텀 모델을 사용하기 때문)
    # 로컬 파일 저장소 설정 - ".cache" 폴더에 캐시 파일 저장
    store = LocalFileStore(".cache")

    # 캐시를 지원하는 임베딩 생성
    cached_embedder = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings=embeddings,  # 실제 임베딩을 수행할 모델
        document_embedding_cache=store,  # 캐시를 저장할 저장소
        namespace=collection_name,  # 모델별로 캐시를 구분하기 위한 네임스페이스
        key_encoder="sha256",
        query_embedding_cache=True
    )    

    loader = DirectoryLoader(docs_dir, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs={"autodetect_encoding": True})
    splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    texts = loader.load_and_split(splitter)
    # docs = loader.load()
    # texts = splitter.split_documents(docs)

    # client = HttpClient(
    #     host="localhost",
    #     port=8000,
    #     # ssl=False
    # )    

    def make_id(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    ids = [make_id(t.page_content) for t in texts]

    vector_db = Chroma.from_documents(
        documents=texts,
        embedding=cached_embedder,
        collection_name=collection_name,
        persist_directory=persist_dir,
        ids=ids  # 👈 ID 지정
    )

    return vector_db

def main():
    docs_dir = "docs"  # 텍스트 파일(.txt) 모아둔 폴더
    db_dir = ".chromadb"
    collection_name = "common_api_library"

    print("인덱스 생성/로드 중...")
    vectordb = build_or_load_db(os.path.join(os.path.dirname(__file__), docs_dir), collection_name, db_dir)

    if vectordb:
        print("인덱스 생성 완료.")
    else:
        print("인덱스 생성 실패.")

if __name__ == "__main__":
    main()
