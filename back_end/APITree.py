import HISyn.tools.Log as log

class API_tree_node:
    def __init__(self, name):
        self.name = name
        self.child = []  # API_tree_node


class API_tree:
    def __init__(self):
        self.root = API_tree_node('root')

    def cg_to_api(self, cg_node, api_node, gg):
        api = api_node

        if cg_node.name in gg.api_dict or '(' in cg_node.name:
            api = API_tree_node(cg_node.name)
            api_node.child.append(api)

        for k in cg_node.child:
            self.cg_to_api(k, api, gg)

    def display(self, node, level):
        log.lprint('--' * level + '|', node.name)
        for i in node.child:
            self.display(i, level + 1)


    def convert_to_expression(self, node, expression):
        if len(node.child) > 1:
            for c in node.child:
                if not '(' in c.name:
                    expression = expression + c.name + '('
                    expression = self.convert_to_expression(c, expression)
                    if c != node.child[-1]:
                        expression += '), '
                    else:
                        expression += ')'
                else:
                    expression = expression + c.name
                    expression = self.convert_to_expression(c, expression)
                    if c != node.child[-1]:
                        expression += ', '

        elif len(node.child) == 1:
            if not '(' in node.child[0].name:
                expression = expression + node.child[0].name + '('
                expression = self.convert_to_expression(node.child[0], expression)
                expression += ')'
            else:
                expression = expression + node.child[0].name
                expression = self.convert_to_expression(node.child[0], expression)

        else:
            pass
        return expression

    def generate_expression(self):
        expr = ''
        return self.convert_to_expression(self.root, expr)