import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ChromaDB 클라이언트 초기화
chroma_client = chromadb.Client()

# 컬렉션 생성
collection = chroma_client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)

# 샘플 문서들
documents = [
    "Python은 프로그래밍 언어입니다",
    "ChromaDB는 벡터 데이터베이스입니다",
    "머신러닝은 인공지능의 한 분야입니다",
    "LangChain은 LLM 애플리케이션 개발을 위한 프레임워크입니다"
]

# 임베딩 모델 로드
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# 문서 임베딩 및 저장
for i, doc in enumerate(documents):
    embedding = model.encode(doc).tolist()
    collection.add(
        ids=[str(i)],
        documents=[doc],
        embeddings=[embedding],
        metadatas=[{"source": f"doc_{i}"}]
    )

# 쿼리 실행
query = "프로그래밍 언어"
query_embedding = model.encode(query).tolist()

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=2
)

print("검색 결과:")
for i, doc in enumerate(results['documents'][0]):
    print(f"{i+1}. {doc} (거리: {results['distances'][0][i]:.4f})")