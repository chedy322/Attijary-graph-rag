import os
import threading
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings


class LlmSingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LlmSingleton, cls).__new__(cls)
                    cls._instance.llm = None
                    cls._instance.embedding_model = None
        return cls._instance

    def get_llm(self) -> ChatGoogleGenerativeAI:
        if not self.llm:
            with self._lock:
                if not self.llm:  # Double-check lock pattern
                    llm_api_key = os.getenv("LLM_API_KEY")
                    if not llm_api_key:
                        raise ValueError("LLM_API_KEY environment variable is not set")
                    self.llm = ChatGoogleGenerativeAI(
                        model="gemini-3.6-flash",
                        temperature=0,
                        google_api_key=llm_api_key,
                    )
        return self.llm

    def get_embedding_model(self) -> GoogleGenerativeAIEmbeddings:
        if not self.embedding_model:
            with self._lock:
                if not self.embedding_model:
                    llm_api_key = os.getenv("LLM_API_KEY")
                    if not llm_api_key:
                        raise ValueError("LLM_API_KEY environment variable is not set")
                    self.embedding_model = GoogleGenerativeAIEmbeddings(
                        model="gemini-embedding-001", google_api_key=llm_api_key
                    )
        return self.embedding_model


llm_singleton = LlmSingleton()
