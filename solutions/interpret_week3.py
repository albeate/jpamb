#!/usr/bin/env python3

import sys, logging
import json
import numpy as np
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias, Optional


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
        return Path("decompiled", *self.class_name.split(".")).with_suffix(".json")

    def load(self):
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
    callstack: list # bruges den overhoved? .-.
    pc: int
    done: Optional[str] = None

    def interpet(self, limit=60):
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
        """
        opr : return
        type : nullable <LocalType>
        -- return a optional $value of $type
        -- {*return} ["value"] -> []
        -- \{return\} [] -> []
        
        Mangler at kunne returnerer fra en metode der er blevet kaldt
        via invoke. (tror jeg)
        """
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

    def step_goto(self, bc):
        """
        opr : goto
        target : <number>
        {goto*} [] -> []
        """
        if bc["opr"] == "goto":
            self.bytecode[bc["target"]]
        self.pc += 1
        
    def step_ifz(self, bc): # Missing formal rules
        condition = bc["condition"]
        right = 0
        left = self.stack.pop(0)
        result = self.if_match_result(condition, left, right, "ifz")
        self.pc = bc["target"] if result else self.pc + 1

    def step_if(self, bc): # Missing formal rules
        condition = bc["condition"]
        right = self.stack.pop(0)
        left = self.stack.pop(0)
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
        variable_to_store = self.stack.pop(0)
        self.locals.insert(bc["index"], variable_to_store)
        self.pc += 1
        
    def execute_bytecode(self, bytecode):
        for instruction in bytecode:
            next = bytecode[self.pc]
            if fn := getattr(instruction, "step_" + next["opr"], None):
                fn(next)

    def step_invoke(self, bc):
        cls = bc["method"]["ref"]["name"]
        if cls == 'java/lang/AssertionError':
            self.stack.pop(0)
            # self.stack.insert(0,False)
            self.stack.insert(0,"assertion error")
        else:
            name = bc["method"]["name"]
            args = bc["method"]["args"]
            # self.locals = {i: arg for i, arg in enumerate(args)}
            if 'int' in args: # mangler at få lavet den dynamisk mht antallet ad inddata
                args_type = 'I'
            elif  'boolean' in args:
                args_type = 'Z'
            else:
                args_type = ''
                return_type = "V" # mangler stadig at få den lavet dynamisk. Kig på original koden 
                method_name = cls.replace('/','.')+'.'+name+':('+args_type+')'+return_type
                # print("invoke_self.locals  := ", self.locals)
                # print("invoke_class := ", cls)
                # print("invoke_name := ", name)
                # print("invoke_argv := ", args)
                # print("invoke_args_type := ", args_type)
                # print("invoke_method_name := ", method_name)
                bytecode = MethodId.parse(method_name).load()
                # print("invoke_bytecode:= ", bytecode)
                execute_bytecode(bytecode) # arbejder på det
                if bytecode is not None:
                    self.stack.pop()
        self.pc += 1
    
    def step_new(self, bc):
        """
        + * opr : "new"
          * class : <ClassName>
          -- create a new $object of $class
          -- \{new\} [] -> ["objectref"]
        """
        # "class": "java/lang/AssertionError"
        class_name = bc["class"]

        # Simulate the creation of a new object (here, an AssertionError object)
        new_object = f"new {class_name}()"
        self.stack.insert(0, new_object)
        self.pc += 1
    
    def step_throw(self, bc):
        """
        + * opr : "throw"
          * <empty>
            -- throws an exception
            -- \{athrow\} ["objectref"] -> ["objectref"]
        """
        
        self.pc += 1
        
    # def step_invoke(self, bc): # not sure if on stack
    #     """
    #     alt her, kunne laves pænere. Men tør ikke at røre noget pt
    #     """
    #     cls = bc["method"]["ref"]["name"]
    #
    #     try:
    #         l.debug(f"local: {self.locals[0]}")
    #         argType = bc["method"]["args"][0]
    #         args = self.locals[0]
    #         l.debug(f"args: {args}")
    #     except:
    #         argType = ""
    #     match argType: # burde bare kopier det der allerede er lavet af forelæser
    #       case "int":
    #         typ = 'I'
    #       case "boolean":
    #         typ = 'Z'
    #       case "":
    #         typ = ''
    #     mthId = cls.replace('/','.')+'.'+name+':('+typ+')V' # the V is hardcoded
    #
    #     # kunne laves pænere...
    #     if typ == '':
    #         if MethodId.parse(mthId).create_interpreter('').interpet() is not None:
    #             if len(self.stack) > 0:
    #                 self.stack.pop()
    #     else:
    #         if MethodId.parse(mthId).create_interpreter([args]).interpet() is not None:
    #             if len(self.stack) > 0:
    #                 self.stack.pop()
    #     self.pc += 1
        
    def step_newarray(self, bc):
        """
        + * opr : "newarray"
          * * dim : <number>
            * type : <SimpleType>
            -- create a $dim - dimentional array of size $count and $type
            -- \{newarray\} ["count1","count2","..."] -> ["objectref"]
        """
        if bc["opr"] == "newarray":
            dim = bc["dim"]
            arrtype = bc["type"]
            size = [self.stack[0] for _ in range(dim)]
            arrnew = self.create_array(arrtype,size)
            self.heap[bc["type"]] = arrnew 
        self.pc += 1
            
    def step_array_store(self, bc):
        """
        + * opr : "array_store"
              * type : <JArrayType>
              -- load a $value of $type from an $arrayref array at index $index
              -- \{aastore\} ["arrayref","index"] -> ["value"]
        """
        value = self.stack.pop(0)
        index = self.stack.pop(0)
        arrayef = self.stack.pop(0)
        if arrayef is None:
            self.done = "null pointer"
        elif 0 <= index < len(arrayef):
            arrayef[index] = value
        elif index > len(arrayef):
            self.done = "out of bounds"
        self.pc += 1
        
    def step_arraylength(self, bc):
        """
        + * opr : "arraylength"
          * <empty>
            -- finds the length of an array
            -- \{arraylength\} ["array"] -> ["length"]
        """
        if any(isinstance(s,list) for s in self.stack):
            uddata = list(filter(lambda x: isinstance(x,list), self.stack))[0]
            self.stack.insert(0,len(uddata))
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
                    self.done = "divide by zero"
            case "rem":
                result = left % right
        self.stack.insert(0, result)
        self.pc += 1

    def step_incr(self, bc): # Missing formal rules 
        amount = bc["amount"]
        index = bc["index"]
        value_to_be_incremented = self.stack.pop(index)
        value_to_be_incremented += amount
        self.stack.insert(0, value_to_be_incremented)

    # START :: HELPER METHODS/FUNCTIONS
    def if_match_result(self, condition: str, value1, value2, operant: str) -> bool:
        if isinstance(value1, list):
            value1 = len(value1)
        if isinstance(value2, list):
            value2 = len(value2)
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
        
    def create_array(self, arrtype, sizes):
        if len(sizes) == 1:
            return [None] * sizes[0]
        else:
            x = sizes[0]
            xs = sizes[1:]
            return [self.create_array(arrtype, xs) for _ in range(x)]
            
    # END :: HELPER METHODS/FUNCTIONS


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
