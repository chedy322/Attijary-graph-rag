# import os
# import weaviate

# class WeaviateClient:
#     _instance = None

#     def __new__(cls, *args, **kwargs):
#         if not cls._instance:
#             cls._instance = super(WeaviateClient, cls).__new__(cls, *args, **kwargs)
#             cls._instance._client = None
#         return cls._instance

#     def get_client(self) -> weaviate.Client:
#         if self._client is None:
#             url = os.getenv("WEAVIATE_URL")
#             api_key = os.getenv("WEAVIATE_API_KEY")

#             if not url:
#                 raise ValueError("WEAVIATE_URL environment variable is not set")

#             if api_key:
#                 auth_config = weaviate.AuthApiKey(api_key=api_key)
#                 self._client = weaviate.Client(url=url, auth_client_config=auth_config)
#             else:
#                 self._client = weaviate.Client(url=url)
#         return self._client

# weaviate_client = WeaviateClient()

import os
from urllib.parse import urlparse
import weaviate
from weaviate.classes.init import Auth


class WeaviateClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(WeaviateClient, cls).__new__(cls, *args, **kwargs)
            cls._instance._client = None
        return cls._instance

    def get_client(self) -> weaviate.WeaviateClient:
        if self._client is None:
            url = os.getenv("WEAVIATE_URL")
            api_key = os.getenv("WEAVIATE_API_KEY")

            if not url:
                raise ValueError("WEAVIATE_URL environment variable is not set")
            if not api_key:
                raise ValueError("WEAVIATE_API_KEY environment variable is not set")

            self._client = weaviate.connect_to_weaviate_cloud(
                cluster_url=url,
                auth_credentials=Auth.api_key(api_key) if api_key else None,
                skip_init_checks=True
            )

        return self._client


weaviate_client = WeaviateClient()
