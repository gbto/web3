import os

import pandas as pd
from neo4j import GraphDatabase
from ricochet_collection import RicochetCollection


class RicochetModelling:
    def __init__(self):

        self.txs_model = self.TransactionBasedModel()
        self.add_model = self.AccountBasedModel()

    class TransactionBasedModel:
        def __init__(self):

            __neo_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
            __neo_usr = os.environ.get("NEO4J_USR", "neo4j")
            __neo_pwd = os.environ.get("NEO4J_PWD", "ledger")

            self.driver = self.__instantiate_driver(__neo_uri, __neo_usr, __neo_pwd)
            self.session = self.driver.session()

        def __instantiate_driver(self, uri: str, usr: str, pwd: str):
            """Instantiate the Neo4j driver used for interacting with the DBMS."""
            try:
                return GraphDatabase.driver(uri, auth=(usr, pwd))
            except OSError:
                raise ConnectionError(f"Could not connect to the neo4j bolt server at {uri}")

        def create_blocks(self, logs: pd.DataFrame):
            """Create the chain of blocks."""

            self.session.run("CREATE CONSTRAINT ON (b:Block) ASSERT b.blockNumber IS UNIQUE")
            previous_block = None

            for index, row in logs.sort_values("blockNumber", ascending=True).iterrows():
                lines = list()
                if previous_block:
                    lines.append(f"MATCH (previous_block:Block) WHERE previous_block.height={previous_block}")
                    lines.append("WITH previous_block")
                    lines.append("MERGE (previous_block)-[:NEXT]->(b:Block)")
                else:
                    lines.append("MERGE (b:Block)")

                lines.append(f"SET b.height={row['blockNumber']}")
                lines.append(f"SET b.timestamp='{row['timeStamp'].strftime('%Y/%m/%d-%H:%M:%S')}'")

                statement = "\n".join(lines)
                self.session.run(statement)

                previous_block = row["blockNumber"]

            return

        def create_addresses(self, logs: pd.DataFrame):
            """Create all nodes in the contracts logs dataset.

            We'll create both smart contracts accounts and wallet accounts.
            """

            self.session.run("CREATE CONSTRAINT ON (node:Account) ASSERT node.address IS UNIQUE")

            # Create contract nodes
            for address in logs["to_"].unique():
                statement = "MERGE (:Account:Contract {address: $address})"
                self.session.run(statement, dict(address=address))

            # Create wallet nodes
            for address in logs["from_"].unique():
                statement = "MERGE (:Account:Wallet {address: $address})"
                self.session.run(statement, dict(address=address))

            return

        def create_transactions(self, logs: pd.DataFrame):
            """Create all nodes in the contracts logs dataset.

            We'll create both smart contracts accounts and wallet accounts.
            """

            self.session.run("CREATE CONSTRAINT ON (tx:Transaction) ASSERT tx.hash IS UNIQUE")

            for index, row in logs.sort_values("blockNumber", ascending=True).iterrows():
                lines = list()

                # Create transactions nodes
                lines.append("CREATE (tx:Transaction)")
                lines.append(f"SET tx.hash='{row['hash']}'")
                lines.append(f"SET tx.nonce='{row['nonce']}'")
                lines.append(f"SET tx.index='{row['transactionIndex']}'")
                lines.append(f"SET tx.value='{row['value']}'")
                lines.append(f"SET tx.gas='{row['gas']}'")
                lines.append(f"SET tx.gasPrice='{row['gasPrice']}'")
                lines.append(f"SET tx.cumulativeGasUsed='{row['cumulativeGasUsed']}'")
                lines.append(f"SET tx.gasUsed='{row['gasUsed']}'")
                lines.append("WITH tx")

                # link to blocks
                lines.append(f"MATCH (b:Block) WHERE b.height={row['blockNumber']}")
                lines.append("WITH b, tx")
                lines.append("MERGE (b) - [:CONTAINS] -> (tx)")
                lines.append("WITH tx")

                # link from addresses
                lines.append(f"MATCH (from:Account) WHERE from.address='{row['from_']}'")
                lines.append("WITH from, tx")
                lines.append("MERGE (from) <- [:FROM] - (tx)")
                lines.append("WITH tx")

                # link to addresses
                lines.append(f"MATCH (to:Account) WHERE to.address='{row['to_']}'")
                lines.append("WITH to, tx")
                lines.append("MERGE (tx) - [:TO] -> (to)")

                # execute the cypher statement
                statement = "\n".join(lines)
                self.session.run(statement)

            return

        def create_relationships(self, logs: pd.DataFrame):

            for index, row in logs.sort_values("blockNumber", ascending=True).iterrows():

                lines = list()

                lines.append("MATCH (from: Wallet), (to: Contract)")
                lines.append(f"WHERE from.address = '{row['from_']}' AND to.address = '{row['to_']}'")
                lines.append(f"CREATE(from) - [r:{row['function_called']}] -> (to)")

                # execute the cypher statement
                statement = "\n".join(lines)
                result = self.session.run(statement)

            return result

        def create_graph_model(self, logs: pd.DataFrame):
            """Create the entire model of the logs ingested from web3."""

            self.reset_database()
            self.create_blocks(logs)
            self.create_addresses(logs)
            self.create_transactions(logs)
            self.create_relationships(logs)

        def reset_database(self, database: str = "neo4j"):

            reset_statement = f"CREATE OR REPLACE DATABASE {database}"
            result = self.session.run(reset_statement)
            return result

    class AccountBasedModel:
        def __init__(self):
            __neo_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
            __neo_usr = os.environ.get("NEO4J_USR", "neo4j")
            __neo_pwd = os.environ.get("NEO4J_PWD", "ledger")

            self.driver = self.__instantiate_driver(__neo_uri, __neo_usr, __neo_pwd)
            self.session = self.driver.session()

        def __instantiate_driver(self, uri: str, usr: str, pwd: str):
            """Instantiate the Neo4j driver used for interacting with the DBMS."""
            try:
                return GraphDatabase.driver(uri, auth=(usr, pwd))
            except OSError:
                raise ConnectionError(f"Could not connect to the neo4j bolt server at {uri}")

        def create_user_nodes(self, logs: pd.DataFrame):

            self.session.run("CREATE CONSTRAINT ON (node:User) ASSERT node.address IS UNIQUE")

            # Create contract nodes
            for address in logs["from_"].unique():
                statement = "MERGE (:User {address: $address})"
                self.session.run(statement, dict(address=address))

            return

        def create_contract_nodes(self, logs: pd.DataFrame):

            self.session.run("CREATE CONSTRAINT ON (node:Contract) ASSERT node.address IS UNIQUE")

            # Create contract nodes
            for address in logs["to_"].unique():
                statement = "MERGE (:Contract {address: $address})"
                self.session.run(statement, dict(address=address))

            return

        def create_relationships(self, logs: pd.DataFrame):

            for index, row in logs.sort_values("blockNumber", ascending=True).iterrows():

                lines = list()

                lines.append("MATCH (from: User), (to: Contract)")
                lines.append(f"WHERE from.address = '{row['from_']}' AND to.address = '{row['to_']}'")
                lines.append(f"CREATE(from) - [r:{row['function_called']}] -> (to)")

                # execute the cypher statement
                statement = "\n".join(lines)
                result = self.session.run(statement)

            return result

        def create_graph_model(self, logs: pd.DataFrame):
            """Create the full graph model."""

            self.reset_database()
            self.create_contract_nodes(logs)
            self.create_user_nodes(logs)
            self.create_relationships(logs)

            return

        def reset_database(self, database: str = "neo4j"):

            reset_statement = f"CREATE OR REPLACE DATABASE {database}"
            result = self.session.run(reset_statement)
            return result


if __name__ == "__main__":

    collection = RicochetCollection()
    modelling = RicochetModelling()
