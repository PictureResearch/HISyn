# transform prefix-tree to code generation tree
# from HISyn.back_end.back_end_function_kit import is_list_in
import HISyn.tools.Log as log


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


class CG_tree_node:
    def __init__(self, name, tree):
        self.name = name
        self.child = []  # CG_tree_node
        self.formal_child = []
        self.is_complete = False
        self.tree = tree
        self.complete_index = None
        self.node_type = ''
        self.gg_node = None
        self.final_derive_rule = ''

    def set_derive_rule(self, gg):
        [node, node_type] = gg.get_node_type_by_name(self.name)
        self.node_type = node_type
        child_name_list = [i.name for i in self.child]
        log.test('formal:', self.formal_child, 'actual:', child_name_list)
        if node:
            self.gg_node = node
            if node_type == 'nt':
                log.test(node.derive_rule)
                if child_name_list in self.formal_child:
                    index = self.formal_child.index(child_name_list)
                    log.test(index, node.derive_rule[index])
                    self.final_derive_rule = node.derive_rule[index]
                # API replaced with API(arg), e.g. STRING(colon)
                else:
                    self.final_derive_rule = child_name_list[0]



class CG_tree:
    def __init__(self):
        self.root = CG_tree_node('root', self)
        self.is_valid_tree = True
        self.api_count = 0
        self.api_list = []

    def check_cgt_node_grammar(self, node, gg):
        name = node.name
        formal_child = gg.get_child(name)
        child_list = [n.name for n in node.child]

        if not child_list:
            return True

        max_formal_len = 0
        for f in formal_child:
            if len(f) > max_formal_len:
                max_formal_len = len(f)

        if len(child_list) > max_formal_len:
            return False

        if formal_child:
            if child_list in formal_child:
                for child in node.child:
                    if not self.check_cgt_node_grammar(child, gg):
                        return False

            else:
                flag = False
                for fc in formal_child:
                    # log.lprint("child list: ", child_list)
                    # log.lprint('formal child: ', fc)
                    if is_list_in(child_list, fc):
                        # log.lprint('true')
                        flag = True
                        for child in node.child:
                            if not self.check_cgt_node_grammar(child, gg):
                                return False
                    else:
                        # log.lprint('false')
                        continue
                if not flag:
                    return False
        return True

    def check_cgt_grammar(self, gg):
        for child in self.root.child:
            if not self.check_cgt_node_grammar(child, gg):
                return (False)
        return (True)

    def count_api(self, node, gg):
        node.tree = self
        for i in node.child:
            if i.name in gg.api_dict:
                self.api_list.append(i.name)
            self.count_api(i, gg)

    def set_api_list(self, node, gg):
        self.api_list.clear()
        self.count_api(node, gg)
        self.api_count = len(self.api_list)

    def prefix_to_cg(self, prefix_node, cg_node, gg):
        cg = cg_node

        if not prefix_node.name == 'root':
            cg = CG_tree_node(prefix_node.name, self)
            cg_node.child.append(cg)

        for k in prefix_node.child.keys():
            self.prefix_to_cg(prefix_node.child[k], cg, gg)

    def list_to_cg(self, path, gg):
        cg = self.root
        for i in path:
            tmp = CG_tree_node(i, self)
            cg.child.append(tmp)
            cg = tmp

    def set_tree_node(self, node):
        node.tree = self
        for i in node.child:
            self.set_tree_node(i)

    def display_go(self, node, level):
        log.lprint('--' * level + '|', node.name, '|', node.node_type, '|', node.final_derive_rule)
        for i in node.child:
            self.display_go(i, level + 1)

    def display(self):
        self.display_go(self.root, 0)

    def set_node_derive_rule(self, node, gg):
        node.set_derive_rule(gg)
        for i in node.child:
            self.set_node_derive_rule(i, gg)

    def set_cgt_derive_rule(self, gg):
        self.set_node_derive_rule(self.root.child[0], gg)

    def is_name_char(self, ch):
        if 'a' < ch < 'z' or 'A' < ch < 'Z' or ch == '_':
            return True
        return False

    def exact_func_index_match(self, expr, arg):
        if expr == arg:
            return 0
        for i in range(len(expr)-len(arg)+1):
            if expr[i:i+len(arg)] == arg:
                if i-1 >= 0:
                    if self.is_name_char(expr[i-1]):
                        continue
                if i + len(arg) < len(expr):
                    if self.is_name_char(expr[i+len(arg)]):
                        continue
                return i
        log.test('arg not found in expr', expr, arg)
        return -1

    def replace_api(self, expr, arg, api_type):
        if api_type == 'norm':
            return expr

        func_index = self.exact_func_index_match(expr, arg)
        if func_index == '-1':
            return 'error-expr'
        arg_index = func_index + len(arg)
        paren = []
        end_index = -1
        for i in range(arg_index, len(expr)):
            if expr[i] == '(':
                paren.append('(')
            elif expr[i] == ')':
                paren.pop(-1)
            if len(paren) == 0:
                end_index = i + 1
                break
        print(expr[arg_index:end_index])
        if api_type == 'keyword_arg':
            # remove parenthesis of argument
            expr = expr[0:arg_index] + expr[arg_index + 1:end_index-1] + expr[end_index:len(expr)]
            # replace API_key to API
            expr = expr[0:func_index] + arg[0:-5] + '=' + expr[arg_index:]
            return expr
        # api_type == 'common_knowledge
        else:
            expr = expr[0:arg_index] + expr[end_index:len(expr)]
            expr = expr[0:func_index] + arg[1:-1] + expr[arg_index:]
        return expr

    def rewrite_node(self, expr, node):
        log.test(expr, node.name, node.final_derive_rule)
        if node.node_type == 'nt':
            if node.final_derive_rule == 'empty':
                replacement = ''
            else:
                replacement = node.final_derive_rule

            if node.name + ',' in expr and replacement == '':
                replace_index = self.exact_func_index_match(expr, node.name)+1
                if replace_index == -1:
                    return 'error-expr'
                new_expr = expr[0:replace_index] + expr[replace_index + len(node.name) + 1:]
            elif (',' + node.name in expr or '.' + node.name in expr) and replacement == '':
                replace_index = self.exact_func_index_match(expr, node.name)-1
                if replace_index == -1:
                    return 'error-expr'
                new_expr = expr[0:replace_index] + expr[replace_index + len(node.name) + 1:]
            else:
                # new_expr = expr.replace(node.name, replacement)
                replace_index = self.exact_func_index_match(expr, node.name)
                if replace_index == -1:
                    return 'error-expr'
                new_expr = expr[0:replace_index] + replacement + expr[replace_index + len(node.name):]

        else:
            if node.gg_node:
                # if node.gg_node.generation_type == 'keyword_arg':
                new_expr = self.replace_api(expr, node.name, node.gg_node.generation_type)
                if new_expr == 'error-expr':
                    return new_expr
                # elif node.gg_node.generation_type == 'common_knowledge':
                #     new_expr = self.replace_ck_api(expr, node.name)
                # else:
                #     new_expr = expr
            else:
                new_expr = expr

        for i in node.child:
            new_expr = self.rewrite_node(new_expr, i)
        return new_expr

    def convert_to_expr(self, gg):
        self.set_cgt_derive_rule(gg)
        expr = self.root.child[0].final_derive_rule
        for i in self.root.child[0].child:
            expr = self.rewrite_node(expr, i)
            if expr == 'error-expr':
                return None
        expr = expr.replace('_cO_pY', '').replace('_c', '')
        return expr
