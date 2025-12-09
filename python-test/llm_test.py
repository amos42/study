from langchain_ollama import ChatOllama
from langchain.messages import HumanMessage

def main():
    # 로컬 Ollama에서 사용할 모델 이름을 지정 (예: "gemma3:1b")
    model = ChatOllama(model="gemma3:1b")

    # LangChain chat 모델은 배치 형태의 메시지 리스트를 받습니다.
    # 여기서는 단일 사용자 메시지를 단일 배치로 전달합니다.
    messages_batch = [[HumanMessage(content="한글로 간단히 자기소개해줘.")]]
    result = model.generate(messages_batch)

    # result.generations는 [[ChatGeneration]] 형태입니다.
    text = result.generations[0][0].message.content
    print(text)

if __name__ == "__main__":
    main()