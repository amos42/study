import os
from sentence_transformers import SentenceTransformer
import chromadb

# EMBEDDING_MODEL="BAAI/bge-m3"
# EMBEDDING_MODEL="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# EMBEDDING_MODEL="google/embeddinggemma-300m"
# EMBEDDING_MODEL="intfloat/multilingual-e5-large-instruct"
# EMBEDDING_MODEL="snunlp/KR-SBERT-V40K-klueNLI-augSTS"
# EMBEDDING_MODEL="nlpai-lab/KURE-v1"
EMBEDDING_MODEL="kakaocorp/kanana-nano-2.1b-embedding"

# HF_TOKEN="......"

documents_kor = [
    "인공지능은 현대 과학 기술의 핵심이다.",
    "머신러닝과 딥러닝은 AI의 하위 분야입니다.",
    "최근 한식은 건강식이라는 인식과 다채로운 맛, K-콘텐츠의 영향으로 세계적인 열풍을 끌고 있다.",
    "벡터 데이터베이스는 유사도 검색에 매우 유용합니다.",
    "Chroma DB는 로컬 및 원격 호스팅이 가능한 벡터 DB다.",
    "OpenAI의 임베딩 모델은 고품질 벡터 생성을 제공한다.",
    "닌텐도 스위치는 'TV 모드' / '테이블 모드' / '휴대용 모드'라는 3가지 형태로 활용 가능한 하이브리드 게임기이다.",
    "몇년 전부터 많은 이들이 저렴하다고 알려진 맥도날드 햄버거의 가성비에 의구심을 표시하고 있다.",
    "Youtube의 광고는 사용자의 짜증을 유발하고 있다. Youtube는 노골적으로 유료 구독으로 사용자를 몰고 있다.",
    "2026년 초 한국 주택 시장은 정부의 강력한 부동산 정책으로 주요 지역의 상승세가 꺾이며 하락 전환하는 등 안정화 조짐을 보이고 있다",
    "K-패션은 중성적인 디자인, 독창적인 실루엣, 트렌디함을 앞세워 전 세계적으로 주목받고 있으며, K-팝 아이돌의 영향력으로 글로벌 시장에서 높은 인기를 얻고 있다.",
]

model = SentenceTransformer(
    EMBEDDING_MODEL,
    trust_remote_code=True,
)

documents = documents_kor
embeddings = model.encode(documents, prompt="recall relevant information")

client = chromadb.Client()
collection = client.create_collection("my_collection")
ids = [str(i) for i in range(len(documents))]
collection.add(ids=ids, embeddings=embeddings.tolist(), documents=documents)

query = "사람들의 의식주에 관한 정보"
query_embeddings = model.encode([query], prompt="recall relevant information")
query_embedding = query_embeddings[0]

results = collection.query(query_embeddings=query_embeddings, n_results=5)

print("Query:", query)
print("\nSearch Results:")
for i, (doc, dist) in enumerate(zip(results["documents"][0], results["distances"][0])):
    print(f"{i + 1}. {doc} (distance: {dist:.4f})")
