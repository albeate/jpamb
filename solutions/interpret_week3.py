#!/usr/bin/env python3

from dataclasses import dataclass
from pathlib import Path
import sys, logging
from typing import Literal, TypeAlias, Optional

import numpy as np

l = logging
l.basicConfig(level=logging.DEBUG, format="%(message)s")

JvmType: TypeAlias = Literal["boolean"] | Literal["int"]


@dataclass(frozen=True)
class MethodId:
    class_name: str
    method_name: str
    params: list[JvmType]
    return_type: Optional[JvmType]

    @classmethod
    def parse(cls, name):
        import re

        TYPE_LOOKUP: dict[str, JvmType] = {
            "Z": "boolean",
            "I": "int",
        }

        RE = (
            r"(?P<class_name>.+)\.(?P<method_name>.*)\:\((?P<params>.*)\)(?P<return>.*)"
        )
        if not (i := re.match(RE, name)):
            l.error("invalid method name: %r", name)
            sys.exit(-1)

        return cls(
            class_name=i["class_name"],
            method_name=i["method_name"],
            params=[TYPE_LOOKUP[p] for p in i["params"]],
            return_type=None if i["return"] == "V" else TYPE_LOOKUP[i["return"]],
        )

    def classfile(self):
        return Path("../decompiled", *self.class_name.split(".")).with_suffix(".json")

    def load(self):
        import json

        classfile = self.classfile()
        with open(classfile) as f:
            l.debug(f"read decompiled classfile {classfile}")
            classfile = json.load(f)
        for m in classfile["methods"]:
            if (
                m["name"] == self.method_name
                and len(self.params) == len(m["params"])
                and all(
                    p == t["type"]["base"] for p, t in zip(self.params, m["params"])
                )
            ):
                return m
        else:
            print("Could not find method")
            sys.exit(-1)

    def create_interpreter(self, inputs):
        method = self.load()
        return SimpleInterpreter(
            bytecode=method["code"]["bytecode"],
            locals=inputs,
            stack=[],
            # invokevirtual = [],
            callstack = [],
            pc=0,
        )

# Some useful CLI copy pasta. Golden log can be useful to look at when trying to debug
# Test all cases: python bin/test.py -o golden.log -- python solutions/interpret_week3.py
# Test cases but filter by methods: python bin/test.py --filter-methods=divideByN\: -o golden.log -- python solutions/interpret_week3.py
# Test one method: python solutions/interpret_week3.py 'jpamb.cases.Simple.divideByN:(I)I' '(2)'

@dataclass
class SimpleInterpreter:
    bytecode: list
    locals: list
    stack: list
    # invokevirtual: list
    callstack: list
    pc: int
    done: Optional[str] = None

    def interpet(self, limit=20):
        for i in range(limit):
            next = self.bytecode[self.pc]
            l.debug(f"STEP {i}:")
            l.debug(f"  PC: {self.pc} {next}")
            l.debug(f"  LOCALS: {self.locals}")
            l.debug(f"  STACK: {self.stack}")

            if fn := getattr(self, "step_" + next["opr"], None):
                fn(next)
            else:
                return f"can't handle {next['opr']!r}"

            if self.done:
                break
        else:
            self.done = "out of time"

        l.debug(f"DONE {self.done}")
        l.debug(f"  LOCALS: {self.locals}")
        l.debug(f"  STACK: {self.stack}")

        return self.done

    # OPERATOR METHODS
    def step_push(self, bc):
        if bc["value"] is None:
            self.stack.insert(0, None)
        else:
            self.stack.insert(0, bc["value"]["value"])
        self.pc += 1

    def step_return(self, bc):
        if bc["type"] is not None:
            self.stack.pop(0)
        self.done = "ok"

    def step_get(self, bc): # Missing formal rules
        match bc["field"]["name"]:
            case "$assertionsDisabled":
                result = False # Hardcoded for now
            case _:
                raise Exception("step_get not implemented")
            
        self.stack.insert(0, result)
        self.pc += 1

    def step_ifz(self, bc): # Missing formal rules
        condition = bc["condition"]
        right = 0
        left = self.stack.pop(0)

        result = self.if_match_result(condition, left, right, "ifz")

        self.pc = bc["target"] if result else self.pc + 1

    def step_if(self, bc): # Missing formal rules
        condition = bc["condition"]
        right = self.locals.pop(0)
        left = self.locals .pop(0)

        result = self.if_match_result(condition, left, right, "if")

        self.pc = bc["target"] if result else self.pc + 1

    def step_dup(self, bc): # Missing formal rules:
        self.stack.insert(0, self.stack[0])
        self.pc += 1

    # Missing formal rules
    def step_load(self, bc):
        """
        + * opr : "load"
          * type : <LocalType>
          * index : <number>
          -- load a local variable $index of $type
          -- {*} [] -> ["value"]
        """
        # print("hejhest: ",self.locals[bc["index"]])
        # print(bc["index"] in self.locals)
        # if bc["index"] in self.locals:
        try:
            self.stack.insert(0,self.locals[bc["index"]])
        except:
            None 
        self.pc += 1

    def step_store(self, bc):
        """
        + * opr : "store"
          * type : <LocalType>
          * index : <number>
          -- store a local variable $index of $type
          -- {*} ["value"] -> []
        """
        try:
            idx = bc["index"]
            if len(self.stack) > 0:
                val = self.stack.pop(0)
                # self.locals.insert(idx) = val
                # self.locals[idx] = val
                self.locals.insert(0,val)
        except:
            None            
        self.pc += 1
        
    def step_invoke(self, bc): # not sure if on stack
        cls = bc["method"]["ref"]["name"]
        name = bc["method"]["name"]
        try:
            print(self.locals[0])
            argType = bc["method"]["args"][0]
            args = self.locals[0]
            print("args: ", args)
        except:
            argType = ""
        match argType: # burde bare kopier det der allerede er lavet tidligere i koden -.-
          case "int":
            typ = 'I'
          case "boolean":
            typ = 'Z'
          case "":
            typ = ''
        mthId = cls.replace('/','.')+'.'+name+':('+typ+')V' # the V is hardcoded
        if typ == '':
            if MethodId.parse(mthId).create_interpreter('').interpet() is not None:
                if len(self.stack) > 0:
                    self.stack.pop()
        else:
            if MethodId.parse(mthId).create_interpreter([args]).interpet() is not None:
                if len(self.stack) > 0:
                    self.stack.pop()
        self.pc += 1
        
    def step_newarray(self, bc):
        """
        + * opr : "newarray"
          * * dim : <number>
            * type : <SimpleType>
            -- create a $dim - dimentional array of size $count and $type
            -- \{newarray\} ["count1","count2","..."] -> ["objectref"]
        """
        # print("hejhest:", bc["opr"] )
        if bc["opr"] == "newarray":
            dim = bc["dim"]
            arrType = bc["type"]
            size = self.locals[0]
            if size >= 2:
                # newArr = np.zeros_like(np.arange(size),dtype=arrType,shape=dim)
                self.stack.insert(0, [0 for _ in range(size)])
            else:
                self.stack.insert(0, [None]*1)
        self.pc += 1
    
    def step_array_store(self, bc):
        """
        + * opr : "array_store"
              * type : <JArrayType>
              -- load a $value of $type from an $arrayref array at index $index
              -- \{aastore\} ["arrayref","index"] -> ["value"]
        """
        if bc["opr"] == "array_store":
            arr = self.locals[0]
            val = self.stack.pop(0)
            idx = self.stack.pop(0)
            arr[idx] = val
            self.stack.insert(0,arr)
            
        self.pc += 1
        
    def step_arraylength(self, bc):
        if bc["opr"] == "arraylength":
            if any(isinstance(s,list) for s in self.stack):
                uddata = list(filter(lambda x: isinstance(x,list), self.stack))[0]
                arrLen = len(uddata)
                self.stack.insert(0,arrLen)
            else:
                self.stack.insert(0,1)
        self.pc += 1
        
    def step_binary(self, bc): # Missing formal rules 
        right = self.stack.pop(0)
        left = self.stack.pop(0)

        result = 0
        match bc["operant"]:
            case "add":
                result = left + right
            case "sub":
                result = left - right
            case "mul":
                result = left * right
            case "div":
                try:
                    result = left / right
                except ZeroDivisionError:
                    self.done = "err"
            case "rem":
                result = left % right
        
        self.stack.insert(0, result)
        self.pc += 1
    

    # HELPER METHODS
    def if_match_result(self, condition: str, value1, value2, operant: str) -> bool:
        match condition:
            case "ne":
                result = value1 != value2
            case "eq":
                result = value1 == value2
            case "lt":
                result = value1 < value2
            case "le":
                result = value1 <= value2
            case "gt":
                result = value1 > value2
            case "ge":
                result = value1 >= value2
            case _:
                raise ValueError(f"Condition '{condition}' is not implemented for step_'{operant}'")
            
        return result


if __name__ == "__main__":
    methodid = MethodId.parse(sys.argv[1])
    inputs = []
    result = sys.argv[2][1:-1]
    if result != "":
        for i in result.split(","):
            if i == "true" or i == "false":
                inputs.append(i == "true")
            else:
                inputs.append(int(i))
    print("yoyo:",inputs)
    print(methodid.create_interpreter(inputs).interpet())
