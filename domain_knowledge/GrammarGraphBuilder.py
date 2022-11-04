import HISyn.tools.Log as log

# class for nt of grammar
class NTNode:
    name = ''
    derivations = []  # a 2D array, outer is each derivation, inner is params in this derivation.
    sources = []  # store the node
    max_child_len = 0

    def __init__(self, nt):  # (nt_name, plain_string derivations)
        self.name = nt
        self.derivations = []
        self.sources = []
        self.max_child_len = 0
        self.derive_rule = []   # [str]



    def add_derivation(self, derivation):
        self.derivations.append(derivation)

    def add_source(self, source):
        self.sources.append(source)

    def display(self):
        log.lprint(self.name, ':=', self.derivations)


# Class for API in grammar (terms)
class APINode:
    name = ''
    params = []
    sources = []
    max_child_len = 0

    def __init__(self, api, gen_type = 'norm'):
        self.name = api
        self.params = []
        self.sources = []
        self.input = ''
        self.ret = ''
        self.description = ''
        self.generation_type = gen_type   # norm, keyword_arg, common_knowledge

    def add_params(self, param):
        self.params.append(param)

    def add_source(self, source):
        self.sources.append(source)


# Class for grammar tree
class GrammarGraph:
    nt_dict = {}  # {nt_name, nt_node}
    api_dict = {}  # {API_name, API_node}
    nt_list = []  # nt_name list
    api_list = []  # api_name list
    ck_list = []  # common knowledge
    root = None

    #     write_file = open('./Text/Grammar_tree.txt', 'w+')

    def __init__(self):
        self.nt_dict = {}  # {nt_name, nt_node}
        self.api_dict = {}  # {API_name, API_node}
        self.nt_list = []  # nt_name list
        self.api_list = []  # api_name list
        self.ck_list = []  # common knowledge
        self.root = None

    def build(self, file_name, api_document_name):
        grammar_string = self.read_grammar(file_name)

        log.log("Start building grammar tree...")
        for grammar in grammar_string:
            grammar_split = grammar.split(':=')

            # add nt
            nt = NTNode(grammar_split[0])
            self.add_nt(nt)

            # split each derivation
            derivations = grammar_split[1].split('|')

            for d in derivations:
                nt.derive_rule.append(d)
                # this derivation doesn't have API
                if '(' not in d:
                    elements = d.split(',')
                    nt.derivations.append(elements)
                else:
                    api = d.split('(')
                    api_name = api[0]

                    # normal function
                    if '.' not in api[1]:
                        api_parameters = api[1].replace(')', '').split(',')
                    # object's methods
                    else:
                        object_element = api[1].split('.')
                        api_parameters = object_element[0].replace(')', '').split(',') + [object_element[1]]

                    # set API code generation type
                    if api_name[0] == '_' and api_name[-1] == '_':
                        api_gen_type = 'common_knowledge'
                    elif api_name[-5:len(api_name)] == '_key_':
                        api_gen_type = 'keyword_arg'
                    else:
                        api_gen_type = 'norm'

                    # print(api_name, ' ', api_gen_type, ' ', api_parameters)

                    api_node = APINode(api_name, api_gen_type)
                    api_node.params = api_parameters
                    nt.derivations.append([api_name])
                    self.add_api(api_node)

        # remove duplicate element in sources
        for k in self.api_dict.keys():
            for p in self.api_dict[k].params:
                self.add_source(k, p)

        for k in self.nt_dict.keys():
            for der in self.nt_dict[k].derivations:
                for d in der:
                    self.add_source(k, d)

        self.set_source()

        log.log('Add API description...')
        self.add_api_document(api_document_name)

        log.log('Set nodes max formal children length')
        self.set_max_len()

        log.log('Grammar tree build finished.')

    def set_max_len(self):
        for i in self.nt_dict.keys():
            for f in self.nt_dict[i].derivations:
                if len(f) > self.nt_dict[i].max_child_len:
                    self.nt_dict[i].max_child_len = len(f)
        for i in self.api_dict.keys():
            for f in [self.api_dict[i].params]:
                if len(f) > self.api_dict[i].max_child_len:
                    self.api_dict[i].max_child_len = len(f)

    def add_api(self, api_node):
        self.api_dict[api_node.name] = api_node
        self.api_list.append(api_node.name)

    def add_api_document(self, api_document):
        api_file = open(api_document, 'r', encoding='utf-8').readlines()
        index = 0
        while index < len(api_file):
            name = api_file[index].replace('\n', '')
            input = api_file[index + 1][7:].replace('\n', '')
            ret = api_file[index + 2][8:].replace('\n', '')
            description = api_file[index + 3]
            description = description[13:].replace('\n', '')
            if name in self.api_dict:
                self.api_dict[name].input = input
                self.api_dict[name].ret = ret
                self.api_dict[name].description = description
            else:
                log.err(name + ': name not in api_dictionary')
            index += 5

    def add_nt(self, nt_node):
        if not self.root:
            self.root = nt_node.name
        self.nt_dict[nt_node.name] = nt_node
        self.nt_list.append(nt_node.name)

    def add_source(self, source, derivation):
        #         log.log('add_source ' + source + ' ' + derivation)
        if derivation in self.api_dict:
            self.api_dict[derivation].sources.append(source)
        elif derivation in self.nt_dict:
            self.nt_dict[derivation].sources.append(source)

    def set_source(self):
        for k in self.api_dict.keys():
            self.api_dict[k].sources = set(self.api_dict[k].sources)
        for k in self.nt_dict.keys():
            self.nt_dict[k].sources = set(self.nt_dict[k].sources)

    def build_test(self):
        log.test('Test ouput: ')
        log.test('API dictionary: api, [params], [sources]')
        for k in self.api_dict.keys():
            log.lprint(k, self.api_dict[k].params, self.api_dict[k].sources, self.api_dict[k].description, self.api_dict[k].generation_type)

        log.test('nt dictionary')
        log.test('nt dictionary: nt, [derivations], [sources]')
        for k in self.nt_dict.keys():
            log.lprint(k, self.nt_dict[k].derivations, self.nt_dict[k].sources, self.nt_dict[k].derive_rule)

    def read_grammar(self, file_name):
        # read grammar file
        log.log('Reading grammar file and pre-processing text...')
        grammar_file = open(file_name, 'r', encoding='utf-8').readlines()

        # Group grammar as terms
        grammar_list = []
        tmp_grammar = []
        for g in grammar_file:
            if g[0] == '#':
                continue
            else:
                if g[0] == '\n' or g == grammar_file[-1]:
                    grammar_list.append(tmp_grammar)
                    tmp_grammar = []
                else:
                    tmp_grammar.append(g)

        # Set grammar into string
        remove_list = []
        grammar_string = []
        for g in grammar_list:
            if len(g) == 0:
                remove_list.append(g)
            else:
                tmp = ''.join(g).replace('\n', '').replace('\t', '').replace(' ', '')
                grammar_string.append(tmp)
        for r in remove_list:
            grammar_list.remove(r)

        log.log("Grammar text preparation finished")

        return grammar_string

    def get_child(self, name):
        # log.log('get formal child list ...', name)
        if name in self.api_dict:
            return [self.api_dict[name].params]
        elif name in self.nt_dict:
            return self.nt_dict[name].derivations

    def get_formal_child_max_len(self, name):
        # log.log('get formal child length ...', name)
        if name in self.api_dict:
            return self.api_dict[name].max_child_len
        elif name in self.nt_dict:
            return self.nt_dict[name].max_child_len

    def get_node_type_by_name(self, name):
        if name in self.api_dict:
            return [self.api_dict[name], 'api']
        elif name in self.nt_dict:
            return [self.nt_dict[name], 'nt']
        else:
            return [None, 'api']