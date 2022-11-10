# Introduction

HISyn refers to "**h**uman learning **i**nspired **syn**thesizer". It is a Natural Language Programming tool, which generates code based on queries written in English.

Unlike other Natural Lanugage Programming tools that are driven by many training samples, HISyn does not need training examples. For a given domain, the user just needs to provide the document of the domain's APIs and optionally some special knowledge about that domain. HISyn can then work in that new domain. 

HISyn was inspired by how Humans learn programming: Instead of going through millions of coding examples, humans typically learn about the APIs of the new domain by reading the documents. HISyn takes a similar approach, learning about the new domain through NL understanding on the domain's document. So, **zero training examples** are needed by HISyn. 

Currently, HISyn mainly targets API programming, where, the programmer wants to write some expressions that are composed of some APIs in a certain domain. An example is the text editing domain, where there is a number of APIs useful for finding, replacing, deleting, inserting strings in a text. For a programmer who is not familar with those APIs, she can express her intent in Englilsh and then use HISyn to easily generate the desired expression. 

Details can be found in the paper *HISyn: Human Learning-Inspired Natural Language
Programming*(https://research.csc.ncsu.edu/picture/publications/papers/FSE20-HISyn.pdf) published on FSE2020.

## Prerequisites

Python 3.6 or later.

## Installation and Quick Start
To deploy HISyn on local machine, after clone this repository, you also need to download the required third party packages. 
Please refer to instructions in [third_party_pkgs](./third_party_pkgs) to download and install all the necessary packages. 

After having StanfordNLP package deployed, you need to install the stanfordnlp python library:

      pip install stanfordnlp

The main high-level scripts for running HISyn are main_interact.py, main_new.py and main-new.ipynb (*for jupyter notebook*). After finishing setting up StanfordNLP, you
can directly run these scripts to see HISyn in action. Examples:

```
python main_new.py # batch processing of a number of example inputs by default
python main_interact.py # allow users to input one sentence each time
```

Some example tests are in the `Documentation` folder. For instance, `Documentation/ASTMatcher/text_new.txt` contains a 
number of example queries in the ATMatcher domain, and `Documentation/ASTMatcher/code_new.txt` contains the 
corresponding code expressions (i.e., the ground truth). 

## Hints
### Speed up HISyn by launching the NLP server
HISyn uses Stanford NLP server for NL parsing. Starting the server takes time. Instead of starting the server 
when processing each query, the user may start the server ahead of time in a separate terminal. Go to 
`third_party_pkgs` folder.

For Linux/Mac users, run the following command:

```
sh start_nlp_server.sh
```

For Windows users, in command terminal, change the directory to `third_party_pkgs\stanford-corenlp-full-2018-10-05`, then 
run the following command:
```
java -Xmx8g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 -timeout 15000
```

It may take a few seconds. Then, if you run HISyn in another terminal, the processing time will be significantly
shortened (the first-time run might still take a few seconds). 

### Protobuff downgrade
You might encounter the following error message:
```commandline
TypeError: Descriptors cannot not be created directly.
If this call came from a _pb2.py file, your generated code is out of date and must be regenerated with protoc >= 3.19.0.
If you cannot immediately regenerate your protos, some other possible workarounds are:

1. Downgrade the protobuf package to 3.20.x or lower.
2. Set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python (but this will use pure-Python parsing and will be much slower).
```
To solve this issue, you can do either ways as the error message suggested:
(```pip install protobuf==3.20.*``` can downgrade the protobuf package.)

## How to support a new domain

HISyn features domain extensibility. Users can enable NL programming with HISyn in a new domain by providing it with a *structued API documentation* and a *grammar* of the domain. 

### Formats

#### Format of *structured API documentation*

   The raw API documentation of a domain may be in various formats. HISyn requires the documenation to be in a certain format called *structured API documentation*. The documentation should be a text file, with every API specified in the following format:

    ```
    API name: the name of the API.
    input: the inputs/arguments of this API.
    return(*): the return type of this API. 
    description(*): the natural language description of this API.
    ``` 

    *Example*

    Below is an example of one API entry in the `flight` domain. The full example of the `structured API documentation`
can be found in the [flight domain folder](./Documentation/Flight/API_documents.txt).

    ```
    EXTRACT_ROW_MAX
    input: AtomicColSet, AtomicRowPredSet
    return:flight
    description: the flight with the max highest most value
    ```

  
#### Format of the grammar

  The grammar of a domain contains the context-free grammar written in Backus-Naur form (BNF). Please refer to the `grammar.txt` of each domain in [Document folder](./Documentation/) for examples.


### For domains with an available grammar 

In this case, the user would need to create the *structured API documentation*. Manual conversion from a raw documentation to a *structured API documentation* can be time-consuming. So when there are many APIs in a domain, the users are recommended to create a script to do that. Some existing parsing tools (e.g., BeautifulSoup for HTML) may come in handy. 

When both the documentation and grammar of the new domain (`new_domain`) are in HISyn's required formats, the user just needs to create a new directory with the domain name in ./Document folder, and put there the documents `API_documents.txt` (for the documentation) and `grammar.txt` (for the grammar). HISyn can then support NL programming in `new_domain`. The user may try it by changing `domain` to this new domain in the `main` function of `./main_interact.py`.  

```
domain = 'new_domain'
```

### For domains with only the raw API documentation

Sometimes, a domain does not have a standalone Domain-Specific Language, but is embodied by a library in a general programming language (i.e. the host language). 
These domains usually do not have their own grammar readily available. In this case, the users would need to create the grammar and the *structured API documentation*. Fortunately, XGen provides a tool that can generate both the grammars and the *structured API documentation* for a domain. Please refer to [grammar_generation](./tools/grammar_generation) for details.
[This video](https://drive.google.com/file/d/18DlmjA9dnp0VB5efcYQ7m8SgbIKspWJG/view?usp=sharing) shows a demo about how to add new domains using grammar generation tools.

### A few more steps

To make HISyn generate accurate results, the following extra steps are suggested to provide XGen with some domain-specific knowledge.

1. Add domain name entity annotations.

    HISyn relies on the name entity tags to identify the arguments inside the NL query. For example, to generate code for a query in the flight domain, `I would like to travel to Dallas from Philadelphia`, 
    HISyn needs to know that `Dallas` and `Philadelphia` are two cities rather than some kind of keywords that need to be mapped to some APIs. 
    
    Although the NLP tool used by XGen provides name entity recognition, it is not precise enough for some domains. Thus we can create our own domain annotations to help HISyn recognize such arguments. Please see `./front_end/NLP.py` line 127 for the form of the annotation. Such annotations are stored in the `NER` field (for name entity recognition) of the NLP class in XGen. Before adding annotations for a new domain, the users are suggested to check the annotations in the domains already covered by XGen to learn how to add annotations for a domain. 
    
2. Link the name entity to argument terminals in the grammar.
    
    HISyn generates code expression based on the grammar of the domain. Thus, for the annotated entities, HISyn needs to know which arguments of the API they are corresponding to.
    
    The corresponding relations are stored in `./common_knowledge/NLPCommonKnowledge.py`, line 58, as a dictionary.
    
    The key of each item is the `NER` tag of the argument, and the value is the argument terminal inside the grammar.
    
    
