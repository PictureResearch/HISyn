import sys
sys.path.insert(0, '../../..')

import HISyn.tools.Log as log
from HISyn.tools.root_directory import root_dir


class nt:
    def __init__(self, name=''):
        self.name = '_' + name
        self.api = []
        self.derive_rule = []

    def display(self):
        print(self.name, '|', self.api, '|', self.derive_rule)


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
        self.api_type = ''
        self.ret = ''
        self.arg = ''
        self.caller = []
        self.method = []
        self.desc = ''
        self.derive_rule = ''
        self.arg_nt_list = []

    def display(self):
        print('name: ', self.name, '\ntype:', self.api_type, '\ncaller:', self.caller,
              '\nreturn:', self.ret, '\narg:', self.arg, '\nmethod:', self.method,
              '\ndesc:', self.desc, '\n')

    def name_modify(self):
        if self.api_type == 'keyword_arg':
            self.name += '_key_'
        elif self.api_type == 'common_knowledge':
            self.name = '_' + self.name + '_'

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
                tmp = nt(self.name + '_arg')
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
        self.root_nt = nt('root')

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
                    tmp[1] = tmp[1].replace(' ', '').replace('\t', '').replace('.', '_')
                self.api_lines.append(tmp)

    def add_api_to_dict(self, api):
        if api.name not in self.api_dict:
            self.api_dict[api.name] = api
        else:
            if not self.is_same_api(api, self.api_dict[api.name]):
                api.name += '_cO_pY'
                self.add_api_to_dict(api)

    def is_same_api(self, api1, api2):
        # self.name = name
        # self.api_type = ''
        # self.ret = ''
        # self.arg = ''
        # self.caller = []
        # self.method = []
        # self.desc = ''
        if api1.name == api2.name and api1.api_type == api2.api_type and \
                api1.ret == api2.ret and api1.arg == api2.arg and \
                api1.caller == api2.caller and api1.method == api2.method and \
                api1.desc == api2.desc:
            return True
        return False

    def set_api(self):
        tmp = API()
        for l in self.api_lines:
            if l[0] == 'name':
                if tmp.name:
                    self.add_api_to_dict(tmp)
                tmp = API(l[1])
            elif l[0] == 'type':
                if l[1]:
                    type = l[1].split('->')
                    if len(type) == 1:
                        tmp.api_type = type
                    else:
                        tmp.api_type = type[0]
                        tmp.caller = type[1].split(',')
                else:
                    tmp.api_type = 'norm'
            elif l[0] == 'return':
                tmp.ret = l[1].split('|')

            elif l[0] == 'argument':
                tmp.arg = l[1].split('|')
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
        self.add_api_to_dict(tmp)

    def set_nt(self):
        for k in self.api_dict.keys():
            api = self.api_dict[k]
            #     api.name_modify()
            for ret in api.ret:
                if ret in self.nt_dict:
                    self.nt_dict[ret].api.append(k)
                else:
                    self.nt_dict[ret] = nt(ret)
                    self.nt_dict[ret].api.append(k)
        #     api.display()
        # for k in self.nt_dict:
        #     self.nt_dict[k].display()

    def set_derive_rule(self):
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

    def create_grammar(self):
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

    def write_to_file(self, domain, file_name, text):
        file_name = root_dir + '/Documentation/' + domain + '/' + file_name
        file = open(file_name, 'w+', encoding='utf-8')
        file.write(text)
        file.close()

    def generate_grammar(self, domain, doc_file, grammar_file='grammar.txt'):
        self.read_doc(doc_file)
        self.pre_process()
        self.set_api()
        self.set_nt()
        self.set_derive_rule()
        self.add_root_nt()
        self.create_grammar()
        self.generate_api_doc(domain, doc_file)
        self.write_to_file(domain, grammar_file, self.grammar_text)

    def generate_api_doc(self, domain, doc_file):
        text = ''
        for k in self.api_dict:
            text += self.api_dict[k].name + '\n'
            text += 'input: ' + ', '.join(self.api_dict[k].arg) + '\nreturn:\ndescription:'
            text += self.api_dict[k].desc + '\n\n'
        self.write_to_file(domain, file_name='API_documents.txt', text=text)
