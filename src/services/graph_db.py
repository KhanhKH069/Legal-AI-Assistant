from neo4j import GraphDatabase
import os
import logging
logger = logging.getLogger(__name__)

class GraphDBService:

    def __init__(self, uri=None, user=None, password=None):
        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.user = user or os.getenv('NEO4J_USER', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'password')
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            logger.info('Connected to Neo4j Graph Database.')
        except Exception as e:
            logger.error(f'Failed to connect to Neo4j: {e}')
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def query(self, query: str, parameters=None):
        if not self.driver:
            return []
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f'Neo4j query error: {e}')
            return []
_graph_db = None

def get_graph_db() -> GraphDBService:
    global _graph_db
    if _graph_db is None:
        _graph_db = GraphDBService()
    return _graph_db