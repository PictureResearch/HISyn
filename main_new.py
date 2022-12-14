import sys
sys.path.insert(0, '..')
from HISyn.tools.root_directory import root_dir


def run_HISyn(domain, text='', index = 0):
    # get query from test cases
    import HISyn.front_end.front_end_function_kit as front_kit
    if not text:
        text = front_kit.read_text(root_dir + '/Documentation/' + domain + '/text_new.txt', index)

    # Build grammar graph
    import HISyn.domain_knowledge.DomainKnowledgeConstructor as dkc
    gg = dkc.set_grammar_graph(domain, root_dir + '/Documentation/' + domain + '/grammar.txt', root_dir + '/Documentation/' + domain + '/detailed_API_documents.txt', reload = True)

    # parsing the query and prune the unimportant edges.
    # NLP
    nlp = front_kit.nlp_parsing(text, domain)

    front_kit.domain_specfic_parsing_rules(domain, nlp, gg)

    import HISyn.common_knowledge.NLPCommonKnowledge as nlpck
    front_kit.prune_edges(nlp, nlpck.prunable_dep_tags, nlpck.prunable_pos_tags, nlpck.common_knowledge_tags)

    nlp.displayByEdge()

    import HISyn.back_end.back_end_function_kit as back_kit

    back_kit.semantic_mapping(domain, gg, nlp, nlpck.common_knowledge_tags)

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
    # domain = 'Flight'
    # domain = 'ASTMatcher'
    # domain = 'TextEditing'
    # domain = 'Roblox'
    domain = 'Scratch'

    text = 'Cat moves 7 steps'
    # text = 'Cat rotates 4 degrees and moves 6 steps'
    # text = 'player dies'
    # text = 'I want to spawn 10 enemies'
       #^ when Will used my machine
    # text = 'cat glides 10 seconds to 5 5'
    # text = 'rotate 15 degrees and then move 15 steps.'
    # text = 'I want the Cat to rotate 10 degrees'
    # text = 'Cat rotates 10 degrees'
    # text = 'I want the cat to move 20 steps to the right and when the space key is pressed teleport to a random location.'
    # text = 'When Start is clicked, forever spin 15 degrees to the right'
    # text = 'If cat is touching mouse pointer then move 15 steps'
    # text = 'Repeatedly Move the cat 15 steps, then rotate 20 degrees until the cat is touching the edge then teleport to a random location.'
    # ^good example :)
    # text = 'If the Dog is touching the edge, then the cat moves 10 steps'
    # text = 'The cat glides for 3 seconds to X: 10, Y: 10. Once the Cat is done gliding, the dog will spin 15 degrees. '
    # ^glide isnt working
    # text = 'The Dog moves 15 steps and then the cat will teleport to a random location.'
    #text = 'The Cat meows if the volume of the meow is greater than 5 decibels then the Dog barks'
    #^doesn't work
    # text = 'the cat talks'
    # text = 'If the sprite is touching the color red, then wait .5 seconds then broadcast death.'
    # text = 'if sprite is red then move 5 steps'
    # text = 'broadcast hello'

    run_HISyn(domain, text=text, index=1)
