from langchain_openai import ChatOpenAI
from src.core.config import config

def get_llm(temperature: float=None, max_tokens: int=None, **kwargs) -> ChatOpenAI:
    if temperature is None:
        temperature = config.temperature
    if max_tokens is None:
        max_tokens = config.max_tokens
    return ChatOpenAI(model=config.llm_model_name, api_key=config.llm_api_key, base_url=config.llm_api_base, temperature=temperature, max_tokens=max_tokens, **kwargs)