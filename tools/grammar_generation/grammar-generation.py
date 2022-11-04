from HISyn.tools.grammar_generation.GrammarGenerator_class import GrammarGenerator as GrammarGenerator_class
from HISyn.tools.grammar_generation.GrammarGenerator_function import GrammarGenerator as GrammarGenerator_func

from HISyn.tools.root_directory import root_dir

# select a generator for different target DSL
gram_gen = GrammarGenerator_class() # for domain with classes and methods
# gram_gen = GrammarGenerator_func() # for domain with only function calls

gram_gen.generate_grammar(domain = 'sklearn', doc_file=root_dir + '/Documentation/sklearn/API_documents_detailed.txt')

for k in gram_gen.api_dict:
    gram_gen.api_dict[k].display()