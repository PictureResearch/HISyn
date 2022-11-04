import HISyn.tools.Log as log
import HISyn.back_end.back_end_function_kit as fc

other_query_list = ['fare', 'time', 'airline', 'type', 'cost']
question_word = ['what', 'which']


# domain specific knowledge for flight domain
def parsing_rules(nlp, gg):
    log.log('Set special knowledge for flight domain...')
    for dep in nlp.dependency:
        if (dep.dep in ['det'] and nlp.token[dep.target].lemma in question_word and nlp.token[
                dep.source].lemma in other_query_list):
            log.lprint('---')
            dep.dep = 'query'
            tmp = nlp.token[dep.target]
            nlp.token[dep.target] = nlp.token[dep.source]
            nlp.token[dep.source] = tmp

        elif (dep.dep in ['nsubj'] and nlp.token[dep.source].lemma in ['what'] and nlp.token[
            dep.target].lemma in other_query_list):
            dep.dep = 'query'

        elif dep.dep == 'nummod':
            if nlp.token[dep.source].lemma in ['am', 'pm']:
                nlp.token[dep.source].word = nlp.token[dep.target].word + nlp.token[dep.source].lemma
                dep.dep = 'case'
            elif nlp.token[dep.source].lemma == 'noon' and nlp.token[dep.target].lemma == '12':
                nlp.token[dep.source].word = '12'
                dep.dep = 'case'
    log.log('Special knowledge for flight domain finished')


def special_mapping_rules(nlp):
    for dep in nlp.dependency:
        if (dep.dep == 'dobj' and nlp.token[dep.target].word in other_query_list) or \
                (dep.dep == 'nmod:in' and nlp.token[dep.source].word in ['interested'] and nlp.token[
                    dep.target].word in other_query_list) or \
                (dep.dep == 'query' and nlp.token[dep.source].word.lower() in question_word and nlp.token[
                    dep.target].lemma in other_query_list):
            if not nlp.token[dep.source].mapping:
                nlp.token[dep.source].mapping = ['PROJECT', 'ColSet']
                dep.prep_mapping = ['AtomicColSet']
                remove_list = []
                for api in nlp.token[dep.target].mapping:
                    if 'COL' not in api:
                        remove_list.append(api)
                for r in remove_list:
                    nlp.token[dep.target].mapping.remove(r)

        elif (dep.dep == 'nmod:in' and nlp.token[dep.source].lemma in ['live'] and nlp.token[dep.target].mapping in [
            ['CITY']] or \
              dep.dep == 'nmod:on' and nlp.token[dep.source].lemma in ['information'] and nlp.token[
                  dep.target].mapping in [['CITY']]):
            dep.prep_mapping = ['EQ_DEPARTS']

        elif (dep.dep == 'nmod:for' and nlp.token[dep.source].lemma in ['leave'] and nlp.token[dep.target].mapping in [
            ['CITY']]):
            dep.prep_mapping = ['EQ_ARRIVES']


def special_cases_treatment(nlp, gg, text_index):
    pass


def lock_project(nlp, gg):
    for dep in nlp.dependency:
        if dep.dep == 'dobj' and 'PROJECT' in nlp.token[dep.source].mapping:
            log.lprint(dep.paths)
            min_len = 10000
            min_paths = []
            for p in dep.paths:
                length = fc.count_api_in_path(p, gg)
                if length < min_len:
                    min_len = length
                    min_paths.clear()
                    min_paths.append(p)
                elif length == min_len:
                    min_paths.append(p)
            dep.paths = min_paths
            log.lprint(dep.paths)
