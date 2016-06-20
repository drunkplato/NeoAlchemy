"""
A thin wrapper around the Neo4J Bolt driver's GraphDatabase class
providing a convenient auto-connection during initialization.
"""
import warnings

from neo4j.v1 import GraphDatabase, basic_auth


class Query(object):
    """Run queries on the Graph"""
    def __init__(self, graph):
        self.graph = graph

    def all(self):
        """MATCH (all) RETURN all"""
        return self.graph.driver.session().run('MATCH (all) RETURN all')

    def run(self, *args, **kw):
        """Run an arbitrary Cypher statement"""
        return self.graph.driver.session().run(*args, **kw)


class Graph(GraphDatabase):
    """
    A thin wrapper around the Neo4J Bolt driver's GraphDatabase class
    providing a convenient auto-connection during initialization.
    """
    def __init__(self, url='bolt://localhost', **kw):
        self.connect(url, **kw)
        self.query = Query(self)

    def connect(self, url, user='neo4j', password='neo4j'):
        """
        Parse a Neo4J URL and attempt to connect using Bolt

        Note: If the user and password arguments are provided, they
        will only be used in case no auth information is provided as
        part of the connection URL.
        """
        try:
            protocol, url = url.split('://')
            if protocol.lower() != 'bolt':
                warnings.warn('Switching protocols. Only Bolt is supported '
                              'at this time.')
        except ValueError:
            pass

        try:
            credentials, url = url.split('@')
        except ValueError:
            auth_token = basic_auth(user, password)
        else:
            auth_token = basic_auth(*credentials.split(':', 1))

        self.driver = GraphDatabase.driver('bolt://%s' % url, auth=auth_token)

    def delete_all(self):
        """MATCH (all) DETACH DELETE all"""
        self.driver.session().run('MATCH (all) DETACH DELETE all')