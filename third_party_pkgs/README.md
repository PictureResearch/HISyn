## third_party_pkgs
This directory is used to store the third party packages used in HISyn.

In V1.0, only StanfordCoreNLP is used. Please follow the following instructions to install it.  

### Package install instructions

- Step 1: Download StanfordCoreNLP

   Download the version 3.9.2(2018-10-05) from stanfordnlp official website (https://stanfordnlp.github.io/CoreNLP/history.html).
   If your download doesn't start, your web browser may have blocked downloading zip files. You may try a different web browser or use command line to directly download the package (e.g., wget http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip). 
   

- Step 2: Unzip the package and put the entire folder under *third_party_pkgs* folder.
   
   The directory should look like:
   
        -HISyn
        --third_party_pkgs
        ---stanford-corenlp-full-2018-10-05
        ---start_nlp_server.sh

- Step 3: Run StanfordNLP server
   Run start_nlp_server.sh in a shell: 
   
        sh start_nlp_server.sh

   This command will start a StanfordNLP sever at port 9000. The front end of HISyn will pass the text to the server through corenlp client and get the NLP results.
