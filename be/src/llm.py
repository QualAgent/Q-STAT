import os
from dotenv import load_dotenv

load_dotenv()


def get_llm():
    """
    .env의 LLM_PROVIDER에 따라 LLM 인스턴스를 반환.
    - "ollama": 로컬 Ollama 서버 (기본값, API 키 불필요)
    - "openai": OpenAI API
    - "bedrock": AWS Bedrock
    """
    provider = os.getenv("LLM_PROVIDER", "ollama")

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
            model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL_ID", "gpt-4o"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    elif provider == "bedrock":
        from langchain_aws import ChatBedrockConverse

        return ChatBedrockConverse(
            model=os.getenv("BEDROCK_MODEL_ID", "openai.gpt-oss-120b-1:0"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        )

    else:
        raise ValueError(f"지원하지 않는 LLM_PROVIDER: {provider}")
