#!/usr/bin/env python3
"""
jpamb >> python3 intLib/dynamicAnalysis.py
jpamb >> python3 ./bin/evaluate.py -vv --filter-methods=Simple interpret.yaml -o interpret.json 
jpamb >> python3 ./bin/evaluate.py -vv --filter-methods=Arrays interpret.yaml -o interpret.json
jpamb >> python3 ./bin/evaluate.py -vv --filter-methods=Calls interpret.yaml -o interpret.json
jpamb >> python3 ./bin/evaluate.py -vv --filter-methods=Loops interpret.yaml -o interpret.json
jpamb >> python3 ./bin/evaluate.py -vv --filter-methods=Tricky interpret.yaml -o interpret.json
jpamb >> python3 ./bin/evaluate.py -vv  interpret.yaml -o interpret.json

inddata kan være af type heltal (I), bolsk (Z), intet (),
to heltal (II), en liste af af heltal ([I) og en liste af bogstaver ([C).

"""
"""
Koden virker, men mangler en bedre struktur. Er lavet meget hen af vejen.
Noget af koden kan laves mere smart. E.g. den del der printer gættene.
"""

import interpret_bib as ib
import tree_sitter_java as tsjava
import sys, logging, re, tree_sitter

from random import randrange, choices, sample
from string import ascii_letters

def tjekCases(cases):
    c = ["assertion error", "ok", "*", "divide by zero","out of bounds","null pointer"]
    for x in c:
        if x != cases:
            return print(x+";0%")
    return None

l = logging
l.basicConfig(level=logging.DEBUG)

(name,) = sys.argv[1:]
methodid = ib.MethodId.parse(name)
pattern = r'^(.*)\.(.*):\(([^)]*)\)(\w)$'
matches = re.match(pattern, name)

if matches:
    class_ = matches.group(1).split(".",3)[2]
    method_name = matches.group(2)
    l.debug(f"klasse: {class_}")
    l.debug(f"methodenavn: {method_name}")
    l.debug(f"--------------------")
    path = "src/main/java/jpamb/cases/" + class_.replace(".", "/") + ".java"
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
        #cases = nodes.text.decode()
        case = nodes.text.decode().rsplit("->",1)[1].split("\")",1)[0].strip() # gør ish brug af den
        l.debug(f"cases: {case}")
        if matches:
            param = matches.group(3)
            l.debug(f"parameter: {param}")
            if param == 'Z':
                val = '('+str(choices(['false', 'true'],k=1).pop())+')'
            elif param == 'I':
                val = '('+str(randrange(101))+')'
            elif param == 'II':
                val = '('+str(randrange(101))+','+str(randrange(101))+')'
            elif param == '[I':
                val = '([I:'+str(sample(range(0,101),randrange(10))).strip("[]")+'])'
            elif param == '[C':
                val = '([C:'+str(choices(ascii_letters, k=randrange(10))).strip("[]")+'])'
            else:
                val = '()'    
        inputs = ib.InputParser.parse(val)
        m = methodid.load()
        i = ib.SimpleInterpreter(m["code"]["bytecode"], [i.tolocal() for i in inputs], [])
        result = i.interpet()
        l.debug(f"inddata: {val}")
        l.debug(f"uddata: {result}")
        print(result+";100%")
        # todo: så længe ej result eller en case så print(case+"0%") 
        
        # match result:
        #   case "assertion error":
        #     print("assertion error;100%")
        #     if cases != result:
        #         print(cases + ";100%")
        #   case "ok":
        #     print("ok;100%")
        #     if cases != result:
        #         print(cases + ";100%")
        #   case "*":
        #     print("*;100%")
        #     if cases != result:
        #         print(cases + ";100%")
        #   case "divide by zero":
        #     print("divide by zero;100%")
        #     if cases != result:
        #         print(cases + ";100%")
        #   case "out of bounds":
        #     print("out of bounds;100%")
        #     if cases != result:
        #         print(cases + ";100%")
        #   case "null pointer":
        #     print("null pointer;100%")
        #     if cases != result:
        #         print(cases + ";100%")
        #   case '':
        #      print("ok;80%")
        #      if cases != result:
        #          print(cases + ";100%")
        #          tjekCases(cases)
        l.debug(f"--------------------")
    f.close() 
else:
    l.debug(f"< {name} > er ikke gyldig inddata." )
    sys.exit(0)
