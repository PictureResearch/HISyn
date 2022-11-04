## Grammar generation
The grammar generation tool is used to generate the grammar of a domain from its documentation. As a side product, it also generates the *structured API document* which can be used directly by HISyn when it generates code expressions. 

The current grammar generation tool supports two types of domain-specific languages (DSLs): object-oriented DSLs (i.e., those with classes and methods), and functional DSLs (i.e., its expressions consist of only (nested) function calls).
The `sklearn` library (Science Kit library in Python) and the `re` module (regular expression library in Python) are examples of the former; the basic code expression may take a form like `object.method(keyword_arg = type_literal)`. The `TextEditing` DSL already included in XGen's examples belongs to the latter; there are no classes or methods but only functions in their code expressions. 

### Generate grammars for object-oriented DSLs

- Step 1: Prepare a *detailed API specification*.
    
    A *detailed API specification* is similar to a *structured API documentation*, except that a *detailed API specification* contains more details. These details are useful for grammar generation.
    
    The specification of an API in a *detailed API specification* takes the following format: 
    
    ```
    name(*): the name of the API.
    caller(*): the APIs that could call this API.
    type(*): class - the class name,class construct.
          method - the methods of a class.
          keyword_arg - the keyword argument of the construct or methods.
          literal - the options for a keyword argument that have specific semantics.
          type_literal - specific types or terminal in the grammar 
    method: (used only if the API is a class) all the methods of the class.
    argument(*): the arguments of this API .
    return(*): the return type of this API. This item could be empty if this API does not return anything.
    description(*): the natural language description of this API.
    ```     

    *Example*

    Below is an example of an API in the `sklearn` domain. The full example input file
    can be found here: [example_inputs](./example_inputs/sklearn/API_documents_autogen.txt).
    
    ```
    name: sklearn.linear_model.LinearRegression
    caller: object
    class: sklearn.linear_model.LinearRegression
    type: class
    method: fit | get_params | predict | score | set_params
    argument: fit_intercept, normalize, copy_X, n_jobs, positive
    return: sklearn.linear_model.LinearRegression
    description: Ordinary least squares Linear Regression. LinearRegression fits a linear model with coefficients w = (w1, …, wp) to minimize the residual sum of squares between the observed targets in the dataset, and the targets predicted by the linear approximation.
    ``` 

   *Notes*
      * The above items that labeled with (*) are mandatory for all APIs.
      * As the keyword arguments (keyword_arg) and the literals in a domain are important component of a domain, they should be treated in a way similar to the treament of an API in the domain. So in the *detailed API specification*, each of the keyword arguments and literals in the domain needs to have an entry just as an API does; some fields (e.g., argument) can be left empty.
      * The users are recommended to creates a script to automatically convert the raw documentation of a domain to the *detailed APi specification*. Some existing parsing tools (e.g., BeautifulSoup for HTML) may come in handy. 


- Step 2: Create a domain folder in the `Documentation` folder of HISyn and put the *detailed API specification* there. 
 

- Step 3: Modify and run `grammar-generation.py`

   select the correct grammar generator (line 7), `GrammarGenerator_class()` 
   
    ```
    # select a generator for different target DSL
    gram_gen = GrammarGenerator_class() # for object-oriented DSLs
    # gram_gen = GrammarGenerator_func() # for functional DSLs
    ```

   set the correct argument for grammar generator (line 10), including `domain` and `file_path`.
    ```
    gram_gen.generate_grammar(domain = New-Domain-Name, doc_file=root_dir + The-Path-To-The-Detailed-API-Specification)
    ```
  

### Generate grammar for functional DSLs

The process is the same as that of the object-oriented DSLs. The differences are two:

(i) The format of the specification of an API in the *detailed API specification*:

    *Format*
    
    ```
    name(*): the name of the API.
    type: norm [default] | literal
    argument(*): the arguments of this API.
    return(*): the return type of this API. Can be empty if this API can does not return anything.
    description(*): the natural language discription of this API.
    ```

    *Example*

    Below is an example of an API entry in the `HPC-FAIR` domain (a domain for handling datasets). The full example input file
    can be found here: [example_inputs](./example_inputs/HPC-FAIR/API_documents_autogen.txt).

    ```
    name: BuildingDataset
    type:
    return:	kernel_data_best.csv | kernel_stat.csv
    argument: output.log
    description: Merge kernel-level and data-level features by outer-join
    ``` 

(ii) Use a different version of the GrammarGenerator

    ```
    # select a generator for different target DSL
    # gram_gen = GrammarGenerator_class() # for domain with classes and methods
    gram_gen = GrammarGenerator_func() # for domain with only function calls
    ```

### Outputs

The grammar generator produces two files:

   - *grammar*: a text file, by default, stored as `Documentation/DomainName/grammar-gen.txt`
   - *structured API documentation*: a text file, by default, stored as `Documentation/DomainName/API_documents.txt`

Both files will be used by HISyn when it generates code for a given query.
   
## Hints

Grammar generation tool is still under developing. When apply to a new domain, 
please start with a small portion of APIs and manually check the correctness of 
the generated grammar before applying it to whole domain.