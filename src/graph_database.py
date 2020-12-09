from . import settings
from . import models
from . import validator
from typing import List
from neomodel import config, db, match


class GraphDatabase():

    CYPHER_DELETE_ALL = "MATCH (n) DETACH DELETE n"
    CYPHER_GRAPH_CHECK = "CALL gds.graph.exists('{graph_name}')"
    CYPHER_GRAPH_CREATE = \
        """ CALL gds.graph.create.cypher(
                '{graph_name}',
                'MATCH (n)-[e *0..2]-(m) \
                    WHERE m.name =~ "(?i)({key})" \
                    RETURN distinct(id(n)) AS id',
                'MATCH (n)-[e]-(m) \
                    RETURN id(n) AS source, e.weight AS weight, id(m) AS target',
                {{validateRelationships: false}}
            )
        """
    CYPHER_GRAPH_DELETE = "CALL gds.graph.drop('{graph_name}')"
    CYPHER_PAGE_RANK = \
        """ MATCH (n)
            WHERE n.name =~ "(?i)({key})"
            CALL gds.pageRank.stream('{graph_name}', {{
                maxIterations: 20,
                dampingFactor: 0.85,
                relationshipWeightProperty: 'weight',
                sourceNodes: [n]
            }})
            YIELD nodeId, score WITH gds.util.asNode(nodeId) as node, score
            WHERE node:Paper
            RETURN DISTINCT
                sum(score) AS score,
                node {{
                    .cc,
                    .name
                }}
            ORDER BY score DESC
        """
    CYPHER_CHECK_NODE_EXIST = "MATCH (n) WHERE n.name =~ '(?i){key}' RETURN count(n);"
                # gds.util.asNode(nodeId).created AS created
    
    def __init__(self):
        username = settings.NEO4J_USERNAME
        password = settings.NEO4J_PASSWORD
        host = settings.NEO4J_HOST
        port = settings.NEO4J_PORT
        config.DATABASE_URL = f'bolt://{username}:{password}@{host}:{port}'

    def clear_all(self):
        db.cypher_query(self.CYPHER_DELETE_ALL)

    def get_entity_model(self, entity_type):
        return models.__dict__[entity_type]
        
    def get_all_entities(self, entity_type:str) -> List[models.BaseEntity]:
        entity_model = self.get_entity_model(entity_type)
        return entity_model.nodes.all()
    
    def get_entity(self, entity_type, **kwargs):
        entity_model = self.get_entity_model(entity_type)
        target_entity = entity_model.nodes.get(**kwargs)
        return target_entity
    
    def is_entity_exist(self, entity_type, **kwargs):
        entity_model = self.get_entity_model(entity_type)
        target_entity = entity_model.nodes.first_or_none(**kwargs)
        if target_entity == None:
            return False
        return True
    
    def add_entity(self, entity_type, entity_name, confidence=1, **kwargs):
        if self.is_entity_exist(entity_type, name=entity_name):
            target_entity = self.get_entity(entity_type, name=entity_name)
            target_entity.count += 1
            _weight_diff = (confidence - target_entity.weight) / target_entity.count
            target_entity.weight += _weight_diff
        else:
            entity_model = self.get_entity_model(entity_type)
            target_entity = entity_model(name=entity_name)
            target_entity.weight = confidence
        target_entity.__dict__.update(kwargs)
        target_entity.save()
        return target_entity
    
    def get_relation(self, relation_type, head_entity):
        assert isinstance(head_entity, models.BaseEntity)
        relation_type = relation_type.lower().replace('-', '_')
        relation = head_entity.__dict__[relation_type]
        return relation
    
    def is_relation_exist(self, relation_type, head_entity, tail_entity):
        assert isinstance(head_entity, models.BaseEntity)
        assert isinstance(tail_entity, models.BaseEntity)
        
        relation_type = relation_type.lower().replace('-', '_')
        relation = self.get_relation(relation_type, head_entity)
        relationship = relation.relationship(tail_entity)
        if relationship == None:
            return False
        return True
        
    def add_relation(self, relation_type, head_entity, tail_entity, confidence=1, **kwargs):
        assert isinstance(head_entity, models.BaseEntity)
        assert isinstance(tail_entity, models.BaseEntity)
        
        relation_type = relation_type.lower().replace('-', '_')
        relation = self.get_relation(relation_type, head_entity)
        if self.is_relation_exist(relation_type, head_entity, tail_entity):
            relationship = relation.relationship(tail_entity)
            relationship.count += 1
            relationship.weight += confidence
        else:
            relationship = relation.connect(tail_entity)
            relationship.weight = confidence
        try:
            validator.validate_relation(relation_type, head_entity, tail_entity)
        except Exception as e:
            print(e)
            relationship.flag_violation = True
        relationship.__dict__.update(kwargs)
        relationship.save()
        return relationship
        
    def _is_node_exist(self, key):
        """ Check if node exist before searching """
        query = self.CYPHER_CHECK_NODE_EXIST.format(key=key)
        exist = (db.cypher_query(query)[0][0][0])
        return True if exist else False

    def _is_cypher_graph_exist(self, keys: list):
        graph_name = ''.join(keys)
        query = self.CYPHER_GRAPH_CHECK.format(graph_name=graph_name)
        is_exist = db.cypher_query(query)[0][0][1]
        return is_exist
    
    def _create_cypher_graph(self, keys: list):
        graph_name = ''.join(keys)
        key = '|'.join(keys)
        query = self.CYPHER_GRAPH_CREATE.format(graph_name=graph_name, key=key)
        db.cypher_query(query)
    
    def _delete_cypher_graph(self, keys: list):
        graph_name = ''.join(keys)
        query = self.CYPHER_GRAPH_DELETE.format(graph_name=graph_name)
        db.cypher_query(query)
    
    def _pagerank(self, keys: list):
        graph_name = ''.join(keys)
        key = '|'.join(keys)
        query = self.CYPHER_PAGE_RANK.format(graph_name=graph_name, key=key)
        results = db.cypher_query(query)[0]
        return results
    
    # TODO: prevent injection
    def search(self, keys: list, n=10):
        print('Search key:', keys)
        for key in keys:
            if not self._is_node_exist(key):
                return ["Entity does not exist"]
        if not self._is_cypher_graph_exist(keys):
            self._create_cypher_graph(keys)
        results = self._pagerank(keys)
        self._delete_cypher_graph(keys)
        print(len(results))
        return results[:n]