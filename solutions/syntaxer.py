#!/usr/bin/env python3
""" A very stupid syntatic analysis, that only checks for assertion errors and now also some division by zero errors. 
"""

import sys, logging
from jpamb_utils import MethodId
import tree_sitter
import tree_sitter_java

JAVA_LANGUAGE = tree_sitter.Language(tree_sitter_java.language())
parser = tree_sitter.Parser(JAVA_LANGUAGE)

l = logging
l.basicConfig(level=logging.DEBUG)

(name,) = sys.argv[1:]
method = MethodId.parse(name)

srcfile = method.sourcefile()

with open(srcfile, "rb") as f:
    l.debug("parse sourcefile %s", srcfile)
    tree = parser.parse(f.read())

simple_classname = method.class_name.split(".")[-1]

# To figure out how to write these you can consult the
# https://tree-sitter.github.io/tree-sitter/playground
class_q = JAVA_LANGUAGE.query(
    f"""
    (class_declaration 
        name: ((identifier) @class-name 
               (#eq? @class-name "{simple_classname}"))) @class
"""
)

for node in class_q.captures(tree.root_node)["class"]:
    break
else:
    l.error(f"could not find a class of name {simple_classname} in {srcfile}")
    sys.exit(-1)

l.debug("Found class %s", node.range)

method_name = method.method_name

method_q = JAVA_LANGUAGE.query(
    f"""
    (method_declaration name: 
      ((identifier) @method-name (#eq? @method-name "{method_name}"))
    ) @method
"""
)

for node in method_q.captures(node)["method"]:
    if not (p := node.child_by_field_name("parameters")):
        l.debug(f"Could not find parameteres of {method_name}")
        continue

    params = [c for c in p.children if c.type == "formal_parameter"]

    if len(params) == len(method.params) and all(
        (tp := t.child_by_field_name("type")) is not None
        and tp.text is not None
        and tn == tp.text.decode()
        for tn, t in zip(method.params, params)
    ):
        break
else:
    l.warning(f"could not find a method of name {method_name} in {simple_classname}")
    sys.exit(-1)

l.debug("Found method %s %s", method_name, node.range)

body = node.child_by_field_name("body")
assert body and body.text
for t in body.text.splitlines():
    l.debug("line: %s", t.decode())

assert_q = JAVA_LANGUAGE.query(f"""(assert_statement) @assert""")
divide_q = JAVA_LANGUAGE.query(f"""(binary_expression operator: "/" right: (_) @rhs) @expr""")
while_q = JAVA_LANGUAGE.query(
f"""
(block
  (local_variable_declaration
    declarator: 
      (variable_declarator
        name: (identifier) @varname
        value: (_) @varval
      )
   )
  (while_statement
    condition: 
      (_
        (binary_expression
          left: (identifier) @lhs
          operator: ">" 
          right: (_) @rhs
        ) @expr
      )
   ) @while
 )
""")

"""
python3 solutions/syntaxer.py "jpamb.cases.Simple.divideByN:(I)I"
python3 solutions/syntaxer.py "jpamb.cases.Simple.divideByZero:()I"
python3 solutions/syntaxer.py "jpamb.cases.Simple.assertFalse:()V"
python3 solutions/syntaxer.py "jpamb.cases.Tricky.collatz:(I)V"


-> vil altid fejler som koden er nu, da jeg ikke tjekker for evighedsløkker... hmm
python3 solutions/syntaxer.py "jpamb.cases.Loops.neverAsserts:()V"
python3 solutions/syntaxer.py 'jpamb.cases.Loops.neverDivides:()I'


python3 ./bin/evaluate.py -vv experiment.yaml -o experiment.json 
python3 ./bin/evaluate.py -vv --filter-methods=Simple syntaxer.yaml -o syntaxer.json 
"""

######################
## to-do :: get them all together ##
def tjekWhileLoop(while_q):
    if 'while' in dict(while_q.captures(body).items()):
        varname = while_q.captures(body)['varname'][0].text.decode()
        varval = while_q.captures(body)['varval'][0].text.decode()
        lhs = while_q.captures(body)['lhs'][0].text.decode()
        rhs = while_q.captures(body)['rhs'][0].text.decode()
        if varname == lhs and varval == rhs:
            return True
    return False

######################

if 'rhs' in dict(divide_q.captures(body).items()):
    for node in divide_q.captures(body)['rhs']:
        n = node.text.decode()
        if n == '0':
            print("divide by zero;90%")
        else:
            print("divide by zero;80%")
else:
    l.debug("Did not find any divide by zero")
    print("divide by zero;10%")

if 'assert' in dict(assert_q.captures(body).items()):
    print("assertion error;80%")
else:
    l.debug("Did not find any assertions")
    print("assertion error;20%")


sys.exit(0)
