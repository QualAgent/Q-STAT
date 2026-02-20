"""
임베딩 모델 팩토리.

LLM_PROVIDER 환경변수에 따라 적절한 임베딩 모델 반환.
indexer.py와 retriever.py가 공유 사용.
"""
import os


def get_embeddings():
    """
    LLM_PROVIDER에 맞는 임베딩 모델 반환.

    - bedrock : amazon.titan-embed-text-v2:0  (기본)
    - openai  : text-embedding-3-small
    - ollama  : nomic-embed-text
    """
    provider = os.getenv("LLM_PROVIDER", "ollama")

    if provider == "bedrock":
        from langchain_aws import BedrockEmbeddings
        return BedrockEmbeddings(
            model_id=os.getenv("BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        )
    elif provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBEDDING_MODEL_ID", "text-embedding-3-small"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    else:  # ollama
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
            model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        )
