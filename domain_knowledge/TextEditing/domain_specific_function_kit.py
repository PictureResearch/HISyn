import HISyn.tools.Log as log


def parsing_rules(nlp, gg):
    log.log('Set special knowledge for text domain...')
    for dep in nlp.dependency:
        if nlp.token[dep.target].lemma in ['line'] \
                and dep.dep in ['dobj']:
            return
    for dep in nlp.dependency:
        if nlp.token[dep.source].lemma in ['line'] \
                and dep.dep in ['det', 'det:predet'] and nlp.token[dep.target].lemma in ['each', 'every', 'all']:
            nlp.token[dep.source].mapping = ['LINESCOPE', 'LINETOKEN']
            pass
        # elif nlp.token[dep.target].lemma in ['and', 'or']:
        #     dep.dep = 'rel'


# spcial mapping rules for domains
def special_mapping_rules(nlp):
    for dep in nlp.dependency:
        if dep.dep == 'dobj' and nlp.token[dep.source].word.lower() in ['replace', 'remove', 'print']:
            dep.prep_mapping = ['SelectString']
        elif (nlp.token[dep.target].lemma in ['beginning', 'start', 'begin']
              or nlp.token[dep.source].lemma in ['beginning', 'start', 'begin']):
            if 'nmod' in dep.dep and 'with' not in dep.dep:
                if 'STARTSWITH' in nlp.token[dep.target].mapping:
                    nlp.token[dep.target].mapping.remove('STARTSWITH')
                elif 'STARTSWITH' in nlp.token[dep.source].mapping:
                    nlp.token[dep.source].mapping.remove('STARTSWITH')
            elif 'nmod:with' in dep.dep:
                if 'STARTSWITH' in nlp.token[dep.target].mapping:
                    nlp.token[dep.target].mapping = (['STARTSWITH'])
                elif 'STARTSWITH' in nlp.token[dep.source].mapping:
                    nlp.token[dep.source].mapping = (['STARTSWITH'])


def check_seq_case(nlp):
    count = 0
    index = []
    for t in nlp.token:
        log.test('check_seq_case: ', t.word, t.mapping)
        if t.mapping in [['REMOVE'], ['INSERT'], ['PRINT'], ['REPLACE']]:
            log.test('mapping in')
            count += 1
            index.append(nlp.token.index(t))

    if count > 1:
        return [True, index]
    return [False, None]


def in_list(a, b):
    for x in a:
        if x in b:
            return True
    return False


# return [is_compond, index, is_target]
def check_string_compond(nlp):
    for dep in nlp.dependency:
        if dep.dep == 'compound':
            if nlp.token[dep.source].mapping in [['STRING']]:
                if in_list(nlp.token[dep.target].mapping, ['TEXTTOKEN', 'CHARTOKEN']):
                    return [True, nlp.dependency.index(dep), False]
            elif nlp.token[dep.target].mapping in [['STRING']]:
                if in_list(nlp.token[dep.source].mapping, ['TEXTTOKEN', 'CHARTOKEN']):
                    return [True, nlp.dependency.index(dep), True]
    return [False, None, None]


def find_source_index(nlp, index):
    source = nlp.dependency[index].source
    for dep in nlp.dependency:
        if dep.target == source:
            return nlp.dependency.index(dep)


# special treatment for some cases
def special_cases_treatment(nlp, gg, text_index):
    # if text_index == 447:
    #     remove_list = []
    #     for d in nlp.dependency:
    #         if d.dep == 'nsubj' or 'relcl' in d.dep:
    #             remove_list.append(d)
    #     for r in remove_list:
    #         nlp.dependency.remove(r)

    [is_seq, index] = check_seq_case(nlp)
    if is_seq:
        log.test('is_seq, add SEQ api')
        for dep in nlp.dependency:
            if dep.target in index:
                dep.prep_mapping = ['SEQ']

    [is_compond, index, is_target] = check_string_compond(nlp)
    if is_compond:
        if not is_target:
            nlp.dependency.remove(nlp.dependency[index])
        else:
            new_dep_index = find_source_index(nlp, index)
            nlp.dependency[new_dep_index].target = nlp.dependency[index].target
            nlp.dependency.remove(nlp.dependency[index])

    return

# special rules for Append
# def text_query_set(nlp):
#     log.log('Set special knowledge for append...')
#     for dep in nlp.depdency:
#         if (nlp.token[dep.source])
