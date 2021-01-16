import json
import tqdm
import pickle
from datetime import datetime
from src.graph_database import GraphDatabase

with open('data/pickle/data_5000_cleaned.pickle', 'rb') as f:
    data = pickle.load(f)
    
with open('data/data_5000_mag.json') as f:
    meta = json.load(f)
    meta = {d['Id']:d for d in meta}

graph_database = GraphDatabase()
graph_database.clear_all()

for i, doc in tqdm.tqdm(enumerate(data)):
    entities = doc['entities']
    relations = doc['relations']
    mag_id = doc['id']
    
    # metadata adding section
    # creation_date = datetime.strptime(meta[mag_id]['D'], '%Y-%m-%d')
    paper_entity = graph_database.add_entity('Paper', 
                                             meta[mag_id]['DN'].lower(),
                                             paper_id=i,
                                             mag_id=mag_id,
                                            #  created=creation_date,
                                            #  abstract=meta[mag_id]['ABS'].lower(),
                                            #  cc=meta[mag_id]['CC']
                                             )
    for author in meta[mag_id]['AA']:
        author_entity = graph_database.add_entity('Author', author['DAuN'].lower())
        graph_database.add_relation('Author-of', author_entity, paper_entity)
        if 'AfN' in author:
            affiliation_entity = graph_database.add_entity('Affiliation', author['AfN'].lower())
            graph_database.add_relation('Affiliate-with', author_entity, affiliation_entity)
    
    # information adding section
    entity_cache = []
    for entity_type, entity_name, confidence, *args in entities:
        entity = graph_database.add_entity(entity_type, entity_name.lower(), confidence)
        graph_database.add_relation('Appear-in', entity, paper_entity, confidence)
        entity_cache += [entity]
    for relation_type, head, tail, confidence, *args in relations:
        graph_database.add_relation(relation_type, 
                                    entity_cache[head], 
                                    entity_cache[tail],
                                    confidence,
                                    from_paper=i)

# add citation relation at the end
for mag_id in tqdm.tqdm(meta):
    if graph_database.is_entity_exist('Paper', mag_id=mag_id):
        paper = graph_database.get_entity('Paper', mag_id=mag_id)
        if 'RId' not in meta[mag_id]:
            pass
            # print(id)
        else:
            for rid in meta[mag_id]['RId']:       
                if graph_database.is_entity_exist('Paper', mag_id=rid):
                    r_paper = graph_database.get_entity('Paper', mag_id=rid)
                    graph_database.add_relation('cite', paper, r_paper)