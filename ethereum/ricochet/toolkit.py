import logging
import os

from neo4j import GraphDatabase

logger = logging.getLogger()


class ToolKit():

    def __init__(self):

        neo_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
        neo_usr = os.environ.get('NEO4J_USR', 'neo4j')
        neo_pwd = os.environ.get('NEO4J_PWD', 'ledger')

        self.driver = self.instantiate_driver(neo_uri, neo_usr, neo_pwd)
        self.session = self.driver.session()

    def instantiate_driver(self, uri: str, usr: str, pwd: str):
        """Instantiates the Neo4j driver used for interacting with the DBMS."""
        try:
            return GraphDatabase.driver(uri, auth=(usr, pwd))
        except OSError:
            raise ConnectionError('Could not connect to the neo4j bolt server at {}'.format(uri))

    def execute_statement(self, cypher_statement: str, params: dict = dict()):
        """Executes a Cyper statement in the DBMS. This statement has to be valide in Neo browser,
        i.e. 'CREATE CONSTRAINT ON (node:Address) ASSERT node.address IS UNIQUE'.
        """
        with self.driver.session() as session:
            resp = session.run(cypher_statement, params)
            data = resp.data()
        return data

    def reset_database(self, database: str = 'neo4j'):
        """Removes all the nodes from the database. """
        reset_statement = f"CREATE OR REPLACE DATABASE {database}"
        result = self.execute_statement(reset_statement)
        return result

    def show_databases(self):
        """List of the databases in the Neo4j DBMS."""
        show_dbs_statement = "SHOW DATABASES"
        result = self.execute_statement(show_dbs_statement)
        return result


if __name__ == '__main__':

    neo = ToolKit()
