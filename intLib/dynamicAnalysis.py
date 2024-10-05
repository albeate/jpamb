#!/usr/bin/env python3
"""
jpamb >> python3 intLib/dynamicAnalysis.py
jpamb >> python3 ./bin/evaluate.py -vv --filter-methods=Simple interpret.yaml -o interpret.json 
jpamb >> python3 ./bin/evaluate.py -vv --filter-methods=Arrays interpret.yaml -o interpret.json
jpamb >> python3 ./bin/evaluate.py -vv --filter-methods=Calls interpret.yaml -o interpret.json
jpamb >> python3 ./bin/evaluate.py -vv --filter-methods=Loops interpret.yaml -o interpret.json
jpamb >> python3 ./bin/evaluate.py -vv --filter-methods=Tricky interpret.yaml -o interpret.json
jpamb >> python3 ./bin/evaluate.py -vv  interpret.yaml -o interpret.json

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
print("ok;_%")
print("assertion error;_%")
print("*;_%")
print("divide by zero;_%")
print("out of bounds;_%")
print("null pointer;_%")

'jpamb.cases.Simple.divideByN:(I)I'  '(2)' -> ok
'jpamb.cases.Arrays.binarySearch:(I)V' '(6)' -> assertion error
'jpamb.cases.Arrays.arrayOutOfBounds:()V' '()' -> 'out of bounds'
'jpamb.cases.Loops.neverAsserts:()V' '()' -> '*'
'jpamb.cases.Arrays.arrayIsNull:()V' '()' -> 'null pointer'
'jpamb.cases.Simple.divideByZero:()I' '(0)'  -> 'divide by zero'

methodid = ib.MethodId.parse('jpamb.cases.Simple.divideByN:(I)I')
inputs = ib.InputParser.parse('(2)')

>>>>>>> 4b620d4 (en grov version af dynamisk analyse)
=======
>>>>>>> cc42e12 (dynamisk analyse + yaml. oppe på ca 66 point)
=======
>>>>>>> cc42e12 (dynamisk analyse + yaml. oppe på ca 66 point)
inddata kan være af type heltal (I), bolsk (Z), intet (),
to heltal (II), en liste af af heltal ([I) og en liste af bogstaver ([C).

"""

import interpret_bib as ib
import sys, logging
import re
from random import randrange, choices, sample
from string import ascii_letters

l = logging
l.basicConfig(level=logging.DEBUG)

(name,) = sys.argv[1:]
methodid = ib.MethodId.parse(name)
pattern = r'^(.*)\.(.*):\(([^)]+)\)(\w)$'
matches = re.match(pattern, name)
if matches:
    param = matches.group(3)
    l.debug(f"parameter: {matches.group(3)}")
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
match result:
  case "assertion error":
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> cc42e12 (dynamisk analyse + yaml. oppe på ca 66 point)
    print("assertion error;100%")
  case "ok":
    print("ok;100%")
  case "*":
    print("*;100%")
  case "divide by zero":
    print("divide by zero;100%")
  case "out of bounds":
    print("out of bounds;100%")
  case "null pointer":
<<<<<<< HEAD
=======
    # print("assertion error;92%")
=======
>>>>>>> cc42e12 (dynamisk analyse + yaml. oppe på ca 66 point)
    print("assertion error;100%")
  case "ok":
    print("ok;100%")
  case "*":
    print("*;100%")
  case "divide by zero":
    print("divide by zero;100%")
  case "out of bounds":
    print("out of bounds;100%")
  case "null pointer":
<<<<<<< HEAD
    # print("null pointer;92%")
>>>>>>> 4b620d4 (en grov version af dynamisk analyse)
=======
>>>>>>> cc42e12 (dynamisk analyse + yaml. oppe på ca 66 point)
=======
>>>>>>> cc42e12 (dynamisk analyse + yaml. oppe på ca 66 point)
    print("null pointer;100%")
  case '':
     print("ok;80%")



