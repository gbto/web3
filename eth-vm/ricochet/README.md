
# Summary

This repo contains an experimentation of DeFi protocol storage in Graph Database Neo4j.
With traditional database, all transactions information is displayed in a tabular format hereby making it complex to understand connection between addresseses.

A graph database can store any kind of data using a few basic concepts:

- Nodes - represent entities of a domain.
- Labels - shape the domain by grouping nodes into sets.
- Relationships - connect two nodes.
- Properties - named values that add qualities to nodes and relationships.

For the purpose of this project, we will use Polygonscan and a Polygon node to extract the transactions and logs of the smart contracts we are interested in and will parse it to a tabular format to test the possibility and potential of moving data from RDBMS to a Graph DB.
The complexity will then mostly lie in the definition of the Graph DB model. More specifically, we can project a model that follows the general rules:

At the highest level:
- Nodes are blocks validated on the network
- Blocks can be labelled by te validator
- Relationships between blocks will always be "(b1: Block)[created] -> (b2: Block)"
- The properties of each block would be the timestamps, the amount staked, the rewards granted, the number of transactions it contains, the average monetary value of transactions, and many other aggregates

At another granularity, we can drill down to transactions:
- Each blocks contains transactions, that can be interpreted as nodes themselves
- Each transaction can be labelled with its function (transfers, deposit, withdrawal) which can be captured through transaction logs
- Transactions are made from an address to another, hence again a (a: Address) [t: Transfer] -> (b: Address)
- Finally transactions can have many properties, in the same fashion as blocks.

# The Neo4j technology


https://neo4j.com/graphacademy/training-querying-40/01-querying40-introduction-to-cypher/

Visualizing the relationships in the schema
CALL db.schema.visualization() to view the relationship types in the graph.

Relationships notations:

()          // a node
()--()      // 2 nodes have some type of relationship
()-[]-()    // 2 nodes have some type of relationship
()-->()     // the first node has a relationship to the second node
()<--()     // the second node has a relationship to the first node

Querying multiple relationships:
-[:ACTED_IN|DIRECTED]->


# The DeFi protocol: Ricochet

Ricochet is a smart contract managing fixed-rate collateral-backed lending on Ethereum. It provides decentralized exchange that supports automatic real-time investing on Polygon.
Ricochet Exchange contracts use Superfluid for streaming tokens and Tellor Oracle for getting prices, and SushiSwap/QuickSwap for liquidity.

## Contracts addresses

You'll find in the [queries of the Dune dashboards](https://dune.xyz/queries/299872/569279) as well as the [source code](https://github.com/Ricochet-Exchange/ricochet-analytics/blob/master/03-ric-endpoint/circulatingSupply.py) some of the addresses of ricochet smart contracts.

### Treasury address:
- 0x9C6B5FdC145912dfe6eE13A667aF3C5Eb07CbB89

### Exchanges addresses:
- 0x9BEf427fa1fF5269b824eeD9415F7622b81244f5
- 0x0A70Fbb45bc8c70fb94d8678b92686Bb69dEA3c3
- 0xe0A0ec8dee2f73943A6b731a2e11484916f45D44
- 0x71f649EB05AA48cF8d92328D1C486B7d9fDbfF6b
- 0x8082Ab2f4E220dAd92689F3682F3e7a42b206B42
- 0x3941e2E89f7047E0AC7B9CcE18fBe90927a32100
- 0xE093D8A4269CE5C91cD9389A0646bAdAB2c8D9A3
- 0x93D2d0812C9856141B080e9Ef6E97c7A7b342d7F
- 0xA152715dF800dB5926598917A6eF3702308bcB7e
- 0x250efbB94De68dD165bD6c98e804E08153Eb91c6
- 0xC89583Fa7B84d81FE54c1339ce3fEb10De8B4C96
- 0xdc19ed26aD3a544e729B72B50b518a231cBAD9Ab
- 0x47de4Fd666373Ca4A793e2E0e7F995Ea7D3c9A29
- 0x94e5b18309066dd1E5aE97628afC9d4d7EB58161
- 0xBe79a6fd39a8E8b0ff7E1af1Ea6E264699680584
- 0xeb367F6a0DDd531666D778BC096d212a235a6f78
- 0x0cb9cd99dbC614d9a0B31c9014185DfbBe392eb5
- 0x98d463A3F29F259E67176482eB15107F364c7E18

### Bank addresses:
- Bank v1.1: 0xe78dc447d404695541b540f2fbb7682fd24d778b
- Bank v1.0: 0xaD39F774A75C7673eE0c8Ca2A7b88454580D7F53
- Bank v0: 0x91093c77720e744F415D33551C2fC3FAf7333c8c

# Useful link

- [Ricochet Dune Analytics](https://github.com/Ricochet-Exchange/ricochet-analytics)
- [Ricochet smart contracts](https://github.com/Ricochet-Exchange/ricochet-protocol/tree/main/contracts)
- [Ricochet bank smart contracts](https://github.com/Ricochet-Exchange/rex-bank/tree/master/contracts)
