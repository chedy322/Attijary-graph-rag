import os
from clerk_backend_api import Clerk


class ClerkClientSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ClerkClientSingleton, cls).__new__(
                cls, *args, **kwargs
            )
            cls._instance._clerk = None
        return cls._instance

    def initialize(self):
        if self._clerk is None:
            secret_key = os.getenv("CLERK_SECRET_KEY")
            if not secret_key:
                raise ValueError("CLERK_SECRET_KEY environment variable is not set")
            self._clerk = Clerk(bearer_auth=secret_key)

    def authenticate_request(self, request, options=None):
        self.initialize()
        try:
            return self._clerk.authenticate_request(request, options)
        except Exception as e:
            raise

    def get_user(self, user_id):
        self.initialize()
        try:
            return self._clerk.users.get(user_id=user_id)
        except Exception as e:
            raise


clerk_client = ClerkClientSingleton()
