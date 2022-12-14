#################################################################
# NLP common knowledge
# Include prunable dependency tags, pos tags
# Include list of prepositions, common knowledge tags for
#   arguments
#################################################################


prunable_dep_tags = [
    'det',  # determiner
    'det:predet',
    'case',  # The case relation is used for any preposition in English. It was labeled together with nmod.
    'aux',
    # An aux (auxiliary) of a clause is a function word associated with a verbal predicate that expresses categories such as tense, mood, aspect, voice or evidentiality.
    'mark',  # A marker (mark) is the word introducing a clause subordinate to another clause
    'cop',  # A copula is the relation between the complement of a copular verb and the copular verb
    'cc',
    # A coordination is the relation between an element of a conjunct and the coordinating conjunction word of the conjunct.
    'conj:and',
    # A conjunct is the relation between two elements connected by a coordinating conjunction, such as and, or, etc.
    'punct',
    'acl:relcl',
    'conj:or',
    'ref',
    'auxpass'
]

prunable_pos_tags = [
    'PRP',  # personal pronoun
    'MD',  # modal
    'DT',  # Determiner
    'PRP$',  # Possessive pronoun
    'LS',
    'FW',
    'WP$'
]

preposition = [
    'from',
    'to',
    'between',
    'on',
    'after',
    'before',
    'around',
    'about',
    'by',
    'except',
    'in_front_of',
    'with',
    'unless',
    'following',
    'including',
    'inside',
    'above'
]


# NER: types in grammar
common_knowledge_tags = {
    'NUMBER': 'doubleValue',
    'xpos': 'x-pos',
    'ypos': 'y-pos',
    'plotformat': 'plot-format'
}