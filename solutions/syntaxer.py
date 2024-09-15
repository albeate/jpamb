#!/usr/bin/env python3
""" A very stupid syntatic analysis, that only checks for assertion errors.
"""

import os
import sys, logging

l = logging
l.basicConfig(level=logging.DEBUG)

(name,) = sys.argv[1:]

import re
from pathlib import Path

# Read the method_name
RE = r"(?P<class_name>.+)\.(?P<method_name>.*)\:\((?P<params>.*)\)(?P<return>.*)"
if not (i := re.match(RE, name)):
    l.error("invalid method name: %r", name)
    sys.exit(-1)

TYPE_LOOKUP = {
    "Z": "boolean",
    "I": "int",
}


srcfile = (Path("src/main/java") / i["class_name"].replace(".", "/")).with_suffix(
    ".java"
)

import tree_sitter
import tree_sitter_java

JAVA_LANGUAGE = tree_sitter.Language(tree_sitter_java.language())
parser = tree_sitter.Parser(JAVA_LANGUAGE)

with open(srcfile, "rb") as f:
    l.debug("parse sourcefile %s", srcfile)
    tree = parser.parse(f.read())

simple_classname = i["class_name"].split(".")[-1]

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

method_name = i["method_name"]

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

    if len(params) == len(i["params"]) and all(
        (tp := t.child_by_field_name("type")) is not None
        and tp.text is not None
        and TYPE_LOOKUP[tn] == tp.text.decode()
        for tn, t in zip(i["params"], params)
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

## recursiveness, nestedness? 
## to-do: tilføj (method_name)
##name: (identifier) @method-name (#eq? @method-name "{method_name}")
divide_q = JAVA_LANGUAGE.query(
f"""
(method_declaration
  name: (identifier) @method-name (#eq? @method-name "{method_name}")
  body: (block 
        (return_statement 
        (binary_expression 
           operator: "/"
           right: (_) @rhs
           ) @expr
)))
 """)

"""
python3 solutions/syntaxer.py "jpamb.cases.Simple.divideByN:(I)I"
python3 solutions/syntaxer.py "jpamb.cases.Simple.divideByZero:()I"
python3 solutions/syntaxer.py "jpamb.cases.Simple.assertFalse:()V"
python3 ./bin/evaluate.py sample.yaml -o sample.json 
"""

# dict_ = dict(divide_q.captures(tree.root_node).items())
# print("dict_: ", dict_)
# print("bool(dict_): ", bool(dict_))
# print('rhs' in dict_)
if 'rhs' in dict(divide_q.captures(tree.root_node).items()):
    print("divide by zero;80%")
else:
    l.debug("Did not find any divide by zero")
    print("divide by zero;20%")

if 'assert' in dict(assert_q.captures(body).items()):
    print("assertion error;80%")
else:
    l.debug("Did not find any assertions")
    print("assertion error;20%")

# for node, t in assert_q.captures(body).items():
#     print("node: ", node)
#     if node == "assert":
#         print("assertion error;80%")
#         break
#     else:
#         l.debug("Did not find any assertions")
#         print("assertion error;20%")
#         break

# l.debug("Found assertion")
# print("assertion error;80%")

sys.exit(0)
