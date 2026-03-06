from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import os
import dotenv

dotenv.load_dotenv()

# Chroma DB 설정
CHROMA_COLLECTION_NAME = "sample_collection"

# OpenAI API 키 확인
EMBEDDINGS_API_KEY = os.getenv("EMBEDDINGS_API_KEY")
EMBEDDINGS_API_BASE = os.getenv("EMBEDDINGS_API_BASE")
EMBEDDINGS_API_MODEL = os.getenv("EMBEDDINGS_API_MODEL")

# 샘플 텍스트 데이터
texts = [
    "인공지능은 현대 과학 기술의 핵심입니다.",
    "머신러닝과 딥러닝은 AI의 하위 분야입니다.",
    "최근 한식은 건강식이라는 인식과 다채로운 맛, K-콘텐츠의 영향으로 세계적인 열풍을 끌고 있다.",
    "벡터 데이터베이스는 유사도 검색에 매우 유용합니다.",
    "Chroma DB는 로컬 및 원격 호스팅이 가능한 벡터 DB입니다.",
    "OpenAI의 임베딩 모델은 고품질 벡터 생성을 제공합니다.",
    "닌텐도 스위치는 TV 모드 - 테이블 모드 - 휴대용 모드라는 3가지 형태로 활용 가능한 거치가 가능한 하이브리드 게임기이다.",
    "맥도날드의 가성비는 최근 들어 의심을 받고 있다.",
    "Youtube의 광고는 사용자의 짜증을 유발하고 있다. Youtube는 노골적으로 유료 구독으로 사용자를 몰고 있다."
]

# 임베딩 모델 초기화
embeddings = OpenAIEmbeddings(base_url=EMBEDDINGS_API_BASE,
                            api_key=EMBEDDINGS_API_KEY,
                            model=EMBEDDINGS_API_MODEL,
                            tiktoken_enabled=True)

# Chroma 벡터 스토어 초기화 및 데이터 저장
vectorstore = Chroma.from_texts(
    texts=texts,
    embedding=embeddings,
    collection_name=CHROMA_COLLECTION_NAME,
)

# 샘플 검색 쿼리 실행
# query = "AI와 관련된 기술에는 무엇이 있나요?"
# query = "멀티미디어 관련된 정보는 무엇이 있는가?"
query = "의식주에 관한 주목할만한 정보는?"
results = vectorstore.similarity_search_with_score(query, k=5)

# 검색 결과 출력
print("검색 쿼리:", query)
for i, (result, score) in enumerate(results):
    print(f" > {i+1}. {result.page_content} ({score})")
