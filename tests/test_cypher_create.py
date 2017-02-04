"""Cypher Create tests"""
import pytest

from neoalchemy import Create, Match, Node, Property, Relationship
from neoalchemy.exceptions import DetachedObjectError


def test_create_node_no_props():
    user = Node('User')
    create = Create(user)
    assert str(create) == 'CREATE (node:`User`)'
    assert not create.params


def test_create_node_one_prop():
    expected_stmt = (
        'CREATE (node:`User`)\n'
        '    SET node.name = {node_name}'
    )
    user = Node('User', name=Property())
    create = Create(user)
    assert str(create) == expected_stmt
    assert len(create.params) == 1
    assert 'node_name' in create.params
    assert create.params['node_name'] is None
    user.name = 'Frank'
    create = Create(user)
    assert str(create) == expected_stmt
    assert len(create.params) == 1
    assert 'node_name' in create.params
    assert create.params['node_name'] == 'Frank'


def test_create_node_two_props():
    user = Node('User', name=Property(), age=Property(type=int))
    create = Create(user)
    assert len(create.params) == 2
    assert 'node_name' in create.params
    assert create.params['node_name'] is None
    assert 'node_age' in create.params
    assert create.params['node_age'] is None
    create.set(user['name'] == 'Frank')
    assert len(create.params) == 2
    assert 'node_name' in create.params
    assert create.params['node_name'] == 'Frank'
    assert 'node_age' in create.params
    assert create.params['node_age'] is None
    create.set(user['age'] == '29')
    assert len(create.params) == 2
    assert 'node_name' in create.params
    assert create.params['node_name'] == 'Frank'
    assert 'node_age' in create.params
    assert create.params['node_age'] == 29


def test_create_node_two_labels():
    expected_stmts = (
        'CREATE (node:`Person`:`User`)\n'
        '    SET node.name = {node_name}',
        'CREATE (node:`User`:`Person`)\n'
        '    SET node.name = {node_name}'
    )
    user = Node('User', 'Person', name=Property())
    create = Create(user)
    assert str(create) in expected_stmts


def test_create_relation_to_nowhere():
    rel = Relationship('KNOWS', Node('User'))
    with pytest.raises(DetachedObjectError):
        create = Create(rel)


def test_create_relationship():
    rel = Relationship('KNOWS', Node('User'), Node('User'))
    with pytest.raises(ValueError):
        create = Create(rel)
    rel.end_node.var = 'end_node'
    assert str(Create(rel)) == 'CREATE (node)-[rel:`KNOWS`]->(end_node)'


def test_create_undirected_relationship():
    rel = Relationship('KNOWS', Node('User', var='m'), Node('User', var='n'),
                       var='r', directed=False)
    assert str(Create(rel)) == 'CREATE (m)-[r:`KNOWS`]-(n)'


def test_full_relationship_create():
    expected_query = (
        'MATCH (m:`User`)\n'
        'MATCH (n:`User`)\n'
        'CREATE (m)-[rel:`KNOWS`]->(n)'
    )
    user_m = Node('User', name=Property(), var='m')
    user_n = user_m.copy(var='n')
    rel = Relationship('KNOWS', user_m, user_n)
    query = Match(user_m) & Match(user_n) & Create(rel)
    assert str(query) == expected_query
    assert len(query.params) == 0


def test_logical_cypher_expressions():
    person = Node('Person', name=Property(), var='n')
    match = Match(person).where(person['name']=='Alice')
    assert str(match) == 'MATCH (n:`Person`)\n    WHERE n.name = {n_name}'
    assert len(match.params) == 1
    assert 'n_name' in match.params
    assert match.params['n_name'] == 'Alice'
    match = Match(person).where(person['name']!='Alice')
    assert str(match) == 'MATCH (n:`Person`)\n    WHERE n.name <> {n_name}'
    assert len(match.params) == 1
    assert 'n_name' in match.params
    assert match.params['n_name'] == 'Alice'
    match = Match(person).where(person['name']>='Alice')
    assert str(match) == 'MATCH (n:`Person`)\n    WHERE n.name >= {n_name}'
    assert len(match.params) == 1
    assert 'n_name' in match.params
    assert match.params['n_name'] == 'Alice'
    match = Match(person).where(person['name']<='Alice')
    assert str(match) == 'MATCH (n:`Person`)\n    WHERE n.name <= {n_name}'
    assert len(match.params) == 1
    assert 'n_name' in match.params
    assert match.params['n_name'] == 'Alice'
    match = Match(person).where(person['name']<'Alice')
    assert str(match) == 'MATCH (n:`Person`)\n    WHERE n.name < {n_name}'
    assert len(match.params) == 1
    assert 'n_name' in match.params
    assert match.params['n_name'] == 'Alice'
    match = Match(person).where(person['name']>'Alice')
    assert str(match) == 'MATCH (n:`Person`)\n    WHERE n.name > {n_name}'
    assert len(match.params) == 1
    assert 'n_name' in match.params
    assert match.params['n_name'] == 'Alice'


@pytest.mark.skip(reason='Combining CypherExpressions not yet supported')
def test_complex_logical_cypher_expressions():
    Person = NodeType('Person', Property('name'), Property('hair_color'))
    expected_match = ('MATCH (n:Person) WHERE n.name = {name_n} '
                      'AND n.hair_color = {hair_color_n}')

    match = (Match(Person)
                .where(Person.name=='Alice')
                .where(Person.hair_color=='red'))
    assert str(match) == expected_match
    assert match.params == {'name_n': 'Alice', 'hair_color_n': 'red'}

    match = (Match(Person)
                .where((Person.name=='Alice') & (Person.hair_color=='red')))
    assert str(match) == expected_match
    assert match.params == {'name_n': 'Alice', 'hair_color_n': 'red'}

    Person = NodeType('Person', Property('name'), Property('hair_color'),
                      Property('age', type=int))
    expected_match += ' AND n.age = {age_n}'
    match = (Match(Person)
                .where((Person.name=='Alice') &
                       (Person.hair_color=='red') &
                       (Person.age=='29')))
    assert str(match) == expected_match
    assert match.params == {'name_n': 'Alice', 'hair_color_n': 'red',
                            'age_n': 29}

    match = (Match(Person)
                .where(Person.name=='Alice')
                .where(Person.hair_color=='red')
                .where(Person.age==29))
    assert str(match) == expected_match
    assert match.params == {'name_n': 'Alice', 'hair_color_n': 'red',
                            'age_n': 29}

    expected_match = 'OR'.join(expected_match.rsplit('AND', 1))
    match = (Match(Person)
                .where((Person.name=='Alice') &
                       (Person.hair_color=='red') |
                       (Person.age==29)))
    assert str(match) == expected_match
    assert match.params == {'name_n': 'Alice', 'hair_color_n': 'red',
                            'age_n': 29}

    match = (Match(Person)
                .where(Person.name=='Alice')
                .where(Person.hair_color=='red')
                .where(Person.age==29, or_=True))
    assert str(match) == expected_match
    assert match.params == {'name_n': 'Alice', 'hair_color_n': 'red',
                            'age_n': 29}


@pytest.mark.skip(reason='Combining CypherExpressions not yet supported')
def test_arithmetic_cypher_expressions():
    Person = NodeType('Person', Property('age', type=int))

    match = Match(Person).where((Person.age + 5) == 23)
    assert str(match) == 'MATCH (n:Person) WHERE n.age + {param0} = {param1}'
    assert match.params['param0'] == 5
    assert match.params['param1'] == 23
    match = Match(Person).where((5 + Person.age) == 23)
    assert str(match) == 'MATCH (n:Person) WHERE n.age + {param0} = {param1}'
    assert match.params['param0'] == 5
    assert match.params['param1'] == 23

    match = Match(Person).where((Person.age - 4) == 13)
    assert str(match) == 'MATCH (n:Person) WHERE n.age - {param0} = {param1}'
    assert match.params['param0'] == 4
    assert match.params['param1'] == 13
    match = Match(Person).where((4 - Person.age) == 13)
    assert str(match) == 'MATCH (n:Person) WHERE {param0} - n.age = {param1}'
    assert match.params['param0'] == 4
    assert match.params['param1'] == 13

    match = Match(Person).where((Person.age * 5) == 23)
    assert str(match) == 'MATCH (n:Person) WHERE n.age * {param0} = {param1}'
    assert match.params['param0'] == 5
    assert match.params['param1'] == 23
    match = Match(Person).where((5 * Person.age) == 23)
    assert str(match) == 'MATCH (n:Person) WHERE n.age * {param0} = {param1}'
    assert match.params['param0'] == 5
    assert match.params['param1'] == 23

    match = Match(Person).where((Person.age / 4) == 13)
    assert str(match) == 'MATCH (n:Person) WHERE n.age / {param0} = {param1}'
    assert match.params['param0'] == 4
    assert match.params['param1'] == 13
    match = Match(Person).where((4 / Person.age) == 13)
    assert str(match) == 'MATCH (n:Person) WHERE {param0} / n.age = {param1}'
    assert match.params['param0'] == 4
    assert match.params['param1'] == 13

    match = Match(Person).where((Person.age % 4) == 13)
    assert str(match) == 'MATCH (n:Person) WHERE n.age % {param0} = {param1}'
    assert match.params['param0'] == 4
    assert match.params['param1'] == 13
    match = Match(Person).where((4 % Person.age) == 13)
    assert str(match) == 'MATCH (n:Person) WHERE {param0} % n.age = {param1}'
    assert match.params['param0'] == 4
    assert match.params['param1'] == 13

    match = Match(Person).where((Person.age ** 4) == 13)
    assert str(match) == 'MATCH (n:Person) WHERE n.age ^ {param0} = {param1}'
    assert match.params['param0'] == 4
    assert match.params['param1'] == 13
    match = Match(Person).where((4 ** Person.age) == 13)
    assert str(match) == 'MATCH (n:Person) WHERE {param0} ^ n.age = {param1}'
    assert match.params['param0'] == 4
    assert match.params['param1'] == 13