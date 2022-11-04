import sys
sys.path.insert(0, '../../..')

import HISyn.tools.Log as log
from HISyn.tools.root_directory import root_dir


class NT:
    def __init__(self, name=''):
        self.name = '_' + name
        self.original_name  = name
        self.api = []       # non-terminal := API(kw-nt...)
        self.method = []    # non-terminal_method := API(kw-nt) | ...
        self.keyword_arg = []       # non-terminal_keyword := API_key_(arg) -- api and key-arg are mapped with index
        self.arg = []       # non-terminal := input_type
        self.non_term = []        # non-terminal := nt | nt | ...
        self.derive_rule = []

    def display(self):
        print(self.name,
              # '|api:', [a.name for a in self.api],
              '\n|api:', [a for a in self.api],
              '\n|method:', self.method,
              '\n|key_arg:', self.keyword_arg,
              '\n|arg:', self.arg,
              '\n|nt:', self.non_term,
              '\n|dr:', self.derive_rule, '\n')


class API:
    #     def __init__(name, api_type, ret, arg, method, desc):
    #         self.name = name
    #         self.api_type = api_type
    #         self.ret = ret
    #         self.arg = arg
    #         self.method = method
    #         self.desc = desc

    def __init__(self, name=''):
        self.name = name
        self.original_name = ''
        self.api_type = ''
        self.ret = ''
        self.arg = ''
        self.cls = []   # class
        self.caller = []
        self.method = []
        self.desc = ''
        self.derive_rule = ''
        self.arg_nt_list = []

    def display(self):
        print('name: ', self.name, '\noriginal_name:', self.original_name, '\ntype:', self.api_type, '\ncaller:', self.caller, '\nclass:', self.cls,
              '\nreturn:', self.ret, '\narg:', self.arg, '\nmethod:', self.method,
              '\ndesc:', self.desc, '\n')

    def name_modify(self):
        if self.api_type == 'keyword_arg':
            self.name += '_key_'
        elif self.api_type == 'literal':
            self.name = '_' + self.name + '_'
        elif self.api_type == 'class':
            pass

    def set_arg(self):
        for idx in range(len(self.arg)):
            tmp = self.arg[idx].split(',')
            for i in range(len(tmp)):
                if tmp[i] != 'empty' and tmp[i] != '':
                    tmp[i] = '_' + tmp[i]
                    self.arg_nt_list.append(tmp[i])
            self.arg[idx] = ','.join(tmp)
        # print('arg:', self.arg)

        for idx in range(len(self.method)):
            tmp = self.method[idx].split(',')
            for i in range(len(tmp)):
                if tmp[i] != 'empty' and tmp[i] != '':
                    tmp[i] = '_' + tmp[i]
                    self.arg_nt_list.append(tmp[i])
            self.method[idx] = ','.join(tmp)
        # print('method:', self.method)

    def set_derive_rule(self, nt_dict=None):
        #         print(self.arg)
        if len(self.arg) == 1:
            rule = self.name + '(' + self.arg[0] + ')'
        elif len(self.arg) == 2 and 'empty' in self.arg:
            empty_index = self.arg.index('empty')
            # tmp = []
            # for arg in self.arg:
            #     if arg != 'empty':
            #         tmp.append( '_' + arg)
            # self.arg = tmp
            rule = self.name + '(' + '|'.join(self.arg[0:empty_index] + self.arg[empty_index + 1:]) + ')'
        else:
            if nt_dict:
                #                 print(self.arg)
                tmp = NT(self.name + '_arg')
                log.test('arg:', self.arg)
                if 'empty' not in self.arg:
                    tmp.derive_rule = ['|'.join(self.arg)]
                    # print(tmp.derive_rule)
                    nt_dict[tmp.name] = tmp
                    # nt_dict[tmp.name].display()
                    rule = self.name + '(' + tmp.name + ')'
                else:
                    empty_index = self.arg.index('empty')
                    log.test('empty index:', empty_index)
                    tmp.derive_rule = ['|'.join(self.arg[0:empty_index] + self.arg[empty_index + 1:])]
                    # print(tmp.derive_rule)
                    nt_dict[tmp.name] = tmp
                    # nt_dict[tmp.name].display()
                    rule = self.name + '(' + tmp.name + ')'
            else:
                rule = self.name + '(' + '|'.join(self.arg) + ')'
        if self.method:
            if 'empty' not in self.method:
                rule += '.' + '|'.join(self.method)
            else:
                empty_index = self.method.index('empty')
                log.test('method empty index:', empty_index)
                tmp_rule = '|'.join(self.method[0:empty_index] + self.method[empty_index + 1:])
                # print('tmp_rule: ', tmp_rule)
                rule += '.' + tmp_rule
        #         print('rule:', rule)
        self.derive_rule = rule


class GrammarGenerator:
    def __init__(self):
        self.api_doc = ''
        self.api_lines = []
        self.api_dict = {}  # name:API_doc object
        self.nt_dict = {}  # non-terminals: API name
        self.empty_api_list = []  # API with 'empty' argument
        self.empty_method_list = []  # API with 'empty' method
        self.grammar_text = ''
        self.rename_api_dict = {}   # API_original_name: API_original_name_(copy)*
        self.root_nt = NT('root')
        self.object_nt = NT('object')
        self.general_type = [
            'np.array',
            'python_var',
            'python_dict',
            'python_float',
            'python_string',
            'bool',
            'python_int',
            'python_str'
            # 'estimator',
            # 'predictor',
            # 'transformer',
            # 'model'
        ]
        self.nt_dict['root'] = self.root_nt
        self.nt_dict['object'] = self.object_nt
        self.root_nt.non_term.append(self.object_nt.name)
        self.cls_nt_dict = {}   # class: class_nt
        self.general_type_literal_list = [] # stores general type literals

    def add_root_nt(self):
        arg_nt_list = []
        for k in self.api_dict.keys():
            arg_nt_list += self.api_dict[k].arg_nt_list
        print('arg_nt_list:', arg_nt_list)

        root_nt_list = []
        for k in self.nt_dict.keys():
            if self.nt_dict[k].name not in arg_nt_list:
                root_nt_list.append(self.nt_dict[k].name)
        print('root_nt_list:', root_nt_list)

        for r in root_nt_list:
            self.root_nt.derive_rule.append(r)

    def read_doc(self, file_name):
        self.api_doc = open(file_name, 'r', encoding='utf-8').readlines()

    def pre_process(self):
        for l in self.api_doc:
            tmp = l.replace('\n', '')
            if tmp and tmp[0] != '#':
                tmp = tmp.split(':')
                if tmp[0] != 'description' and tmp[1]:
                    tmp[1] = tmp[1].replace(' ', '')
                self.api_lines.append(tmp)

    def add_api_to_dict(self, api):
        # print('--add api:', api.name)
        if api.api_type not in ['class', 'module'] and '<' not in api.name and '>' not in api.name:
            api.name += '_<' + api.cls + '>'
        if api.name not in self.api_dict:
            if '_c0pY' in api.name:
                origin_name = api.name.replace('_c0pY', '')
                if origin_name in self.rename_api_dict:
                    self.rename_api_dict[origin_name].append(api)
                else:
                    self.rename_api_dict[origin_name] = [api]
            self.api_dict[api.name] = api
        else:
            if '<' in api.name and '>' in api.name:
                api.name += '_c0pY'
                self.add_api_to_dict(api)
            if not self.is_same_api(api, self.api_dict[api.name]):
                api.name += '_<' + api.cls + '>'
                self.add_api_to_dict(api)

    def is_same_api(self, api1, api2):
        # self.name = name
        # self.api_type = ''
        # self.ret = ''
        # self.arg = ''
        # self.caller = []
        # self.method = []
        # self.desc = ''
        if api1.name == api2.name and \
                api1.api_type == api2.api_type and \
                api1.ret == api2.ret and \
                api1.arg == api2.arg and \
                api1.method == api2.method and \
                api1.desc == api2.desc:
                # api1.caller == api2.caller and \

                    return True
        return False

    def set_api(self):
        tmp = API()
        for l in self.api_lines:
            if l[0] == 'name':
                if tmp.name:
                    tmp.original_name = tmp.name
                    self.add_api_to_dict(tmp)
                tmp = API(l[1])
            elif l[0] == 'type':
                if l[1]:
                    tmp.api_type = l[1]
                    #     .split('->')
                    # if len(type) == 1:
                    #     tmp.api_type = type
                    # else:
                    #     tmp.api_type = type[0]
                    #     tmp.caller = type[1].split(',')
                else:
                    tmp.api_type = 'norm'

            elif l[0] == 'return':
                tmp.ret = l[1].split('|')

            elif l[0] == 'caller':
                tmp.caller = l[1].split('|')
                if len(tmp.caller) > 1:
                    print('has multiple caller:', tmp.name, tmp.caller)

            elif l[0] == 'class':
                tmp.cls = l[1]

            elif l[0] == 'argument':
                tmp.arg = l[1].split('|')
                for i in range(len(tmp.arg)):
                    tmp.arg[i] = tmp.arg[i].split(',')
                if 'empty' in tmp.arg:
                    self.empty_api_list.append(tmp)

            elif l[0] == 'method' and l[1]:
                tmp.method = l[1].split('|')
                if 'empty' in tmp.method:
                    self.empty_method_list.append(tmp)

            elif l[0] == 'description':
                tmp.desc = l[1]

            else:
                continue

        # add last API
        tmp.original_name = tmp.name
        self.add_api_to_dict(tmp)

    def add_general_type_literal(self):
        for name in self.general_type:
            tmp = API()
            tmp.name = name
            tmp.api_type = 'type_literal'
            tmp.original_name = name
            tmp.arg = [[name]]
            self.api_dict[name] = tmp

            # add nt and derive rule
            if name not in self.nt_dict:
                nt = self.add_nt(name, derive_rule=name)



    def add_nt(self, name, derive_rule=None, api=None, method=None, nt=None, keyword_arg=None):
        # log.test('add nt:', name)
        if name not in self.nt_dict:
            tmp = NT(name)
            self.nt_dict[name] = tmp
        else:
            tmp = self.nt_dict[name]
        if method:
            # log.test('add_nt-method:', method)
            tmp.method = method
        if api:
            # log.test('add_nt-api', api)
            tmp.api.append(api)
        if nt:
            # log.test('add_nt-nt:', nt)
            tmp.non_term = nt
        if keyword_arg:
            # log.test('add_nt-key-arg:', keyword_arg)
            tmp.keyword_arg.append(keyword_arg)
        if derive_rule:
            tmp.derive_rule.append(derive_rule)
        return tmp

    def update_nt(self, name, derive_rule=None, api=None, method=None, nt=None, keyword_arg=None):
        tmp = self.nt_dict[name]
        if method:
            tmp.method = method
        if api:
            tmp.api.append(api)
        if nt:
            tmp.api.append(nt)
        if keyword_arg:
            tmp.keyword_arg.append(keyword_arg)
        if derive_rule:
            tmp.derive_rule.append(derive_rule)

    # check if the keyword name has '_copy' tag
    def check_arg_by_origin_name(self, api, arg):
        # log.test('check_name:', api.name, arg)
        if arg in self.rename_api_dict:
            api_list = self.rename_api_dict[arg]
            for a in api_list:
                # log.test('-check_name:', a.caller, api.original_name)
                if api.original_name in a.caller:
                    return a.name
        else:
            return None

    def set_arg(self, api):
        if len(api.arg) == 1:
            nt_keyword_arg = []
            for arg in api.arg[0]:
                if arg == '':
                    return ['']
                arg_name = arg + '_<' + api.cls + '>'
                new_arg = self.check_arg_by_origin_name(api, arg_name)
                if not new_arg:
                    new_arg = arg_name
                nt = self.add_nt(new_arg)
                nt_keyword_arg.append(nt.name)
        elif len(api.arg) > 1:  # create a separate nt
            nt_arg = api.name + '_arg'
            nt_keyword_arg = nt_arg
            keyword_arg_list = []
            for args in api.arg:
                tmp = []
                for arg in args:
                    arg_name = arg + '_<' + api.cls + '>'
                    new_arg = self.check_arg_by_origin_name(api, arg_name)
                    if not new_arg:
                        new_arg = arg_name
                    nt = self.add_nt(new_arg)

                    # self.add_nt(arg + '_<' + api.cls + '>')
                    tmp.append(nt.name)
                keyword_arg_list.append(tmp)
            self.add_nt(nt_arg, nt=keyword_arg_list)
        return nt_keyword_arg

    # def create_nt(self):
    #     self.create_nt_class_method()
    #     self.create_key_arg()

    def create_nt(self):
        for k in self.api_dict.keys():
            api = self.api_dict[k]

            if api.api_type == 'class':
                # the return of a class is an object
                nt_return = api.name + '_object'
                nt_keyword_arg = self.set_arg(api)
                # if len(api.arg) == 1:
                #     nt_keyword_arg = []
                #     for arg in api.arg[0]:
                #         self.add_nt(arg+'_<'+api.cls+'>')
                #         nt_keyword_arg.append(arg+'_<'+api.cls+'>')
                # elif len(api.arg) > 1:  # create a separate nt
                #     nt_arg = api.name + '_arg'
                #     nt_keyword_arg = nt_arg
                #     keyword_arg_list = []
                #     for args in api.arg:
                #         tmp = []
                #         for arg in args:
                #             self.add_nt(arg+'_<'+api.cls+'>')
                #             tmp.append(arg+'_<'+api.cls+'>')
                #         keyword_arg_list.append(tmp)
                #     self.add_nt(nt_arg, nt=keyword_arg_list)

                nt = self.add_nt(nt_return, api=api.name, keyword_arg=nt_keyword_arg)
                self.object_nt.non_term.append(nt.name)
                self.cls_nt_dict[api.cls] = nt

                # nt_caller = api.caller[0]
                # nt_method = api.name + '_method'
                # nt_arg = api.name + '_arg'

                # self.add_nt(nt_name, )
                # self.add_nt(nt_caller, api=api)
                # self.add_nt(nt_method, method=api.method)

                # the construct arg is keyword_arg
                # if len(api.arg) == 1:
                #     self.set_nt(api.name, keyword_arg=api.arg[0])
                #     for arg in api.arg[0]:
                #         self.add_nt(arg+'_<'+api.cls+'>')
                # elif len(api.arg) > 1:  # create a separate nt
                #     nt_arg = api.name + '_arg'
                #     self.add_nt(nt_arg)

            elif api.api_type == 'module':
                nt_return = api.name + '_object'
                print('--nt return',nt_return)
                nt_keyword_arg = self.set_arg(api)
                nt = self.add_nt(nt_return, api=api.name, keyword_arg=nt_keyword_arg)
                self.object_nt.non_term.append(nt.name)
                self.cls_nt_dict[api.cls] = nt


            elif api.api_type == 'method':
                nt_return = api.ret
                nt = None
                if api.cls in api.ret or api.ret[0] == 'self':
                    nt_return = api.cls + '_object'
                    # nt_return = self.cls_nt_dict[api.cls].name
                    nt_keyword_arg = self.set_arg(api)
                    nt = self.add_nt(nt_return, keyword_arg=nt_keyword_arg)
                    nt.api.append(''.join([nt.name, '{.}', api.name]))
                else:
                    if api.ret[0] in self.general_type:
                        nt_return = api.ret[0]
                        nt_keyword_arg = self.set_arg(api)
                        nt = self.add_nt(nt_return, keyword_arg=nt_keyword_arg)

                        # create general type literal
                        if nt_return not in nt.derive_rule:
                            nt.derive_rule.append(nt_return)
                        if nt_return not in self.api_dict:
                            self.general_type_literal_list.append(nt_return)

                        nt.api.append(''.join([self.cls_nt_dict[api.cls].name, '{.}', api.name]))
                    elif not api.ret[0]:
                        nt_return = 'function'
                        nt_keyword_arg = self.set_arg(api)
                        nt = self.add_nt(nt_return, keyword_arg=nt_keyword_arg)
                        nt.api.append(''.join([self.cls_nt_dict[api.cls].name, '{.}', api.name]))
                    if nt and nt.name not in self.root_nt.non_term:
                        self.root_nt.non_term.append(nt.name)

        for k in self.api_dict.keys():
            api = self.api_dict[k]
            if api.api_type == 'literal' and 'c0pY' in api.name:
                print(api.name)
                for caller_name in api.caller:
                    caller =  self.api_dict[caller_name + '_<' + api.cls + '>']
                    for arg in caller.arg:
                        for i in range(len(arg)):
                            inner_arg = arg[i]
                            if inner_arg == api.original_name:
                                # copy_count = k.count('_c0pY')
                                copies = k[k.index('_c0pY'):]
                                arg[i] = inner_arg + copies

        log.log('Set keyword arguments:')
        for k in self.api_dict.keys():
            api = self.api_dict[k]

            if api.api_type == 'keyword_arg':
                # log.test('--key_word: ', api.name, api.cls, api.caller)
                nt = self.get_key_arg_nt(api)

                # empty_count = 0
                for args in api.arg:
                    if 'empty' in args:
                        nt.arg.append('empty')
                        # empty_count += 1

                # add nt: _keyword_arg:
                nt_arg_name = api.name + '_arg'
                nt_arg = self.add_nt(nt_arg_name)
                nt.arg.append(api.name + '{=}' + nt_arg.name)

                for args in api.arg:
                    tmp = []
                    if 'empty' in args:
                        continue
                    for i in range(len(args)):
                        a = args[i]
                        copies = ''
                        if '_c0pY' in a:
                            copies = a[a.index('_c0pY'):]
                            a = a[:a.index('_c0pY')]
                            args[i] = a
                        print('--keyword:', a)
                        if a in self.general_type:
                            tmp.append('_' + a)
                        elif a + '_<' + api.cls + '>' in self.api_dict and \
                                self.api_dict[a + '_<' + api.cls + '>'].api_type == 'literal':
                            print('---keyword:', a)
                            tmp.append(a + '_<' + api.cls + '>' + copies)
                        else:
                            tmp.append(a)

                        nt_arg.arg.append(','.join(tmp))

                #     else:
                #         tmp = []
                #         # for args in api.arg:
                #         print('--args:', args)
                #         if len(args) >= 1:
                #             for a in args:
                #                 print('--keyword:', a)
                #                 if a in self.general_type:
                #                     tmp.append('_' + a)
                #                 elif a + '_<'+api.cls+'>' in self.api_dict and \
                #                         self.api_dict[a + '_<'+api.cls+'>'].api_type == 'literal':
                #                     print('---keyword:', a)
                #                     tmp.append(a + '_<'+api.cls+'>')
                #                 else:
                #                     tmp.append(a)
                #
                #             nt.arg.append(api.name + '{=}' + ','.join(tmp))

        for k in self.nt_dict.keys():
            self.nt_dict[k].display()

    def get_caller_nt(self, api):
        caller_nt = []
        for c in api.caller:
            if c == api.cls:
                caller_nt.append(self.nt_dict[api.cls + '_object'])
            else:
                caller_nt.append(self.nt_dict[c + '_<' + api.cls + '>'])
        return caller_nt

    def get_key_arg_nt(self, api):
        if '_c0pY' in api.name:
            self.add_nt(api.name)
        return self.nt_dict[api.name]

    def set_derive_rule(self):
        for k in self.nt_dict.keys():
            nt = self.nt_dict[k]
            if nt.arg:  # this nt refers to keyword_arg api
                for arg in nt.arg:
                    nt.derive_rule.append(arg)
            elif nt.api: # nt refers to class or method or module
                for i, api in enumerate(nt.api):
                    if not nt.keyword_arg:
                        continue
                    arg = ','.join(nt.keyword_arg[i])
                    expr = api + '(' + arg + ')'
                    if api in self.api_dict and self.api_dict[api].api_type == 'module':
                        expr = api
                    nt.derive_rule.append(expr)
            elif nt.non_term:
                for non_term in nt.non_term:
                    nt.derive_rule.append(non_term)

        for k in self.nt_dict.keys():
            self.nt_dict[k].display()

    def create_grammar(self):
        # add notes
        self.grammar_text = '# _non-terminal -> return types or keyword_arg' \
               '\n# api_<class-tag> -> class or methods' \
               '\n# {symbols} and () parenthesis -> part of rules' \
               '\n\n'

        # add other rules
        for k in self.nt_dict:
            tab_num = int(len(self.nt_dict[k].name) / 7) + 2
            self.grammar_text += self.nt_dict[k].name + '\t:=\t' + self.nt_dict[k].derive_rule[0] + '\n'
            if len(self.nt_dict) > 0:
                for rule in self.nt_dict[k].derive_rule[1:]:
                    self.grammar_text += '\t' * tab_num + '|\t' + rule + '\n'
            self.grammar_text += '\n'

    def write_to_file(self, domain, file_name, text):
        file_name = root_dir + '/Documentation/' + domain + '/' + file_name
        file = open(file_name, 'w+', encoding='utf-8')
        file.write(text)
        file.close()


############## below are old functions ##############
    def set_nt_old(self):
        for k in self.api_dict.keys():
            api = self.api_dict[k]
            #     api.name_modify()
            for ret in api.ret:
                if ret in self.nt_dict:
                    self.nt_dict[ret].api.append(k)
                else:
                    self.nt_dict[ret] = NT(ret)
                    self.nt_dict[ret].api.append(k)
        #     api.display()
        # for k in self.nt_dict:
        #     self.nt_dict[k].display()

    def set_derive_rule_old(self):
        for k in self.api_dict.keys():
            api = self.api_dict[k]
            api.name_modify()
            api.set_arg()
            api.set_derive_rule(nt_dict=self.nt_dict)

        for k in self.nt_dict:
            tmp = []
            for i in self.nt_dict[k].api:
                if self.nt_dict[k].api and not self.nt_dict[k].derive_rule:
                    tmp.append(self.api_dict[i].derive_rule)
            if tmp:
                self.nt_dict[k].derive_rule = tmp
            # print(self.nt_dict[k].name, self.nt_dict[k].derive_rule)

        for i in self.empty_api_list:
            if i.api_type == 'keyword_arg':
                for ret in i.ret:
                    if 'empty' not in self.nt_dict[ret].derive_rule:
                        self.nt_dict[ret].derive_rule.insert(0, 'empty')
                # self.nt_dict[i.ret].display()

        for i in self.empty_method_list:
            for m in i.method:
                if 'empty' != m:
                    self.nt_dict[m[1:]].derive_rule.insert(0, 'empty')
                    # self.nt_dict[m[1:]].display()

    def create_grammar_old(self):
        # add root nt rule
        self.grammar_text = self.root_nt.name + '\t:=\t' + self.root_nt.derive_rule[0] + '\n'
        if len(self.root_nt.derive_rule) > 0:
            for rule in self.root_nt.derive_rule[1:]:
                self.grammar_text += '\t' + '|\t' + rule + '\n'
            self.grammar_text += '\n'

        # add other rules
        for k in self.nt_dict:
            tab_num = int(len(self.nt_dict[k].name) / 7) + 2
            self.grammar_text += self.nt_dict[k].name + '\t:=\t' + self.nt_dict[k].derive_rule[0] + '\n'
            if len(self.nt_dict) > 0:
                for rule in self.nt_dict[k].derive_rule[1:]:
                    self.grammar_text += '\t' * tab_num + '|\t' + rule + '\n'
            self.grammar_text += '\n'

    def generate_grammar(self, domain, doc_file, grammar_file='grammar.txt'):
        self.read_doc(doc_file)
        self.pre_process()
        self.set_api()
        self.create_nt()
        self.add_general_type_literal()
        self.set_derive_rule()
        # self.add_root_nt()
        self.create_grammar()
        self.generate_api_doc(domain, doc_file)
        self.write_to_file(domain, grammar_file, self.grammar_text)


    def generate_api_doc(self, domain, doc_file=None):
        text = ''
        # for k in self.api_dict:
        #     print(([', '.join(arg) for arg in self.api_dict[k].arg]))
        for k in self.api_dict:
            api = self.api_dict[k]
            text += 'name: ' + api.name + '\n'
            text += 'original_name: ' + api.original_name + '\n'
            text += 'type: ' + api.api_type + '\n'
            text += 'input: ' + '|'.join([', '.join(arg) for arg in api.arg]) + '\nreturn:\ndescription:'
            text += api.desc + ' ' + api.original_name + '\n\n'
        self.write_to_file(domain, file_name='API_documents.txt', text=text)
