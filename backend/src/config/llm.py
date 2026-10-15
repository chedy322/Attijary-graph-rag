import os
import threading
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openrouter import ChatOpenRouter

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
                    cls._instance.router_model = None
                    cls._instance.quick_model = None
        return cls._instance


    # This llm for Ai Re-Act agent
    def get_llm(self) -> ChatGoogleGenerativeAI:
        if not self.llm:
            with self._lock:
                if not self.llm:  # Double-check lock pattern
                    llm_api_key = os.getenv("LLM_API_KEY")
                    if not llm_api_key:
                        raise ValueError("LLM_API_KEY environment variable is not set")
                    primary_model = ChatGoogleGenerativeAI(
                        model="gemini-3.5-flash-lite",
                        temperature=0,
                        google_api_key=llm_api_key,
                        max_output_tokens=1024,
                        timeout=30000
                    )
                    fallback_model = ChatGoogleGenerativeAI(
                        model="gemini-3.1-flash-lite",
                        temperature=0,
                        google_api_key=llm_api_key,
                        max_output_tokens=1024,
                        timeout=30000
                    )
                    self.llm = primary_model.with_fallbacks([fallback_model])
        return self.llm

    # This embedding model is used for vectorization of text data for semantic search and retrieval.
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

    # # This router model is used for routing queries to the appropriate tools or methods based on the context and history of the conversation.
    # def get_router_model(self):
    #     if not self.router_model:
    #         with self._lock:
    #             if not self.router_model:
    #                 llm_api_key = os.getenv("OPENROUTER_API_KEY")
    #                 if not llm_api_key:
    #                     raise ValueError("OPENROUTER_API_KEY environment variable is not set")
    #                 self.router_model = ChatOpenRouter(
    #                     model="anthropic/claude-3-haiku", 
    #                     temperature=0.0
    #                 )
                    
    #     return self.router_model

    # This quick model is used for lightweight and fast classification of user queries to determine the appropriate method or tool to invoke.
    def get_quick_anwser_model(self):
        # if not self.quick_model:
        #     with self._lock:
        #         if not self.quick_model:
        #             llm_api_key = os.getenv("OPENROUTER_API_KEY")
        #             if not llm_api_key:
        #                 raise ValueError("OPENROUTER_API_KEY environment variable is not set")
        #             primary_model = ChatOpenRouter(
        #                 model="qwen/qwen-2.5-72b-instruct:free",
        #                 api_key=llm_api_key,
        #                 temperature=0.1,
        #                 max_retries=3,
        #                 max_tokens=512,
        #                 model_kwargs={
        #                      "models":[
        #                                 "google/gemma-4-31b-it:free",
        #     "meta-llama/llama-3.3-70b-instruct:free",
        #     "mistralai/mistral-small-24b-instruct-2501:free"
        #                             ],
        #                 },
                       
        #                 timeout=30000
        #             )
        #             self.quick_model=primary_model.with_fallbacks([self.get_llm()])

        return self.get_llm()  # For now, return the same LLM instance for quick answers. You can replace this with a different model if needed.

llm_singleton = LlmSingleton()
