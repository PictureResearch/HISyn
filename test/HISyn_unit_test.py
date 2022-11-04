import unittest

from HISyn.main_new import run_HISyn
from HISyn.tools.root_directory import root_dir


def check_result(expr_list, domain, index):
    code_file = open(root_dir + '/Documentation/' + domain + '/code_new.txt', encoding='utf-8')
    codes = code_file.readlines()

    if domain == 'TextEditing':
        for i in range(len(expr_list)):
            expr_list[i] = expr_list[i].replace('1st', '1').replace('2nd', '2').replace('3rd', '3').replace('4th',
                                                                                                            '4').replace(
                '5th', '5').replace('6th', '6').replace('7th', '7').replace('8th', '8').replace('10th',
                                                                                                '10').replace('1()',
                                                                                                              '1').replace(
                '80th', '80')

        code = codes[index]

        expr_lower_list = [n.lower().replace(' ', '') for n in expr_list]
        code_compare = code.lower().replace(' ', '').replace('\n', '')

        result = code_compare in expr_lower_list

        if not result:
            if 'start()' in code_compare:
                if (code_compare.replace('start()', 'position(before(linetoken()),all())')) in expr_lower_list:
                    result = True
                elif (code_compare.replace('start()', 'position(before(string()),all())')) in expr_lower_list:
                    result = True

    elif domain == 'Flight':
        code = codes[index]

        expr_lower_list = [n.lower().replace(' ', '') for n in expr_list]
        code_compare = code.lower().replace(' ', '').replace('\n', '')

        result = code_compare in expr_lower_list

        if not result:
            if code_compare.replace('eq_departs_imp', 'eq_departs') in expr_lower_list or \
                    code_compare.replace('eq_class_imp', 'eq_class') in expr_lower_list:
                if domain == 'ASTMatcher':
                    result = True

    else:
        code = codes[index]


        expr_lower_list = [n.lower().replace(' ', '').replace('_c', '') for n in expr_list]
        code_compare = code.lower().replace(' ', '').replace('\n', '')


        result = code_compare in expr_lower_list
    code_file.close()

    return result

class MyTestCase(unittest.TestCase):
    def test_text_editing(self):
        domain = 'TextEditing'
        index = 0
        [min_expr, expr_list] = run_HISyn(domain, index=index)
        result = check_result(expr_list, domain, index)
        self.assertTrue(result)

    def test_flight(self):
        domain = 'Flight'
        index = 0
        [min_expr, expr_list] = run_HISyn(domain, index=index)
        result = check_result(expr_list, domain, index)
        self.assertTrue(result)

    def test_ASTMatcher(self):
        domain = 'ASTMatcher'
        index = 1
        [min_expr, expr_list] = run_HISyn(domain, index=index)
        result = check_result(expr_list, domain, index)
        self.assertTrue(result)

    def test_sklearn(self):
        domain = 'sklearn'
        index = 0
        [min_expr, expr_list] = run_HISyn(domain, index=index)
        result = check_result(expr_list, domain, index)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
