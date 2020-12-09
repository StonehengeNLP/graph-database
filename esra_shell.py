import cmd
from os import system
from src import graph_search as gs


INTRO = \
"""
                 _____ ____  ____      _     
                | ____/ ___||  _ \    / \    
                |  _| \___ \| |_) |  / _ \   
                | |___ ___) |  _ <  / ___ \  
                |_____|____/|_| \_\/_/   \_\ 
  ____                 _       ____                      _
 / ___|_ __ __ _ _ __ | |__   / ___|  ___  __ _ _ __ ___| |__
| |  _| '__/ _` | '_ \| '_ \  \___ \ / _ \/ _` | '__/ __| '_ \ 
| |_| | | | (_| | |_) | | | |  ___) |  __/ (_| | | | (__| | | |
 \____|_|  \__,_| .__/|_| |_| |____/ \___|\__,_|_|  \___|_| |_|
                |_|
"""

class EsraShell(cmd.Cmd):
    
    intro = INTRO + "\nWelcome to the ESRA's graph search command line.\n"
    prompt = '(esra) '
    
    def __init__(self):
        super().__init__()
        
    def emptyline(self):
         pass
        
    def do_clear(self, line):
        """Clear screen"""
        system('clear')
    
    def do_exit(self,*args):
        """Quit the program"""
        return True
        
    def do_search(self, line):
        """Search scientific papers by using keyword(s)"""
        line = line.replace('_', ' ')
        gs.text_preprocessing(line)
        # results = self.graph_database.search(line)
        # for i in results:
        #     print(*i, sep=' \t')
                        
    def complete_search(self, text, line, start_index, end_index):
        if text:
            text = text.replace('_', ' ')
            out = gs.text_autocomplete(text)
            if len(out) == 0:
                out = gs.text_correction(text)
            out = out[0].replace(' ', '_')
            return out
        return []
    
from src.graph_database import GraphDatabase
import re

if __name__ == '__main__':
    esra_shell = EsraShell()
    # esra_shell.cmdloop()

    search_text = 'bert'
    print('Search text:', search_text)
    keywords = gs.text_preprocessing(search_text)
    r = gs.search(keywords)
    for i in r:
        print(i)
    
    gdb = GraphDatabase()
    
    # for score, node in r[:3]:
    #     paper = gdb.get_entity('Paper', name=node['name'])
    #     name = paper.name
    #     abstract = paper.abstract
    #     for key in keywords:
    #         name = re.sub(f'(?i){key}', f'**{key}**', name)
    #         abstract = re.sub(f'(?i){key}', f'**{key}**', abstract)
    #     print(name)
    #     print(abstract)
    #     print('*'*100)

    gdb.find_path(['bert', 'attention'], 'MASS: Masked Sequence to Sequence Pre-training for Language Generation')