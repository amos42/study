import os
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.retrievers import BaseRetriever
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

def build_or_load_db(docs_dir: str, persist_dir: str = "chroma_db", chunk_size: int = 1000, chunk_overlap: int = 200):
    loader = DirectoryLoader(docs_dir, glob="**/*.txt")
    docs = loader.load()
    splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    vectordb = Chroma.from_documents(documents=docs, embedding=embeddings, persist_directory=persist_dir)
    try:
        vectordb.persist()
    except Exception:
        # persist() may already have been done internally; ignore if unsupported
        pass
    # vectordb = Chroma(embedding_function=embeddings, persist_directory=persist_dir)
    return vectordb

def create_rag_chain(llm: BaseChatModel, retriever: BaseRetriever):
    # RAG 프롬프트 템플릿 정의
    template = """다음 문서들을 참고하여 질문에 답해라. 문서에 답이 없으면 "모르겠습니다"라고 명확히 답해라.

문서들:
{context}

질문: {question}

답변:"""
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )
    
    # RAG chain 구성
    def format_docs(docs):
        return "\n\n---\n\n".join(d.page_content for d in docs)
    
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain

def main():
    docs_dir = "docs"  # 텍스트 파일(.txt) 모아둔 폴더
    db_dir = "chroma_db"

    print("인덱스 생성/로드 중...")
    vectordb = build_or_load_db(docs_dir, db_dir)
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})

    model_name = os.environ.get("OLLAMA_MODEL", "gemma3:1b")
    llm = ChatOllama(model=model_name, temperature=0.0)

    # RAG chain 생성
    rag_chain = create_rag_chain(llm, retriever)

    print("준비 완료. 질문 입력 (종료: quit)")
    while True:
        q = input("질문> ").strip()
        if not q or q.lower() in ("quit", "exit"):
            break
        ans = rag_chain.invoke(q)
        print("\n== 답변 ==")
        print(ans)
        print("-----------")

if __name__ == "__main__":
    main()