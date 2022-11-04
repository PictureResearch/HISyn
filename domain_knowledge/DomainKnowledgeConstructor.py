import pickle
import os.path
import HISyn.tools.Log as log
# import HISyn.tools.Log as log
import HISyn.domain_knowledge.GrammarGraphBuilder as grammar_graph
from HISyn.tools.root_directory import root_dir


# call grammar graph builder to build grammar graph from file
def set_grammar_graph(domain, grammar_doc, api_doc, reload):
    buf_file_path = root_dir + '/domain_knowledge/grammar_graph_buffer/gg-' + domain + '.pkl'
    if os.path.exists(buf_file_path) and not reload:
        log.log('Grammar graph exists, reading...')
        buf_gg = open(buf_file_path, 'rb')
        gg = pickle.load(buf_gg)
        buf_gg.close()
        log.log('Grammar graph built')
    else:
        log.log('Set grammar graph...')
        gg = grammar_graph.GrammarGraph()
        gg.build(grammar_doc, api_doc)

        # write to buffer folder
        buf_gg = open(buf_file_path, 'wb')
        pickle.dump(gg, buf_gg)
        buf_gg.close()

        log.log('Grammar graph built')
    return gg