import sys
sys.path.insert(0, '..')
from HISyn.tools.root_directory import root_dir


def run_HISyn(domain, text='', index = 0, nlp_server=False):
    # get query from test cases
    import HISyn.front_end.front_end_function_kit as front_kit
    if not text:
        text = front_kit.read_text(root_dir + '/Documentation/' + domain + '/text_new.txt', index)

    # Build grammar graph
    import HISyn.domain_knowledge.DomainKnowledgeConstructor as dkc
    gg = dkc.set_grammar_graph(domain, root_dir + '/Documentation/' + domain + '/grammar.txt', root_dir + '/Documentation/' + domain + '/API_documents.txt', reload = True)

    # parsing the query and prune the unimportant edges.
    # NLP
    nlp = front_kit.nlp_parsing(text, domain, nlp_server)

    front_kit.domain_specfic_parsing_rules(domain, nlp, gg)

    import HISyn.common_knowledge.NLPCommonKnowledge as nlpck
    front_kit.prune_edges(nlp, nlpck.prunable_dep_tags, nlpck.prunable_pos_tags)

    nlp.displayByEdge()

    import HISyn.back_end.back_end_function_kit as back_kit

    back_kit.semantic_mapping(domain, gg, nlp)

    nlp.displayByEdge()

    back_kit.longest_matching(nlp)

    [dependent_dict, no_gov_source_dict, empty_mapping_source_edge_dict, root_index] = back_kit.reordering(nlp, gg, nlpck.preposition)

    back_kit.reversed_all_path_searching(domain, nlp, gg, dependent_dict)

    final_cgt_list = back_kit.path_selection_and_combination(nlp, gg, dependent_dict, root_index)

    [min_expr, expr_list] = back_kit.code_generation(gg, final_cgt_list)


    for i in min_expr:
        print('-', i)
    for i in expr_list:
        print('-', i)

    return [min_expr, expr_list]


if __name__ == '__main__':
    # set domain
    domain = 'Flight'
    # domain = 'TextEditing'

    # set NLP server
    nlp_server = True   # dependent server launched in separately, see README - Hint
    # nlp_server = False

    # set NL query text
    # text = 'Insert colon after 1st word'
    # run_HISyn(domain, text=text, nlp_server=nlp_server)

    # run test cases by index
    run_HISyn(domain, index=0, nlp_server=nlp_server)