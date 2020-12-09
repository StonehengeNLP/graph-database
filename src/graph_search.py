import re
from fuzzywuzzy import fuzz
from neomodel import Q
from .graph_database import GraphDatabase

gdb = GraphDatabase()

def text_autocomplete(text, n=10):
    """suggest top 10 similar keywords based on the given text"""
    base_entity = gdb.get_entity_model('BaseEntity')
    nodes = base_entity.nodes.filter(name__istartswith=text.lower())
    suggested_list = list({node.name.lower() for node in nodes[:100]})
    return sorted(suggested_list, key=len)[:n]

def text_correction(text, limit=1000, length_vary=0.2):
    """correct the text to be matched to a node"""
    text = text.lower()
    len_min, len_max = int(max(0, len(text) * (1-length_vary))), int(len(text) * (1+length_vary))
    base_entity = gdb.get_entity_model('BaseEntity')
    # filtered by the first or second character
    # and the length is +- length_vary * length? 
    nodes = base_entity.nodes.filter(
        (Q(name__istartswith=text[0]) | Q(name__regex=rf'^.{text[1]}.*')) 
        & Q(name__regex=rf'^.{{{len_min},{len_max}}}$'))
    suggested_list = list({node.name.lower() for node in nodes[:limit]})
    score = lambda x: fuzz.ratio(text, x.lower())
    if suggested_list:
        best = max(suggested_list, key=score)
        # cut-off threshold 
        best_score = score(best)
        if best_score > 60:
            return best, best_score
    return None, 0

def _generate_ngrams(s, n):
    s = s.lower()
    tokens = [token for token in s.split(" ") if token != ""]
    # Use the zip function Kto help us generate n-grams
    # Concatentate the tokens into ngrams and return
    ngrams = zip(*[tokens[i:] for i in range(n)])
    return [" ".join(ngram) for ngram in ngrams]

def text_preprocessing(search_text, threshold=90):
    # correct and filter n-gram keywords by similarity threshold
    n = len(search_text.split())
    new_keywords = []
    while n:
        keywords = _generate_ngrams(search_text, n=n)
        for keyword in keywords:
            new_word, score = text_correction(keyword, length_vary=0.1)
            if score >= threshold:
                new_keywords += [new_word]
        n -= 1
    
    res = gdb.search(new_keywords)
    
    # for score, node in res[:3]:
    #     paper = gdb.get_entity('Paper', name=node['name'])
    #     name = paper.name
    #     abstract = paper.abstract
    #     for key in new_keywords:
    #         name = re.sub(f'(?i){key}', f'**{key}**', name)
    #         abstract = re.sub(key, f'**{key}**', abstract)
    #     print(name)
    #     print(abstract)
    #     print('*'*100)
    return res