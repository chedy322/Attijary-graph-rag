import os
from neo4j import GraphDatabase, Driver
import logging

logger = logging.getLogger(__name__)


class Neo4jClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Neo4jClient, cls).__new__(cls, *args, **kwargs)
            cls._instance._driver = None
        return cls._instance

    def get_driver(self) -> Driver:
        if self._driver is None:
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            if self._driver is not None:
                logger.info(f"Connected to Neo4j at {uri} as user {user}.")
        return self._driver

    def close(self):
        if self._driver is not None:
            self._driver.close()
            self._driver = None


neo4j_client = Neo4jClient()
