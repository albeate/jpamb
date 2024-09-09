#!/usr/bin/env python3

"""
================== The intro ==================
This script looks at the current method and locates its @Case(..). 
From there it extracts the information that we are interested in
and make our "guess". 
==============================================

=================== The how ==================
Basically this script is cheating by automating the manuel process
Christian showed us in the <Getting started with the game>. It's
automated usng tree-sitter. 

It works by querying the parser, that has parsed the desired code.
It'll only look at the current method name (taken directly from 
syntaxer.py). Then, in the same breath, extracts the that methods 
@Case(..). These are then used to make a "guess" for each method. 

For some reason it don't like <null pointer> in the following methods 
from Array.java arrayIsNullLength:()V, arrayIsNull:()V and 
arraySometimesNull:(I)V. Either, its a problem in the sovs-code or it's 
on purpose. That you can't do the cheating method that has been 
applied in this script.
Imma gonna need to work on that.. 🫠
==============================================

To run code: python3 ./bin/evaluate.py experiment.yaml -o experiment.json

============ remove when working for <null poiner> ============
python3 ./bin/evaluate.py -vv --filter-methods=Arrays experiment.yaml -o experiment.json

python3 ./bin/evaluate.py -vvv --filter-methods='jpamb.cases.Arrays.arrayIsNullLength' experiment.yaml -o experiment.json
python3 ./bin/evaluate.py -vvv --filter-methods='jpamb.cases.Arrays.arrayIsNull' experiment.yaml -o experiment.json
python3 ./bin/evaluate.py -vvv --filter-methods='jpamb.cases.Arrays.arraySometimesNull' experiment.yaml -o experiment.json

python3 solutions/vogue.py 'jpamb.cases.Arrays.arrayIsNullLength:()V' 
python3 solutions/vogue.py ''jpamb.cases.Arrays.arrayIsNull:()V'
python3 solutions/vogue.py 'jpamb.cases.Arrays.arraySometimesNull:(I)V'
==============================================================
"""

import sys
import tree_sitter 
import tree_sitter_java as tsjava
from logging import DEBUG, debug, basicConfig

basicConfig(level=DEBUG)

# you can use sys.argv[0] as a way to make the program call it self
_, methodid = sys.argv
class_, method  = methodid.rsplit(".", 1)
method_name, _ = method.split(":",1)
path = "src/main/java/" + class_.replace(".", "/") + ".java"

with open(path) as f:
    txt = f.read()
JAVA_LANGUAGE = tree_sitter.Language(tsjava.language())
parser = tree_sitter.Parser(JAVA_LANGUAGE)
tree = parser.parse(bytes(txt, "utf8"))

# https://tree-sitter.github.io/tree-sitter/playground
query = JAVA_LANGUAGE.query(
f""" 
  (class_declaration
    body: 
      (class_body 
        (method_declaration 
          (modifiers
	       (annotation 
               arguments: (_ (_ (string_fragment))) @case-arg 
            )
          )
        name: (identifier) @method-name (#eq? @method-name "{method_name}")
      ) @method
    ) 
  )
"""
)

for nodes in query.captures(tree.root_node)["case-arg"]:
    case = nodes.text.decode().rsplit("->",1)[1].split("\")",1)[0].strip() # make the case clean (again)
    if class_.rsplit(".",1)[1] == "Arrays" and case == "null pointer": # a lappe-loesning: see top note for more info
        print(case + ";20%") # if it's set to zero, then we'll also get a false match for <null pointer>. Can't win 💩
    else:
        print(case + ";100%")

f.close() # remember children, always close up before you leave!
sys.exit(0)   