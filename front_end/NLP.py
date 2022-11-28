#################################################################
# NLP class definition
# Include tokens, dependency edges and parsing processes.
#################################################################


from stanfordnlp.server import CoreNLPClient
import os

import HISyn.tools.Log as log
from HISyn.tools.root_directory import root_dir
from HISyn.tools.system_operations import check_sys_proc_exists_by_name
from HISyn.tools.root_directory import root_dir


# annotator_list = ['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'parse', 'depparse']
# client = CoreNLPClient(annotators=annotator_list, timeout=60000, memory='8G')

class RootToken:
    def __init__(self):
        self.word = 'root'
        self.pos = ''
        self.ner = ''
        self.lemma = ''


class RootEdge:
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.dep = 'root'



class Token:
    def __init__(self, token):
        self.word = token.word
        self.pos = token.pos
        self.ner = token.ner
        self.lemma = token.lemma
        self.dep = []
        self.mapping = []
        self.mapping_vote = []
        self.modifiers = []
        self.final_mapping = None


class Dependency:
    def __init__(self, edge):
        self.source = edge.source - 1
        self.target = edge.target - 1
        self.dep = edge.dep
        self.paths = []
        self.prep_mapping = []
        self.api_paths = []


class NLParsing:
    def __init__(self, nlp_server=False):
        self.text = ''
        self.annotate = ''
        self.sentence = ''
        self.token = []
        self.dependency = []
        self.root = None
        self.modifier_group = []
        self.ner_mapping_dict = {}
        self.start_server = not nlp_server
        if nlp_server:
            if self.check_nlp_server():
                self.start_server = True


    def check_nlp_server(self):
        log.log('Check NLP server status...')
        if check_sys_proc_exists_by_name('edu.stanford.nlp.pipeline.StanfordCoreNLPServer'):
            log.log('NLP server already started!')
            return False
        else:
            log.log('NLP server is not started, a temporary server will created and closed after synthesis.\n '
                   'If you prefer using faster NLP service, please follow the instructions in the\n'
                    '\tthird_party_pkgs\n'
                   'folder and start NLP service via following bash commands:\n'
                   '\tsh start_nlp_server.sh')
            return True


    def preprocessing(self,text, domain):
        if domain == 'Flight':
            text = text.replace('one way ','').replace('washington dc', 'washington').replace('san francisco', 'francisco').replace('san jose', 'jose').replace('fort worth', 'worth').replace('worth texas', 'worth').replace('california', '').replace('pennsylvania', '').replace('colorado', '').replace('georgia', '').replace('o clock', '').replace('am', 'AM').replace('AMerican airline', 'american airline')
        elif domain == 'ASTMatcher':
            text = text.replace('for statement', 'forstatement')
        log.lprint('test: ', text)
        city = ["washington", "atlanta", "philadelphia", "dallas", "francisco", "boston", "baltimore", "denver",
                "worth", "pittsburgh", "detroit",
                "westchester", "oakland", "stapleton", "tacoma", "jose"]
        for i in city:
            while i in text:
                index = text.find(i)
                text = text[0].capitalize() + text[1:index] + text[index].capitalize() + text[index+1:]
        return text.replace('\n', '')



    def parsing(self, text, domain):
        self.text = self.preprocessing(text, domain)
        log.log('Start parsing sentence: ' + self.text)
        self.stanford_parsing()
        self.domain_annotator(domain)
        self.set_local()

    def set_local(self):
        for t in self.sentence.token:
            self.token.append(Token(t))
        for e in self.sentence.enhancedPlusPlusDependencies.edge:
            tmp = Dependency(e)
            self.dependency.append(tmp)
            self.token[tmp.source].dep.append(tmp)
        self.root = self.sentence.enhancedPlusPlusDependencies.root[0]-1

    def stanford_parsing(self):
        log.log('starting JAVA Stanford CoreNLP Server...')
        # setting nlp configurations
        # %env CORENLP_HOME=/Users/zifannan/Documents/code/java/stanford-corenlp-full-2018-10-05

        annotator_list = ['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'parse', 'depparse']
        client = CoreNLPClient(start_server=self.start_server, annotators=annotator_list, timeout=60000, memory='8G')
        self.annotate = client.annotate(self.text)
        client.stop()
        self.sentence = self.annotate.sentence[0]
        # self.dependency = self.sentence.enhancedPlusPlusDependencies

    def domain_annotator(self, domain):
        """
        Assign NER (name entity recognition) tags to special names that may appear in users' queries. 
        """
        if domain == 'Flight':
            log.log('Loading domain NER from domain knowledge')

            ner_dict = {}

            # load from domain defined name entity: HISyn/domain_knowledge/[domain]/name_entity.txt
            ner_file = open(f'{root_dir}/domain_knowledge/{domain}/name_entity.txt', 'r', encoding='utf-8').readlines()

            # load from user defined name entity: HISyn/Documentation/[domain]/name_entity.txt
            ner_user_file = open(f'{root_dir}/Documentation/{domain}/name_entity.txt', 'r', encoding='utf-8').readlines()

            ner_lines = ner_file + ner_user_file
            for line in ner_lines:
                if '=' in line and '#' not in line:
                    l = line.replace(' ', '').split('=')
                    ner = l[0].split(':')[0]
                    self.ner_mapping_dict[ner.lower()] = l[0].split(':')[1].lower()
                    words = l[1].replace('[', '').replace(']', '').replace('\n', '').split(',')
                    for w in words:
                        if w.lower() in ner_dict:
                            log.err('duplicated NER, overwriting:', f'{w}: {ner_dict[w.lower()]} -> {ner.lower()}' )
                        ner_dict[w.lower()] = ner.lower()


            for t in range(len(self.sentence.token)):
                token = self.sentence.token[t].word.lower()
                if token in ner_dict:
                    self.sentence.token[t].ner = ner_dict[token]

            print(self.ner_mapping_dict)

            log.log('Finish domain specific NER')

        elif domain == 'TextEditing':
            string = ['colon', 'space', 'dollar', 'name']
            integer = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th' '13th', '80th', '1', '2', '3', '4',
                       '5', '6', '7', '8', '9', '10', '14','52']
            general_ordi = ['first']

            for t in range(len(self.sentence.token)):
                if self.sentence.token[t].word in string:
                    self.sentence.token[t].ner = 'STRING'
                elif self.sentence.token[t].word in integer:
                    self.sentence.token[t].ner = 'INTEGER'
                elif self.sentence.token[t].word in general_ordi:
                    self.sentence.token[t].ner = 'GENERAL'

        elif domain == 'ASTMatcher':
            string = ['pi', '*']
            unary = []

            for t in range(len(self.sentence.token)):
                if self.sentence.token[t].word in string:
                    self.sentence.token[t].ner = 'STRING'
                elif self.sentence.token[t].word in unary:
                    self.sentence.token[t].ner = 'UNARY'

        elif domain == 'Matplotlib':
            xpositions = ['1', '2']
            ypositions = ['3', '4']
            plotformats = ['bo','b+','ro','r+','go','g+']

            for t in range(len(self.sentence.token)):
                if self.sentence.token[t].word in xpositions:
                    self.sentence.token[t].ner = 'xpos'
                elif self.sentence.token[t].word in ypositions:
                    self.sentence.token[t].ner = 'ypos'
                elif self.sentence.token[t].word in plotformats:
                    self.sentence.token[t].ner = 'plotformat'


    def displayNode(self, index, n):
        log.lprint('---' * n + '| ', self.token[index].word, '[' + self.token[index].pos + '], [', self.token[index].ner + '], [', self.token[index].lemma, ']')
        for e in self.token[index].dep:
            self.displayNode(e.target, n+1)

    def displayByNode(self, n):
        self.displayNode(self.root, n)
        # for e in self.token[self.root].dep:
        #     self.displayNode(e.target, n+1)


    def displayByEdge(self):
        log.lprint('---------------- Dependency graph -----------------')
        for e in self.dependency:
            log.lprint(self.token[e.source].word,
                  '[' + self.token[e.source].pos + ']',
                  '[' + self.token[e.source].ner + ']',
                  '[' + self.token[e.source].lemma + ']',
                  self.token[e.source].mapping,
                  '--' + e.dep + '-->',
                  self.token[e.target].word,
                  '[' + self.token[e.target].pos + ']',
                  '[' + self.token[e.target].ner + ']',
                  '[' + self.token[e.target].lemma + ']',
                  self.token[e.target].mapping,
                  '====>>',
                  e.api_paths, e.prep_mapping)
            log.lprint('')
        log.lprint('--------------------------------------------------')

    def display_stanfordnlp_result(self):
        for e in self.sentence.enhancedPlusPlusDependencies.edge:
            log.lprint(self.sentence.token[e.source - 1].word,
                  '[' + self.sentence.token[e.source - 1].pos + ']',
                  '[' + self.sentence.token[e.source - 1].coarseNER + ',' + self.sentence.token[
                      e.source - 1].fineGrainedNER + ']',
                  '[' + self.sentence.token[e.source - 1].lemma + ']',
                  '--' + e.dep + '-->',
                  self.sentence.token[e.target - 1].word,
                  '[' + self.sentence.token[e.target - 1].pos + ']',
                  '[' + self.sentence.token[e.target - 1].coarseNER + ',' + self.sentence.token[
                      e.target - 1].fineGrainedNER + ']',
                  '[' + self.sentence.token[e.target - 1].lemma + ']')
