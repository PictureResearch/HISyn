import HISyn.tools.Log as log

class Prefix_tree_node:
    def __init__(self, name):
        self.name = name
        self.child = {}
        self.path_index = []
        self.depth = 0

    def is_list_in(self, l1, l2):
        for n in l1:
            if n not in l2:
                if '(' not in n:
                    return False
                else:
                    tmp = n[0:n.index('(')]
                    if tmp not in l2:
                        return False
        return True

    def check_grammar(self, gg):
        # log.test('prefix node grammar checking...', self.name)
        formal_child = gg.get_child(self.name)
        child_list = list(self.child.keys())

        if not child_list:
            return True

        max_formal_len = gg.get_formal_child_max_len(self.name)
        if len(child_list) > max_formal_len:
            return False

        if formal_child:
            if child_list in formal_child:
                for child in child_list:
                    if not (self.child[child].check_grammar(gg)):
                        return False
            else:
                flag = False
                for fc in formal_child:
                    if self.is_list_in(child_list, fc):
                        flag = True
                        for child in child_list:
                            if not (self.child[child].check_grammar(gg)):
                                return False
                    else:
                        continue
                if not flag:
                    return False
        return True





class Prefix_tree:
    def __init__(self):
        self.root = Prefix_tree_node('root')
        self.api_count = 0

    def count_api(self, node, api_dict):
        count = 0
        for i in node.child.keys():
            if i in api_dict:
                count += 1
            tmp = self.count_api(node.child[i], api_dict)
            if tmp:
                count += tmp
        return count

    def add_path(self, path_0, index, node):
        path = list(path_0)
        if path:
            path_node = path.pop(0)
        else:
            return

        if not path_node in node.child:
            node.child[path_node] = Prefix_tree_node(path_node)
            node.child[path_node].path_index.append(index)
        else:
            node.child[path_node].path_index.append(index)
        node.child[path_node].depth = node.depth + 1
        self.add_path(path, index, node.child[path_node])

    def check_grammar(self, gg):
        for key in self.root.child.keys():
            if not self.root.child[key].check_grammar(gg):
                return False
        return True

    def display(self):
        self.display_go(self.root, 0)

    def display_go(self, node, level):
        log.lprint('--' * level + '|', node.name, '| path_len:', len(node.path_index), '| depth:', node.depth, ' | api: ', self.api_count)
        for i in node.child.keys():
            self.display_go(node.child[i], level + 1)

