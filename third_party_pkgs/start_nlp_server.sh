#!/usr/bin/env bash

DIR=$(dirname $0)
echo "$DIR"
cd $DIR/stanford-corenlp-full-2018-10-05
java -Xmx8g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 -timeout 15000
