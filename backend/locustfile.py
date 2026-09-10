import os
from uuid import UUID
from locust import HttpUser, between, task



def env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


class BackendApiUser(HttpUser):
    """Simulates a user exercising the API's safe read paths."""

    wait_time = between(
        float(os.getenv("LOCUST_MIN_WAIT_SECONDS", "1")),
        float(os.getenv("LOCUST_MAX_WAIT_SECONDS", "3")),
    )

    def on_start(self) -> None:
        # Falls back to default token if LOCUST_AUTH_TOKEN is empty
        token = os.getenv("LOCUST_AUTH_TOKEN", "").strip()
        if token:
            self.client.headers.update({"Authorization": f"Bearer {token}"})

        self.chat_id = self._optional_uuid("LOCUST_CHAT_ID")
        self.document_id = self._optional_uuid("LOCUST_DOCUMENT_ID")

    @staticmethod
    def _optional_uuid(name: str) -> str | None:
        value = os.getenv(name, "").strip()
        if not value:
            return None
        try:
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError(f"{name} must contain a valid UUID") from exc

    @task(5)
    def health_check(self) -> None:
        # Explicitly unsets Authorization header for health check
        self.client.get(
            "/health",
            headers={"Authorization": None},
            name="GET /health",
        )

    # @task(3)
    # def protected_route(self) -> None:
    #     self.client.get(
    #         "/api/v1/protected-route-test",
    #         name="GET /api/v1/protected-route-test",
    #     )

    @task(3)
    def list_chats(self) -> None:
        self.client.get("/api/v1/agent/chats", name="GET /api/v1/agent/chats")

    @task(2)
    def list_documents(self) -> None:
        self.client.get(
            "/api/v1/documents/?page=1&limit=10",
            name="GET /api/v1/documents/",
        )

    @task(1)
    def get_chat_messages(self) -> None:
        if not self.chat_id:
            self.list_chats()
            return
        self.client.get(
            f"/api/v1/agent/chats/{self.chat_id}/messages",
            name="GET /api/v1/agent/chats/{chat_id}/messages",
        )

    @task(1)
    def get_document(self) -> None:
        if not self.document_id:
            self.list_documents()
            return
        self.client.get(
            f"/api/v1/documents/{self.document_id}",
            name="GET /api/v1/documents/{document_id}",
        )

    @task(1)
    def agent_query(self) -> None:
        if not env_flag("LOCUST_ENABLE_AGENT_QUERY"):
            self.list_chats()
            return

        payload = {
            "query": os.getenv(
                "LOCUST_QUERY", "What are the main regulatory requirements?"
            ),
        }
        if self.chat_id:
            payload["chat_id"] = self.chat_id

        self.client.post(
            "/api/v1/agent/query",
            json=payload,
            name="POST /api/v1/agent/query",
        )