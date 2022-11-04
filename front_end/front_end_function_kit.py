import HISyn.tools.Log as log
import HISyn.front_end.NLP as NLP

import os
from HISyn.tools.root_directory import root_dir
os.environ['CORENLP_HOME'] = root_dir + '/third_party_pkgs/stanford-corenlp-full-2018-10-05'

# read text from file
def read_text(file_name, index):
    log.log('Reading text from test cases, case index: ' + str(index) + '...')
    text_t = open(file_name, 'r', encoding='utf-8').readlines()
    text = text_t[index].capitalize()
    log.log('query: ', text)
    return text


# call NLP to processing text, the return is parsing results
def nlp_parsing(text, domain, nlp_server=False):
    log.log('Parsing text...')
    nlp = NLP.NLParsing(nlp_server=nlp_server)
    nlp.parsing(text, domain)
    log.log('Parsing finished')
    return nlp


# add domain-specific rules
## check if rules exist
def domain_specfic_parsing_rules(domain, nlp, gg):
    log.log('apply domain_specific_parsing_rules...')
    ds_func_path = root_dir + '/domain_knowledge/'+ domain + '/domain_specific_function_kit.py'
    if os.path.exists(ds_func_path):
        import importlib
        ds_func_kit = importlib.import_module('HISyn.domain_knowledge.' + domain +'.domain_specific_function_kit')
        ds_func_kit.parsing_rules(nlp, gg)
        log.log('domain specific rules applied.')
    else:
        log.log('no domain specific rules.')


# prune edges based on dependency relations, pos tags
def prune_edges(nlp, prunable_dep_tags, prunable_pos_tags, common_knowledge_tags):
    log.log('Pruning unimportant edges...')
    dep_remove_list = []
    for d in nlp.dependency:
        if d.dep in prunable_dep_tags \
                or (nlp.token[d.target].pos in prunable_pos_tags and (nlp.token[d.target].ner not in common_knowledge_tags and not d.dep == 'neg')) \
                or nlp.token[d.target].ner == 'REMOVE':
            log.test("remove dep: " + d.dep)
            log.test("target token: " + nlp.token[d.target].word)
            dep_remove_list.append(d)

        # SPECIAL RULES, PRUNE TIME(EARLY)
        elif nlp.token[d.target].lemma == 'early' and nlp.token[d.target].ner == 'TIME':
            dep_remove_list.append(d)

    for i in dep_remove_list:
        nlp.dependency.remove(i)
    log.log('Pruning unimportant edges...')