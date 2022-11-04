import HISyn.tools.Log as log
import HISyn.front_end.NLP as NLP
from HISyn.tools.root_directory import root_dir

import os
import re
import copy


############### funcitons for Semantic mapping ######################

# check if a word is part of common knowledge, if yes, mapping with API input
def common_knowledge_checking(gg, token, common_knowledge_tags):
    log.test('checking common knowledge: ', token.word)
    target = token
    if target.ner in common_knowledge_tags:
        api = mapping_input(gg, target.ner, common_knowledge_tags)
        target.mapping = list(api)
        # print(api)
        for i in range(len(api)):
            api[i] = api[i] + '(' + target.word + ')'
            log.test(api[i])
            log.test(api)
            # translated_arguments_api.append(api[i])
        target.word = api
        target.ner = "translated"


# mapping the input type with the name entity to map the API that take common knowledge as input
def mapping_input(gg, input_type, common_knowledge_tags):
    log.test('mapping input: ',  input_type)
    result = []
    for k in gg.api_dict.keys():
        log.test(common_knowledge_tags[input_type], gg.api_dict[k].input)
        if common_knowledge_tags[input_type] == gg.api_dict[k].input:
            result.append(k)
    return result


# domain specific mapping rules
def domain_specific_mapping_rules(domain, nlp):
    log.log('apply domain_specific mapping rules...')
    ds_func_path = root_dir + '/domain_knowledge/' + domain + '/domain_specific_function_kit.py'
    if os.path.exists(ds_func_path):
        import importlib
        ds_func_kit = importlib.import_module('HISyn.domain_knowledge.' + domain + '.domain_specific_function_kit')
        ds_func_kit.special_mapping_rules(nlp)
        log.log('domain specific rules applied.')
    else:
        log.log('no domain specific rules.')


# mapping the word with API descriptions
def mapping_word_in_description(gg, token):
    log.test('mapping word in name or description: ', token.word)
    result = []
    for k in gg.api_dict.keys():
        name = k
        desc = gg.api_dict[k].description.lower().replace(',',' ').replace('.', ' ').split(' ')
#         if (token.word.lower() in desc or token.word.lower() in name or token.lemma in name or token.lemma in desc):
#         print(token.word, desc, token.word.lower() in desc or token.lemma in desc)
        if token.word.lower() in desc or token.lemma in desc:
            result.append(k)
    log.test(result)
    return result


# mapping common knowledge inside sentence
def common_knowledge_mapping(gg, nlp, common_knowledge_tags):
    log.log('checking common knowledge')
    for d in nlp.dependency:
        common_knowledge_checking(gg, nlp.token[d.source], common_knowledge_tags)
        common_knowledge_checking(gg, nlp.token[d.target], common_knowledge_tags)
    log.log('common knowledge replace finished')


# regular mapping, map tokens with descriptions
def mapping_regular(gg, token):
    log.test('regular mapping: ', token.word)
    if len(token.mapping) == 0:
        token.mapping = mapping_word_in_description(gg, token)


# keywords based mapping
def mapping_keywords(gg, nlp):
    log.log('start keywords mapping')
    if not nlp.token[nlp.dependency[0].source].ner == 'translated':
        mapping_regular(gg, nlp.token[nlp.dependency[0].source])

    for d in nlp.dependency:
        if not nlp.token[d.source].mapping:
            mapping_regular(gg, nlp.token[d.source])
        if not nlp.token[d.target].ner == 'translated':
            mapping_regular(gg, nlp.token[d.target])
    log.log('keywords mapping finished')


# remove empty mapping edges, if target mapping is empty, remove this dep edge
def remove_empty_edge(nlp):
    if len(nlp.dependency) <= 1:
        return

    log.log('remove empty edges')
    remove_list = []
    target_dict = {}
    source_dict = {}
    for d in nlp.dependency:
        if not d.target in target_dict:
            target_dict[d.target] = [d]
        else:
            target_dict[d.target].append(d)

        if d.source in source_dict:
            source_dict[d.source].append(d)
        else:
            source_dict[d.source] = [d]
        if len(nlp.token[d.target].mapping) == 0:
            remove_list.append(d)

    for d in remove_list:
        if d.target in source_dict and len(nlp.token[d.source].mapping) > 0:
            for dep in source_dict[d.target]:
                if len(target_dict[dep.target]) > 1:
                    target_dict[dep.target].remove(dep)
                    continue
                dep.source = target_dict[d.target][0].source
                dep.dep = d.dep
        nlp.dependency.remove(d)

    log.log('empty edge removed.')


################### Longest Match ###################

# add a dependency edge to modifier group
def add_to_modifier_group(group, source, target):
    log.test('buiding modifeir group: ')
    log.test(target.word )
    is_source_in = False
    for g in group:
        if source in g:
            g.append(target)
            is_source_in = True
            break
    if not is_source_in:
        group.append([source, target])


# set modifier group
def set_modifier_group(nlp):
    log.log('start longest matching')
    log.test('set modifier group')
    for d in nlp.dependency:
        if d.dep in ['amod', 'nmod', 'nmod:of', 'compound', 'nummod']:
            add_to_modifier_group(nlp.modifier_group, nlp.token[d.source], nlp.token[d.target])

    log.test('modifier_group: ', nlp.modifier_group, [nn.word for n in nlp.modifier_group for nn in n])


# modifier group vote, choose the highest score
def modifier_group_vote(group):
    score = []
    score_nodes = []
    for a in group[0].mapping:
        s_node = []
        count = 0
        for t in group[1:]:
            if a in t.mapping:
                count += 1
                s_node.append(t)
        score.append(count)
        score_nodes.append(s_node)
    return [score, score_nodes]


# return highest score
def highest_score(score):
    max_score = max(score)
    max_index = []
    for i in range(len(score)):
        if score[i] == max_score:
            max_index.append(i)
    return [max_score, max_index]


# modifier_vote function
def modifier_vote(nlp):
    log.test('modifier vote ...')
    for g in nlp.modifier_group:
        [score, score_nodes] = modifier_group_vote(g)
        log.test('score:', score)
        log.test('score_nodes', score_nodes)

        if score:
            [max_score, max_index] = highest_score(score)

        if score:
            if max(score) > 0:
                # [max_score, max_index] = highest_score(score)
                g[0].mapping = [g[0].mapping[x] for x in max_index]
                for x in max_index:
                    if [score_nodes[x]] not in g[0].modifiers:
                        g[0].modifiers.append([score_nodes[x]])
                # g[0].modifiers = set(g[0].modifiers)
                log.test(g[0].mapping)
                log.test(g[0].modifiers)
            #             continue

            if len(g[0].mapping) == 1:
                log.test('g[0].ner', g[0].ner)
                g[0].final_mapping = g[0].mapping[0]
                if g[0].modifiers:
                    for tokens in g[0].modifiers[0]:
                        for t in tokens:
                            t.mapping = []
                            if t.ner == 'translated':
                                if not g[0].ner == 'translated':
                                    g[0].word = t.word
                                    g[0].ner = 'translated'

            elif len(g) == 2 and len(g[0].mapping) > 1 and max(score) > 0:
                log.test('has one modifier with more than one candidates')
                g[1].mapping = []

            elif max_score == len(g) - 1:
                log.test('all the modifiers contribute to match, remove modifiers')
                for i in range(1,len(g)):
                    g[i].mapping = []


    # remove empty edge after modifier vote
    remove_empty_edge(nlp)

################### Longest Match Ends ###################


################### Reordering ###################

# preposition mapping
def preposition_mapping(gg, prep):
    result = []
    for k in gg.api_dict.keys():
        name = re.findall('[A-Z][^A-Z]*', k)
        desc = gg.api_dict[k].description.replace(',', ' ').replace('.', ' ').split(' ')
        if (prep.lower() in desc or prep.lower() in name):
            result.append(k)
    return result


# mapping prepositions
def set_preposition(nlp, gg, preposition):
    log.log('set preposition mappings ...')
    for d in nlp.dependency:
        if d.dep[5:] in preposition and (not d.prep_mapping):
            log.test('preposition found: ', d.dep[5:])
            d.prep_mapping = preposition_mapping(gg, d.dep[5:])
        elif d.dep[6:] in preposition and (not d.prep_mapping):
            log.test('preposition found: ', d.dep[6:])
            d.prep_mapping = preposition_mapping(gg, d.dep[6:])


# reorder subject
def subj_reorder(nlp):
    log.log('subj reordering ...')

    dep_dict = {}
    for dep in nlp.dependency:
        dep_dict[dep.target] = dep

    for dep in nlp.dependency:
        # if dep.dep in ['nsubj', 'nsubjpass']:
        #     if 'V' in nlp.token[dep.source].pos:
        #         tmp = dep.source
        #         dep.source = dep.target
        #         dep.target = tmp

        # is_reorder = False

        if dep.dep in ['nsubj', 'nsubjpass']:
            log.test('dep in [nsubj], ', nlp.token[dep.source].word)
            for key in dep_dict.keys():
                log.test(nlp.token[key].word, nlp.token[dep_dict[key].source].word)

            if dep.source in dep_dict:
                if dep_dict[dep.source].dep not in ['nsubj', 'nsubjpass']:
                    dep_dict[dep.source].target = dep.target
                    dep_dict.pop(dep.source)
            tmp = dep.source
            dep.source = dep.target
            dep.target = tmp
            # is_reorder = True
        elif dep.dep in ['nmod:poss']:
            # log.test('dep in [nmod:poss], ', nlp.token[dep.source].word)
            # for key in dep_dict.keys():
            #     log.test(nlp.token[key].word, nlp.token[dep_dict[key].source].word)

            if dep.source in dep_dict:
                if dep_dict[dep.source].dep not in ['nsubj', 'nsubjpass']:
                    dep_dict[dep.source].target = dep.target
                    dep_dict.pop(dep.source)
            tmp = dep.source
            dep.source = dep.target
            dep.target = tmp


# add root node for dependency edges if the source has a mapping
def check_governor(nlp):
    log.log('checking no governor dependency source')
    dependent_dict = {} # target: source
    for d in nlp.dependency:
        if d.target not in dependent_dict:
            dependent_dict[d.target] = d.source
        elif d.dep == 'dobj':
            dependent_dict[d.target] = d.source
    log.test('dependent dict: ', dependent_dict)

    no_gov_source_dict = {}
    empty_mapping_source_edge_dict = {}
    for d in nlp.dependency:
        if not nlp.token[d.source].mapping:
            empty_mapping_source_edge_dict[d] = None
        elif d.source not in dependent_dict:
            no_gov_source_dict[d.source] = None
    log.test('no governor source dict: ', no_gov_source_dict)

    return [dependent_dict, no_gov_source_dict, empty_mapping_source_edge_dict]


# add root tokens to no governor sources
def add_root_node(nlp, dependent_dict, no_gov_source_dict, empty_mapping_source_edge_dict):
    log.log('add root token to no governor source')

    fake_root_token = NLP.RootToken()
    root_token = NLP.Token(fake_root_token)
    nlp.token.append(root_token)

    root_index = len(nlp.token) - 1

    tmp_dep_dict = {}
    for d in nlp.dependency:
        if d.target not in tmp_dep_dict:
            tmp_dep_dict[d.target] = [d]
        else:
            tmp_dep_dict[d.target].append(d)
    remove_list = []
    for k in empty_mapping_source_edge_dict.keys():
        if len(tmp_dep_dict[k.target]) > 1:
            remove_list.append(k)
        else:
            k.source = root_index

    for r in remove_list:
        nlp.dependency.remove(r)

    for k in no_gov_source_dict.keys():
        fake_root_edge = NLP.RootEdge(len(nlp.token), k + 1)
        root_edge = NLP.Dependency(fake_root_edge)
        nlp.dependency.append(root_edge)

    dependent_dict.clear()
    for d in nlp.dependency:
        dependent_dict[d.target] = d.source
    log.test('dependent_dict: ', [[nlp.token[k].word, nlp.token[dependent_dict[k]].word] for k in dependent_dict.keys()])
    return root_index


################### Reordering Match Ends ###################

################### Reversed all paths search ###################

# BFS from one API of target to all APIs of source
def single_start_BFS(startAPI, endAPISet, gg, path_limit = None, single_api_combine = True):
    log.log('singel start BFS...', startAPI, endAPISet, path_limit)
    # log.log("Start API: ", startAPI)
    # log.log("endAPIset: ", endAPISet)
    # log.log('path_limit: ', path_limit)

    if startAPI in endAPISet and single_api_combine:
        return [[startAPI]]

    endAPISet_copy = list(endAPISet)

    if len(endAPISet_copy) == 0:
        endAPISet_copy.append(gg.root)

    found_path = False

    result = []
    path_list = []
    path = [startAPI]
    path_list.append(path)

    while path_list:
        # log.test('result_len: ', len(result))
        if len(endAPISet_copy) == 0:
            break
        if path_limit:
            if len(result) == path_limit:
                break
        path = path_list.pop(0)

        if path[-1] in gg.nt_dict:
            # log.test('path[-1].source: ', gg.nt_dict[path[-1]].sources)
            for i in gg.nt_dict[path[-1]].sources:
                if i not in path:
                    tmp_path = list(path)
                    tmp_path.append(i)
                    # is_path_add = True
                    if i in endAPISet_copy:
                        result.append(tmp_path)
                        found_path = True
                        # log.test('path found: ', tmp_path)
                        path_list.append(tmp_path)
                    elif i == gg.root:
                        result.append(tmp_path)
                    else:
                        path_list.append(tmp_path)
        elif path[-1] in gg.api_dict:
            # log.test('path[-1].source: ', gg.api_dict[path[-1]].sources)
            for i in gg.api_dict[path[-1]].sources:
                if i not in path:
                    tmp_path = list(path)
                    tmp_path.append(i)
                    if i in endAPISet_copy:
                        result.append(tmp_path)
                        found_path = True
                        #                     endAPISet.remove(i)
                        log.test('path found: ', tmp_path)
                        path_list.append(tmp_path)
                    elif i == gg.root:
                        result.append(tmp_path)
                    else:
                        path_list.append(tmp_path)
        else:
            log.err("Invalid name: " + path[-1])

    if found_path and endAPISet:
        remove_list = []
        for r in result:
            if r[-1] == gg.root:
                remove_list.append(r)
        for r in remove_list:
            result.remove(r)

    log.log("total paths: ", str(len(result)))
    for i in result:
        log.test(i, len(i))
    return result


################### Search started #####################
# search paths for all dependency edges.
# The function adds paths to corresponding edges
# Returns reorder_dict for following steps
def single_prep_dep_path_search(nlp, d, gg):
    # target to prep
    target_prep_result = []
    for api in nlp.token[d.target].mapping:
        target_prep_result += (single_start_BFS(api, d.prep_mapping, gg))
    #         d.paths.append(target_prep_result)

    # prep to source
    prep_source_result = []
    for api in d.prep_mapping:
        prep_source_result += (single_start_BFS(api, nlp.token[d.source].mapping, gg))

    # connect paths
    connect_path = []
    for tpr in target_prep_result:
        tmp = tpr[-1]
        #             c_path = []
        for psr in prep_source_result:
            if psr[0] == tmp:
                connect_path.append(tpr + psr[1:])
    #             connect_path.append(c_path)

    if not connect_path:
        # print('%%%%%----', target_prep_result)
        d.paths = target_prep_result
    else:
        d.paths = connect_path


def all_paths_search(nlp, gg, single_path_limit = None, reorder_shortest_select = False):
    log.log('Starting all paths search ...')
    reorder_dict = {}
    for d in nlp.dependency:
        if d.prep_mapping:
            log.test('prep_mapped')
            single_prep_dep_path_search(nlp, d, gg)
            # # target to prep
            # target_prep_result = []
            # for api in nlp.token[d.target].mapping:
            #     target_prep_result += (single_start_BFS(api, d.prep_mapping, gg))
            # #         d.paths.append(target_prep_result)
            #
            # # prep to source
            # prep_source_result = []
            # for api in d.prep_mapping:
            #     prep_source_result += (single_start_BFS(api, nlp.token[d.source].mapping, gg))
            #
            # # connect paths
            # connect_path = []
            # for tpr in target_prep_result:
            #     tmp = tpr[-1]
            #     #             c_path = []
            #     for psr in prep_source_result:
            #         if psr[0] == tmp:
            #             connect_path.append(tpr + psr[1:])
            # #             connect_path.append(c_path)
            #
            # if not connect_path:
            #     # print('%%%%%----', target_prep_result)
            #     d.paths = target_prep_result
            # else:
            #     d.paths = connect_path

        else:
            if d.dep in ['neg', 'compound', 'amod'] and nlp.token[d.source].mapping and nlp.token[d.target].mapping:
                log.test('reorderable dependency relation')
                source_to_target = []
                is_root_path = True
                for api in nlp.token[d.source].mapping:
                    target_source_result = single_start_BFS(api, nlp.token[d.target].mapping, gg, single_path_limit)
                    if (is_root_path and target_source_result[0][-1] == gg.root) or (
                            not is_root_path and not target_source_result[0][-1] == gg.root):
                        source_to_target += (target_source_result)
                    elif is_root_path and not target_source_result[0][-1] == gg.root:
                        source_to_target.clear()
                        source_to_target = target_source_result
                        is_root_path = False
                    elif not is_root_path and target_source_result[0][-1] == gg.root:
                        pass

                target_to_source = []
                is_root_path = True
                for api in nlp.token[d.target].mapping:
                    target_source_result = single_start_BFS(api, nlp.token[d.source].mapping, gg, single_path_limit)
                    if (is_root_path and target_source_result[0][-1] == gg.root) or (
                            not is_root_path and not target_source_result[0][-1] == gg.root):
                        target_to_source += (target_source_result)
                    elif is_root_path and not target_source_result[0][-1] == gg.root:
                        target_to_source.clear()
                        target_to_source = target_source_result
                        is_root_path = False
                    elif not is_root_path and target_source_result[0][-1] == gg.root:
                        pass

                # if source to target paths trace to root, the original order is correct
                if source_to_target[0][-1] == gg.root:
                    log.test('source to taget trace to root, set paths as target to source')
                    d.paths = target_to_source

                # elif target to source paths trace to root and source to target not,
                # the reversed order is correct, swap dep
                elif target_to_source[0][-1] == gg.root:
                    log.test('target to source trace to root, set paths as source to target')
                    d.paths = source_to_target
                    reorder_dict[d.source] = d
                #                 tmp = d.source
                #                 d.source = d.target
                #                 d.target = tmp

                # else, still use target to source
                else:
                    if not reorder_shortest_select:
                        log.test('both not root, still use target to source')
                        d.paths = target_to_source
                    else:
                        log.log('reorder path using shortest path')
                        target_to_source.sort(key=len)
                        source_to_target.sort(key=len)
                        log.test('target source: ', target_to_source)
                        log.test('source target: ', source_to_target)
                        if len(target_to_source[0]) <= len(source_to_target[0]):
                            log.test('keep target to source')
                            d.paths = target_to_source
                        else:
                            log.test('use source to target')
                            d.paths = source_to_target
                            reorder_dict[d.source] = d

            else:
                log.test('no reorder dependency')
                target_to_source = []
                is_root_path = True
                for api in nlp.token[d.target].mapping:
                    target_source_result = single_start_BFS(api, nlp.token[d.source].mapping, gg, single_path_limit, not (d.dep in ['nsubj', 'nsubjpass'] )) #and ('V' in nlp.token[d.source].pos or 'V' in nlp.token[d.target].pos)))
                    if target_source_result:
                        if (is_root_path and target_source_result[0][-1] == gg.root) or (
                                not is_root_path and not target_source_result[0][-1] == gg.root):
                            target_to_source += target_source_result
                        elif is_root_path and not target_source_result[0][-1] == gg.root:
                            target_to_source.clear()
                            target_to_source = target_source_result
                            is_root_path = False
                        elif not is_root_path and target_source_result[0][-1] == gg.root:
                            pass

                d.paths = target_to_source
                log.test('--%%% add result to path: ', d.paths)
    return reorder_dict


# Group reorder edges, reorder edges and renew dependent dict
def edge_reordering(nlp, gg, reorder_dict, dependent_dict, single_path_limit = None):
    log.log('Edges reordering... ')
    reorder_group = []
    for d in nlp.dependency:
        if d.target in reorder_dict:
            reorder_group.append([d, reorder_dict[d.target]])
        # if d.source

    log.test('reorder_group:', reorder_group)
    log.test('reorder_dict', reorder_dict)

    # reorder edges
    for g in reorder_group:
        g[0].target = g[1].target
        g[1].target = g[1].source
        g[1].source = g[0].target

        # g[1]'s paths are the reordered paths already, reset g[0]'s paths
        g[0].paths.clear()
        target_to_source = []
        is_root_path = True

        if g[0].prep_mapping:
            single_prep_dep_path_search(nlp, g[0], gg)

        else:
            for api in nlp.token[g[0].target].mapping:

                target_source_result = single_start_BFS(api, nlp.token[g[0].source].mapping, gg, single_path_limit)
                if (is_root_path and target_source_result[0][-1] == gg.root) or (
                        not is_root_path and not target_source_result[0][-1] == gg.root):
                    target_to_source += target_source_result
                elif is_root_path and not target_source_result[0][-1] == gg.root:
                    target_to_source.clear()
                    target_to_source = target_source_result
                    is_root_path = False
                elif not is_root_path and target_source_result[0][-1] == gg.root:
                    pass

            g[0].paths = target_to_source

    # renew dependent dict
    dependent_dict.clear()
    for d in nlp.dependency:
        dependent_dict[d.target] = d.source
    log.test('dependent_dict: ', [[nlp.token[k].word, nlp.token[dependent_dict[k]].word] for k in dependent_dict.keys()])


# count the numbers of api in the path
def count_api_in_path(path, gg):
    count = 0
    for p in path:
        if p in gg.api_dict:
            count += 1
    return(count)


# set all api path, which means the path with only API
def set_all_api_path(nlp, gg):
    cnt = []
    for d in nlp.dependency:
        cnt.append(len(d.paths))
        for paths in d.paths:
            path_api_list = []
            paths.reverse()
            for node in paths:
                if node in gg.api_dict:
                    path_api_list.append(node)
            d.api_paths.append(path_api_list)
    log.test('Path len', cnt)
    # log.record('Path len', cnt, 'sum: ', sum(cnt))


# replace common knowledge API with API(ck_arguments)
def replace_common_knowledge_API(nlp):
    log.log('replace common knowledge api...')
    for d in nlp.dependency:
        if nlp.token[d.target].ner == 'translated':
            for path in d.paths:
                if len(nlp.token[d.target].word) == 1:
                    path[-1] = nlp.token[d.target].word[0]
                else:
                    for word in nlp.token[d.target].word:
                        if path[-1] == word[0:word.find('(')]:
                            path[-1] = word

################### Reversed all paths search Ends ###################

################### Path combination ###################


# find siblings in dependency graph
def find_siblings(nlp):
    log.log('find siblings on dependency graph...')
    dep_dict = {}
    path_dict = {}

    for d in nlp.dependency:
        if d.source in dep_dict:
            dep_dict[d.source].append(d)
        else:
            dep_dict[d.source] = [d]
            path_dict[d.source] = []

    # log.test('dep_dict: ', dep_dict)
    # for k in dep_dict.keys():
    #     log.test('key: ', nlp.token[k].word)
    #     for i in dep_dict[k]:
    #         log.test('dep:', nlp.token[i.target].word)

    return [dep_dict, path_dict]


def combine_paths(paths_be_append, paths_to_append, new_dep_size_limit):
    log.test('paths be append', len(paths_be_append), paths_be_append)
    log.test('paths to append', len(paths_to_append), paths_to_append)
    new_paths = []
    for pb in paths_be_append:
        for pt in paths_to_append:
            if '(' in pt[0] and len(pt) == 1:
                new_paths.append(list(pb[0:len(pb)-1]) + [pt[0]])
            elif pb[-1] == pt[0]:
                new_paths.append(list(pb) + pt[1:])

    if new_dep_size_limit:
        if len(new_paths) > new_dep_size_limit:
            path = []
            log.log('dependency paths length: ', len(new_paths))
            new_paths.sort(key = len)
            path.append(new_paths[0])
            min_path_len = len(new_paths[0])
            index = 1
            while len(path[-1]) == min_path_len and index < len(new_paths):
                # log.err(path)
                if new_paths[index] not in path:
                    path.append(new_paths[index])
                index += 1
                if len(path[-1]) > min_path_len and len(path) < new_dep_size_limit - 5:
                    min_path_len = len(path[-1])
            new_paths = path
            log.log('paths length after set: ', len(new_paths))
            log.log('new paths: ', new_paths)

    return new_paths


def reorder_single_dep_key(dependent_dict, single_dep_key):
    new_key = []
    for k in single_dep_key:
        if not dependent_dict[k] in new_key:
            new_key.append(k)
        else:
            new_key.insert(new_key.index(dependent_dict[k]), k)
    return new_key


def attach_non_sibling_edges(nlp, gg, dependent_dict, dep_dict, new_dep_size_limit = None):
    log.log('attach_non_sibling_edges...')
    root_dep_list = []
    single_dep_key = []
    for k in dep_dict.keys():
        # log.test('check dep: ', nlp.token[k].word)
        if len(dep_dict[k]) == 1:
            if not dep_dict[k][0].paths[0][0] == gg.root:
                source_index = dependent_dict[k]
                is_be_append_root = False
                for dep in dep_dict[source_index]:
                    if dep.target == k:
                        if dep.paths[0][0] == gg.root:
                            is_be_append_root = True
                            break
                if not is_be_append_root:
                    single_dep_key.append(k)
    # log.test('singel dep key: ', single_dep_key, [nlp.token[k].word for k in single_dep_key])
    new_single_dep_key = reorder_single_dep_key(dependent_dict, single_dep_key)
    # log.test('new singel key: ', new_single_dep_key, [nlp.token[k].word for k in new_single_dep_key])

    for k in new_single_dep_key:
        paths_to_append = dep_dict[k][0].paths
        source = dependent_dict[k]
        # log.test('%%%% test: ', dep_dict[k][0].target, nlp.token[dep_dict[k][0].target].word, k, nlp.token[k].word)
        for dep in dep_dict[source]:
            if dep.target == k:
                paths_be_append = dep.paths
                # log.test('combine dep: ', nlp.token[dep_dict[k][0].target].word, nlp.token[k].word, nlp.token[dep.source].word)
                dep.paths = combine_paths(paths_be_append, paths_to_append, new_dep_size_limit)
                # update_dependent_dict(dependent_dict, dep_dict, k)
                # Update dependent dict
                dependent_dict[dep_dict[k][0].target] = dependent_dict[k]
                # dep.target =

                dep_dict.pop(k, None)
                # log.test('pop: ', k, nlp.token[k].word)
                # log.test('new dependency path: ', dep.paths)
                break

    # log.test('dep_dict: ', dep_dict)

################### Path End ###################

############## Prefix tree related operations #############
from HISyn.back_end.PrefixTree import Prefix_tree
def build_prefix_tree(path, api_dict):
    pt = Prefix_tree()
    for p in path:
        pt.add_path(p, path.index(p), pt.root)
    pt.api_count = pt.count_api(pt.root, api_dict)
    return pt


def add_to_prefix_list(all_paths, result, tmp, index):
    if index == len(all_paths):
        result.append(list(tmp))
        return result
    #     tmp = result
    for i in all_paths[index]:
        tmp.append(i)
        add_to_prefix_list(all_paths, result, tmp, index + 1)
        tmp.pop()


def min_count_api(p, gg):
    max_count = 0
    for l in p:
        count = 0
        for i in l:
            if i in gg.api_dict:
                count += 1
        if count > max_count:
            max_count = count
    return (max_count)


def count_api_in_prefix_list(p, gg):
    api = []
    for l in p:
        for i in l:
            if i in gg.api_dict:
                api.append(i)
    return len(set(api))


def min_tree_add_path(min_tree, paths, api_dict):
    log.log('min_tree_add_path')
    min_t = []
    min_api_count = 5000
    for tree in min_tree:
        for path in paths:
            tmp = copy.deepcopy(tree)
            tmp.add_path(path, paths.index(path), tmp.root)
            tmp.api_count = tmp.count_api(tmp.root, api_dict)
            if tmp.api_count < min_api_count:
                min_api_count = tmp.api_count
                min_t.clear()
                min_t.append(tmp)
            elif tmp.api_count == min_api_count:
                min_t.append(tmp)
    return min_t


def is_list_in(l1, l2):
    for n in l1:
        if n not in l2:
            if '(' not in n:
                return False
            else:
                tmp = n[0:n.index('(')]
                if tmp not in l2:
                    return False
    return True


def find_smallest_prefix_tree(deps, gg):
    # log.log('find smallest prefix tree')
    all_paths = []
    all_paths_len = []

    for d in deps:
        #         print(d.paths)
        all_paths.append(d.paths)
        all_paths_len.append(len(d.paths))
    # log.test('all paths length: ', all_paths_len)

    tree_list = []
    tree_index_list = []
    path_list = []
    for i in range(len(all_paths_len)):
        if all_paths_len[i] < 500:
            tree_list.append(all_paths[i])
            tree_index_list.append(range(len(all_paths[i])))
        else:
            path_list.append(all_paths[i])

    prefix_list = []
    tmp = []
    add_to_prefix_list(tree_index_list, prefix_list, tmp, 0)

    #     print('---------2-----------')
    #     print(all_paths)

    # log.test('length of prefix tree:', len(prefix_list))
    #     print(prefix_list)

    prefix_tree = []
    min_tree = []
    min_api_count = 5000

    exe_count = 0

    for pre_tree in prefix_list:
        p = [tree_list[i][pre_tree[i]] for i in range(len(pre_tree))]
        api_count = count_api_in_prefix_list(p, gg)
        if api_count > min_api_count:
            continue
        tmp = build_prefix_tree(p, gg.api_dict)
        exe_count += 1

        # is_gram_correct = check_prefix_grammar(tmp, gg)
        is_gram_correct = tmp.check_grammar(gg)
        if not is_gram_correct:
            continue

        prefix_tree.append(tmp)
        if tmp.api_count < min_api_count:
            min_api_count = tmp.api_count
            min_tree.clear()
            min_tree.append(tmp)

        elif tmp.api_count == min_api_count:
            min_tree.append(tmp)

        if tmp.api_count == 0:
            log.test(p)
            break

    for paths in path_list:
        min_tree = min_tree_add_path(min_tree, paths, gg.api_dict)

    # log.test('Minimum trees')
    # for i in min_tree:
    #     i.display()

    # log.log('Execute times:', exe_count)

    return (min_tree)


# find shortest path for each <start, end> pair
def find_shortest_path(dep):
    log.log('find shortest path:', dep.dep)
    symb_path = dep.paths
    api_path = dep.api_paths

    log.test('symb_path length:', len(symb_path))

    add_list = []
    shortest_paths = [symb_path[0]]
    shortest_api_path = [api_path[0]]
    for i in range(1, len(symb_path)):
        #         print('-----shortest path: ', shortest_paths)
        is_same_start_end_in = False
        for s in range(len(shortest_paths)):
            #
            if symb_path[i][0] == shortest_paths[s][0] and symb_path[i][-1] == shortest_paths[s][-1]:
                is_same_start_end_in = True
                log.test('same <start, end> found: ' + shortest_paths[s][0] + ', ' + shortest_paths[s][-1])
                if len(api_path[i]) < len(shortest_api_path[s]):  # shorter, replace
                    shortest_paths[s] = symb_path[i]
                    shortest_api_path[s] = api_path[i]
                elif len(api_path[i]) == len(shortest_api_path[s]):  # same, add to list
                    #                     print('--------same length add--------')
                    shortest_paths.append(symb_path[i])
                    shortest_api_path.append(api_path[i])
                    break
            #                     add_list.append(symb_path[i])
            #                     add_list.append(api_path[i])
        if not is_same_start_end_in:
            #                 pass
            shortest_paths.append(symb_path[i])
            shortest_api_path.append(api_path[i])
            break
    #         if add_list:
    #             shortest_paths.append(add_list[0])
    #             shortest_api_path.append(add_list[1])
    #             add_list.clear()

    dep.paths = shortest_paths
    dep.api_paths = shortest_api_path
    return (shortest_paths)


def path_selection(nlp, gg, dep_dict, path_dict):
    log.log('Path selection: min path/prefix tree heuristic')
    root_dep_list = []

    for k in dep_dict.keys():
        # log.test('dependency dict:', k, dep_dict[k])
        if len(dep_dict[k]) == 1:
            # log.test('--%%%--', dep_dict[k][0].dep, dep_dict[k][0].paths)
            # log.test(dep_dict[k][0].paths[0][0])
            if dep_dict[k][0].paths[0][0] == gg.root:
                # log.test('root paths, add to root dep list')
                root_dep_list.append(dep_dict[k][0])
            else:
                # path = find_shortest_path(dep_dict[k][0])
                # test, consider all the paths
                path = dep_dict[k][0].paths
                l = []
                for p in path:
                    pt = Prefix_tree()
                    pt.add_path(p, path.index(p), pt.root)
                    l.append(pt)
                path_dict[k] = l
                # log.log('Single edge, shortest path list')
                # log.test(path_dict[k])
        else:
            ll = []
            for i in dep_dict[k]:
                # log.test('--$$$--', i.dep, i.paths)
                if i.paths:
                    if i.paths[0][0] == gg.root:
                        # log.test('root path, added to root-dep-list')
                        root_dep_list.append(i)
                    else:
                        ll.append(i)
            if ll:
                import time
                # start_time = time.time()
                path_dict[k] = find_smallest_prefix_tree(ll, gg)
                # log.test('prefix time: ', time.time()-start_time)
    # log.log('root dep list: ', root_dep_list)
    return root_dep_list


#################### Code generation tree ##############
# add cgt2 to cgt1 with prefix tree, cgt1_node has same name with cgt2_node
def prefix_combine(cgt1_node, cgt2_node):
#     log.log('prefix combine: ' + cgt1_node.name + ' ' + cgt2_node.name)
    child1_name = []
    for child1 in cgt1_node.child:
        child1_name.append(child1.name)
    for child2 in cgt2_node.child:
#         log.test('checking for cgt2 child: ' + child2.name)
        if child2.name in child1_name:
#             log.test('child2 name in child1: ' + child2.name)
            prefix_combine(cgt1_node.child[child1_name.index(child2.name)], child2)
        else:
#             log.test('child2 name not in child1, add to child1 list: ' + child2.name)
            cgt1_node.child.append(child2)


# add cgt2 to cgt1
def combine_trees(cgt1_node, cgt2):
    common_node = cgt2.root.child[0]
    #     log.log('combine trees:')
    #     log.test('cgt1_node name: ' + cgt1_node.name)
    #     log.test('cgt2_root name: ' + common_node.name)

    if cgt1_node.name == common_node.name:
        #         log.test('node found!')
        if len(cgt1_node.child) == 0:
            #             print('cgt_1.child = common_node.child', common_node.child)
            cgt1_node.child = common_node.child
            return True
        else:
            prefix_combine(cgt1_node, common_node)
            return True
    else:
        for i in cgt1_node.child:
            if not combine_trees(i, cgt2):
                continue
            else:
                return True
        return False


from HISyn.back_end.CGTree import CG_tree
# change current prefix trees and all root-paths into code generation tree
# prefix tree and cgt has different join rules.
def prefix_tree_to_cg_tree(gg, root_dep_list, path_dict, root_index):
    #convert root-paths
    log.test('convert prefix trees to code generation trees')
    root_cg_tree_dict = {}  # {target of root path: cgt_list}
    for d in root_dep_list:
        d.source = root_index
        cgt_list = []
        for p in d.paths:
            cg_tree = CG_tree()
            cg_tree.list_to_cg(p, gg)
            cgt_list.append(cg_tree)
    #         cg_tree.display(cg_tree.root, 0)
        root_cg_tree_dict[d.target] = cgt_list

    # log.log('root_cg_tree_dict: ', root_cg_tree_dict, 'key: ', root_cg_tree_dict.keys())

    # convert prefix trees
    cg_tree_dict = {}     # {source_index: minimum_cgt(min prefix or shortest path)}
    for key in path_dict.keys():
        tmp = []
        for pt in path_dict[key]:
    #         print(key, pt)
            cg_tree = CG_tree()
            cg_tree.prefix_to_cg(pt.root, cg_tree.root, gg)
            tmp.append(cg_tree)
    #         cg_tree.display(cg_tree.root, 0)
        cg_tree_dict[key] = tmp
    # log.log('cg_tree_dict: ', cg_tree_dict)

    return [root_cg_tree_dict, cg_tree_dict]


# connect all un-root cgt
def connect_unroot_cgt(nlp, gg, root_index, cg_tree_dict, dependent_dict, root_cg_tree_dict):
    log.log('connect all cgts whose root is not root')
    root_governor_index = []
    for k in cg_tree_dict.keys():
        # log.test('find for k: ', k, nlp.token[k].word)
        if k in root_cg_tree_dict:
            # log.test('tree is root cgt, continue', nlp.token[k].word)
            continue
        if cg_tree_dict[k]:
            # log.test('k tree found, length:', len(cg_tree_dict[k]))
            if k in dependent_dict:
                # log.test('k has source: ', nlp.token[dependent_dict[k]].word)
                governor = dependent_dict[k]
                if governor == root_index:
                    root_governor_index.append(k)
                    # log.test('governor is root, break')
                    continue
                while (not cg_tree_dict[governor]) and (not governor == root_index):
                    # log.test('governor is empty, change to governor\'s governor')
                    # log.test('governor\'s governor: ', nlp.token[dependent_dict[governor]].word)
                    governor = dependent_dict[governor]
                if governor == root_index:
                    root_governor_index.append(k)
                    # log.test('governor is root, break')
                    continue
                a1_list = []
                for a1 in cg_tree_dict[governor]:
                    for a2 in cg_tree_dict[k]:
                        a1_tmp = copy.deepcopy(a1)
                        a2_tmp = copy.deepcopy(a2)
                        # log.test('combining trees: ')
                        # a1_tmp.display()
                        # a2_tmp.display()
                        combine_trees(a1_tmp.root, a2_tmp)
                        if a1_tmp.check_cgt_grammar(gg):
                            a1_list.append(a1_tmp)
                # log.test('combined tree: ')
                for tree in a1_list:
                    tree.display()
                cg_tree_dict[governor] = a1_list
                cg_tree_dict[k].clear()
        else:
            log.test('k tree not found')

    # log.log('root_governor_index: ', root_governor_index)
    # for i in root_governor_index:
    #     cg_tree_dict[i][0].display()

    return root_governor_index


# connect cgt to root_cgt
# remove root cgt which cannot be append a cgt
def connect_cgt_to_root_cgt(cg_tree_dict, root_cg_tree_dict):
    log.log('connect cgts to root cgts')
    remove_dict = {}
    root_cgt_dict = {}

    # log.test('cg_tree_dict keys: ', cg_tree_dict.keys())
    # log.test('root_cg_tree_dict keys: ', root_cg_tree_dict.keys())

    connect_count = 0
    for cg_key in cg_tree_dict.keys():
        if cg_key in root_cg_tree_dict and cg_tree_dict[cg_key]:
            connect_count += len(root_cg_tree_dict[cg_key]) * len(cg_tree_dict[cg_key])

    # log.test('total numbers of connection: ', connect_count)

    for cg_key in cg_tree_dict.keys():
        if cg_key in root_cg_tree_dict and cg_tree_dict[cg_key]:
            remove_dict[cg_key] = []
            root_cgt_dict[cg_key] = []
            for cgt1 in root_cg_tree_dict[cg_key]:
                a1_list = []
                for cgt2 in cg_tree_dict[cg_key]:
                    a1_tmp = copy.deepcopy(cgt1)
                    a2_tmp = copy.deepcopy(cgt2)
                    # log.test('combine trees: ')
                    # a1_tmp.display()
                    # a2_tmp.display()
                    result = combine_trees(a1_tmp.root, a2_tmp)
                    # log.lprint('****** result: ', result, 'cg_key: ', cg_key)
                    if result:
                        a1_list.append(a1_tmp)
                if a1_list:
                    for i in a1_list:
                        root_cgt_dict[cg_key].append(i)
                else:
                    remove_dict[cg_key].append(cgt1)

    # log.test('root_cgt_dict: ', root_cgt_dict)

    # add other root paths which did not have un-root cgt

    for key in root_cg_tree_dict:
        if not key in root_cgt_dict:
            root_cgt_dict[key] = root_cg_tree_dict[key]

    # for key in root_cgt_dict.keys():
    #     log.test('root cgt dict key: ', key, 'length: ', len(root_cgt_dict[key]), '--------')
    #     for cgt in root_cgt_dict[key]:
    #         cgt.display()

    return root_cgt_dict


# put all combinations into lists, result contains all possible combinations
def set_all_cgt_combinations(root_cgt_dict):
    log.log('Set all cgt combinations ...')
    root_cgt_list = []
    for key in root_cgt_dict.keys():
        if root_cgt_dict[key]:
            root_cgt_list.append(root_cgt_dict[key])
    # print(root_cgt_list)

    root_cgt_group = []
    tmp = []
    # log.test('root_cgt_list: ', root_cgt_list)
    add_to_prefix_list(root_cgt_list, root_cgt_group, tmp, 0)
    # log.log('# of root cgt group: ', len(root_cgt_group))
    # log.record('# of root cgt group: ', len(root_cgt_group))

    return root_cgt_group


def count_api_in_cgt_list(cgt_list, gg):
    api = []
    for cgt in cgt_list:
#         cgt.display(cgt.root, 0)
        cgt.set_api_list(cgt.root, gg)
#         print('**** cgt_api: ', cgt.api_list)
        api += cgt.api_list
    return(len(set(api)))


def combine_cgt(root_cgt_group, gg):
    log.log('Combine cgts in each group ...')
    min_tree = []
    min_api_count = 5000
    min_index = None

    exe_count = 0

    for tree_set in root_cgt_group:

        # log.test('%%%%% execute count: ', exe_count)
        tree_set_api_count = count_api_in_cgt_list(tree_set, gg)
        if tree_set_api_count > min_api_count:
            continue

        import time
        start_time = time.time()
        cgt1 = copy.deepcopy(tree_set[0])
        for i in range(1, len(tree_set)):
            # log.test('combine start ...')
            cgt2 = copy.deepcopy(tree_set[i])
            # cgt1.display()
            # cgt2.display()
            combine_trees(cgt1.root, cgt2)
        # log.test('combine_cgt_time: ', time.time() - start_time)

        exe_count += 1
        is_gram_correct = cgt1.check_cgt_grammar(gg)
        if not is_gram_correct:
            continue
        # else:
        #     log.lprint('%%%% correct tree display %%%%')
        #     cgt1.display()
        #     log.lprint("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

        # count api in tree_set[0]
        cgt1.set_api_list(cgt1.root, gg)

        if cgt1.api_count < min_api_count:
            min_api_count = cgt1.api_count
            min_tree.clear()
            min_tree.append(cgt1)
            min_index = root_cgt_group.index(tree_set)

        elif cgt1.api_count == min_api_count:
            min_tree.append(cgt1)
            min_index = root_cgt_group.index(tree_set)

        if cgt1.api_count == 0:
            log.test(cgt1)
            break

    # display_min_tree(min_tree, min_index, exe_count)
    return min_tree


def display_min_tree(min_tree, min_index, exe_count):
    for i in min_tree:
        log.lprint('api_count: ', i.api_count)
        i.display()

    log.log('Execute times:')
    log.log(exe_count)
################### Path combination Ends ###################


################## code generation ######################

# Check if node consists with grammar, all nodes are putting into
# an incomplete node list
def grammar_check_go(cg_node, incomplete_node_list, gg):
    # log.log('check node: ' + cg_node.name)

    formal_child = gg.get_child(cg_node.name)

    cg_node.formal_child = formal_child

    child_list = [n.name for n in cg_node.child]

    if formal_child:
        if child_list in formal_child:
            cg_node.is_complete = True
        else:
            incomplete_node_list.append(cg_node)
    else:
        if not child_list:
            cg_node.is_complete = True
        else:
            incomplete_node_list.append(cg_node)
    # log.test(cg_node.is_complete)

    if cg_node.child:
        for n in cg_node.child:
            grammar_check_go(n, incomplete_node_list, gg)


def grammar_check(tree_list, gg):
    log.test('checking grammar on cgts...')
    incomplete_node_list = []
    for final_incomp_tree in tree_list:
        grammar_check_go(final_incomp_tree.root.child[0], incomplete_node_list, gg)
    return incomplete_node_list


# Remove API with arguments and API with non arguments.
# They are correct APIs.
def remove_API_with_arguments(incomplete_node_list):
    remove_list = []
    for i in incomplete_node_list:
        # log.lprint('name:', i.name)
        # log.lprint('child:', [n.name for n in i.child])
        # log.lprint('formal:', i.formal_child)

        if len(i.child) == 1:
            if '(' in i.child[0].name:
                tmp_name = i.child[0].name[0:i.child[0].name.index('(')]
                if [tmp_name] in i.formal_child:
                    i.is_complete = True
                    remove_list.append(i)
        elif len(i.child) == 0:
            if i.formal_child == [['']]:
                i.is_complete = True
                remove_list.append(i)

    for r in remove_list:
        incomplete_node_list.remove(r)


# Order child nodes. Put arguments to correct location
def order_child_nodes(node_list, child_list): # change node_list order based on child_list
    log.log('reorder child nodes')
    log.lprint(child_list)
    length = len(node_list)
    new_node_list = [0]*length
    for i in node_list:
        index = child_list.index(i.name)
        new_node_list[index] = i
    return new_node_list


# check node derivations, set arguments to correct location is a node is valid, remove from incomplete list
# remove invalid derivations
def set_valid_nodes(incomplete_node_list):
    log.log('changing argument order of valid nodes')
    remove_list = []

    for i in incomplete_node_list:
        # log.lprint('name:', i.name)
        # log.lprint('child:', [n.name for n in i.child])
        # log.lprint('formal:', i.formal_child)

        if len(i.child) == 1:
            if '(' in i.child[0].name:
                tmp_name = i.child[0].name[0:i.child[0].name.index('(')]
                if [tmp_name] in i.formal_child:
                    i.is_complete = True
                    remove_list.append(i)
        elif len(i.child) == 0:
            if i.formal_child == [['']]:
                i.is_complete = True
                remove_list.append(i)

    for r in remove_list:
        incomplete_node_list.remove(r)


# Remove invalid trees whose derivation is invalid
# Set valid node to correct location, remove it from incomplete node list
def remove_invalid_trees(incomplete_node_list):
    log.log('removing trees with wrong grammar...')
    remove_list = []

    for i in incomplete_node_list:
        # log.lprint('name:', i.name)
        # log.lprint('child:', [n.name for n in i.child])
        # log.lprint('formal:', i.formal_child)

        child_names = [n.name for n in i.child]

        if i.tree.is_valid_tree:
            i.tree.is_valid_tree = False

            for f in i.formal_child:
                if len(f) < len(child_names):
                    continue
                elif len(f) == len(child_names):
                    if set(f) == set(child_names):
                        i.tree.is_valid_tree = True
                        i.child = order_child_nodes(i.child, f)
                        remove_list.append(i)
                        break
                    else:
                        continue
                else:
                    if is_list_in(child_names, f):
                        i.tree.is_valid_tree = True
                        i.complete_index = i.formal_child.index(f)
                        break
                    else:
                        continue
        # log.lprint('is_valid? ', i.tree, i.tree.is_valid_tree)

    for i in remove_list:
        incomplete_node_list.remove(i)


# Delete invalid tree and tree nodes
def delete_invalid_tree(final_CG_tree_list, incomplete_node_list):
    invalid_tree_remove_list = []
    invalid_tree_node_remove_list = []
    for tree in final_CG_tree_list:
        if not tree.is_valid_tree:
            invalid_tree_remove_list.append(tree)

    for i in incomplete_node_list:
        if i.tree in invalid_tree_remove_list:
            invalid_tree_node_remove_list.append(i)

    for i in invalid_tree_remove_list:
        final_CG_tree_list.remove(i)

    for i in invalid_tree_node_remove_list:
        incomplete_node_list.remove(i)


# Complete a single branch with default arguments
from HISyn.back_end.CGTree import CG_tree_node


def complete_CG_node(node_name, tree, gg):
    log.test('completing node, node name:', node_name)
    cg_node = CG_tree_node(node_name, tree)
    formal_child = gg.get_child(node_name)
    # log.lprint(formal_child)
    if formal_child and formal_child[0][0] != '':
        for fc in formal_child[0]:
            cg_node.child.append(complete_CG_node(fc, tree, gg))
    return (cg_node)


# add complete nodes to right position
def add_complete_nodes_to_position(incomplete_node_list, gg):
    log.log('adding default argument to complete the cgt...')
    for node in incomplete_node_list:
        # log.lprint(node.name)
        new_node_list = [CG_tree_node("empty", node.tree)]*len(node.formal_child[node.complete_index])
        for fn in node.formal_child[node.complete_index]:
            log.test('node child:', node.child, [i.name for i in node.child])
            log.test('fn: ', fn)
            if fn not in [n.name for n in node.child]:
                index = node.formal_child[node.complete_index].index(fn)
                new_node_list[index] = complete_CG_node(fn, node.tree, gg)
            else:
                log.test('node exists, set position')
                index = node.formal_child[node.complete_index].index(fn)
                log.test('index', index)
                new_node_list[index] = node.child[[n.name for n in node.child].index(fn)]
        node.child = new_node_list


# check complete tree
def select_min_cgt(final_CG_tree_list, gg):
    min_size = 200
    min_tree_list = []
    for cgt in final_CG_tree_list:
        cgt.set_api_list(cgt.root, gg)
        tmp_size = cgt.api_count
        if tmp_size < min_size:
            min_size = tmp_size
            min_tree_list = [cgt]
        elif tmp_size == min_size:
            min_tree_list.append(cgt)
        else:
            continue
    return min_tree_list

def final_cgt_check(final_CG_tree_list, gg):
    incomplete_node_list = grammar_check(final_CG_tree_list, gg)
    set_valid_nodes(incomplete_node_list)

    if incomplete_node_list:
        remove_list = []
        for i in incomplete_node_list:
            if i.tree not in remove_list:
                remove_list.append(i.tree)
        for r in remove_list:
            final_CG_tree_list.remove(r)

    min_tree_list = select_min_cgt(final_CG_tree_list, gg)

    return min_tree_list


from HISyn.back_end.APITree import API_tree


# tranform CG-tree to expression through API tree
def convert_to_expression(final_CG_tree_list, gg):
    log.log('converting to codes...')
    expression_list = []
    for tree in final_CG_tree_list:
        expr = tree.convert_to_expr(gg)
        if expr:
            expression_list.append(expr)
        # api_tree = API_tree()
        # api_tree.cg_to_api(tree.root, api_tree.root, gg)
        # expression_list.append(api_tree.generate_expression())
    return expression_list
    # for tree in final_CG_tree_list:
    #     tree.display()

################## code generation end ##################


# Overall semantic mapping function
def semantic_mapping(domain, gg, nlp, common_knowledge_tags):
    common_knowledge_mapping(gg, nlp, common_knowledge_tags)
    mapping_keywords(gg, nlp)
    domain_specific_mapping_rules(domain, nlp)
    remove_empty_edge(nlp)


# Overall longest match
def longest_matching(nlp):
    set_modifier_group(nlp)
    modifier_vote((nlp))


# Overall preposition set & reordering
def reordering(nlp, gg, preposition):
    set_preposition(nlp, gg, preposition)
    subj_reorder(nlp)
    remove_empty_edge(nlp)

    # add root node for dependency edges if the source has a mapping
    [dependent_dict, no_gov_source_dict, empty_mapping_source_edge_dict] = check_governor(nlp)
    root_index = add_root_node(nlp, dependent_dict, no_gov_source_dict, empty_mapping_source_edge_dict)
    remove_empty_edge(nlp)

    # todo: add domain-specific operations
    return [dependent_dict, no_gov_source_dict, empty_mapping_source_edge_dict, root_index]


# Overall all-path search
def reversed_all_path_searching(domain, nlp, gg, dependent_dict):
    # All paths search
    if domain == 'ASTMatcher':
        reorder_dict = all_paths_search(nlp, gg, single_path_limit=10, reorder_shortest_select=True)
        from HISyn.domain_knowledge.ASTMatcher.domain_specific_function_kit import set_shortest_path
        set_shortest_path(nlp, length=10)
        # adf.set_shortest_path(nlp, length=10)
    else:
        reorder_dict = all_paths_search(nlp, gg)

    # Reorder edges
    edge_reordering(nlp, gg, reorder_dict, dependent_dict, single_path_limit=10)
    # nlp.displayByEdge()

    # Special rules for flight domain
    import HISyn.domain_knowledge.Flight.domain_specific_function_kit as fdf
    if domain == 'Flight':
        fdf.lock_project(nlp, gg)

    # Set all api paths: may not useful
    set_all_api_path(nlp, gg)
    # nlp.displayByEdge()

    # replace common knowledge API with API(ck_argument)
    # Purpose: these APIs become distinguished to each other and
    #  won't be combined in later steps
    replace_common_knowledge_API(nlp)
    # nlp.displayByEdge()


# Overall path-selection and combination
def path_selection_and_combination(nlp, gg, dependent_dict, root_index):
    [dep_dict, path_dict] = find_siblings(nlp)

    # Attach non-sibling edges' paths to its source
    attach_non_sibling_edges(nlp, gg, dependent_dict, dep_dict, new_dep_size_limit=10)

    # select paths for dependency edges
    root_dep_list = path_selection(nlp, gg, dep_dict, path_dict)

    # convert prefix trees to cgtrees
    [root_cg_tree_dict, cg_tree_dict] = prefix_tree_to_cg_tree(gg, root_dep_list, path_dict, root_index)

    # connect all unroot cgts
    log.test('dependent_dict: ',
             [[nlp.token[k].word, nlp.token[dependent_dict[k]].word] for k in dependent_dict.keys()])

    root_governor_index = connect_unroot_cgt(nlp, gg, root_index, cg_tree_dict, dependent_dict, root_cg_tree_dict)

    # connect current cgts to root cgts
    root_cgt_dict = connect_cgt_to_root_cgt(cg_tree_dict, root_cg_tree_dict)

    # set all tree combinations, the root_cgt_group is a list of
    # all possible combinations
    root_cgt_group = set_all_cgt_combinations(root_cgt_dict)

    # join each root cgt group
    final_CG_tree_list = combine_cgt(root_cgt_group, gg)

    return final_CG_tree_list


# Overall grammar check & code generation
def code_generation(gg, final_CG_tree_list):
    # check the final tree grammar
    incomplete_node_list = grammar_check(final_CG_tree_list, gg)

    # Set valid nodes. Check if an incomplete nodes has valid arguments
    set_valid_nodes(incomplete_node_list)

    remove_invalid_trees(incomplete_node_list)

    # delete all invalid trees and nodes
    delete_invalid_tree(final_CG_tree_list, incomplete_node_list)

    # complete nodes and put them to correct position
    add_complete_nodes_to_position(incomplete_node_list, gg)

    min_cgt  = final_cgt_check(final_CG_tree_list, gg)



    expr_list = convert_to_expression(final_CG_tree_list, gg)
    min_expr = convert_to_expression(min_cgt, gg)
    #
    log.log('promising exprs: ', min_expr)

    log.log('full candidate list: ', len(expr_list))

    return [min_expr, expr_list]


    # expr_list = convert_to_expression(final_CG_tree_list, gg)
    # min_expr = convert_to_expression(min_cgt, gg)
    #
    # return [min_cgt, final_CG_tree_list]
