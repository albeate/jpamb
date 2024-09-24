#!/usr/bin/env python3
""" The skeleton for writing an interpreter given the bytecode.
"""

from dataclasses import dataclass
import sys, logging
from typing import Optional

from jpamb_utils import InputParser, IntValue, CharValue, MethodId

l = logging
l.basicConfig(level=logging.DEBUG, format="%(message)s")

# Some useful CLI copy pasta. Golden log can be useful to look at when trying to debug
# Test all cases: python bin/test.py -o golden.log -- python solutions/interpret_week3.py
# Test cases but filter by methods: python bin/test.py --filter-methods=divideByN\: -o golden.log -- python solutions/interpret_week3.py
# Test one method: python solutions/interpret_week3.py 'jpamb.cases.Simple.divideByN:(I)I' '(2)'

@dataclass
class SimpleInterpreter:
    bytecode: list
    locals: list
    stack: list
    pc: int = 0
    done: Optional[str] = None

    def interpet(self, limit=200):
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

    #######################################################
    # OPERATOR METHODS
    #######################################################
    def step_push(self, bc):
        val = bc["value"]
        if val is not None:
            type = val["type"]
            match type:
                case "integer":
                    # val = IntValue(val["value"])
                    val = val["value"]
                case _:
                    raise ValueError(f"type {type} is not implemented for step_push.")

        self.stack.insert(0, val)
        self.pc += 1

    def step_return(self, bc):
        if bc["type"] is not None:
            self.stack.pop(0)

        self.done = "ok"

    def step_get(self, bc): 
        field_name = bc["field"]["name"]
        match field_name:
            case "$assertionsDisabled":
                result = False # Hardcoded for now
            case _:
                raise ValueError(f"step_get not implemented for {field_name}")
            
        self.stack.insert(0, result)
        self.pc += 1

    def step_goto(self, bc):
        self.pc = bc["target"]

    def step_ifz(self, bc): 
        condition = bc["condition"]
        right = 0
        left = self.stack.pop(0)

        result = self.compute_if_operation(condition, left, right, "ifz")
        self.pc = bc["target"] if result else self.pc + 1

    def step_if(self, bc): 
        condition = bc["condition"]
        right = self.stack.pop(0)
        left = self.stack.pop(0)

        result = self.compute_if_operation(condition, left, right, "if")
        self.pc = bc["target"] if result else self.pc + 1

    def step_dup(self, bc): 
        if len(self.stack) > 0 and self.stack[0] == "new java/lang/AssertionError()":
           pass # Hardcoded for now, should this be done?, maybe not
        else: 
            self.stack.insert(0, self.stack[0])
        self.pc += 1

    def step_load(self, bc):
        variable_to_load = self.locals[bc["index"]]
        self.stack.insert(0, variable_to_load)
        self.pc += 1

    def step_store(self, bc):
        variable_to_store = self.stack.pop(0)
        self.locals.insert(bc["index"], variable_to_store)
        self.pc += 1

    def step_new(self, bc):
        class_name = bc["class"]

        new_object = f"new {class_name}()"
        self.stack.insert(0, new_object)
        self.pc += 1

    def step_throw(self, bc):
        self.done = self.stack.pop(0)
        self.pc += 1

    def step_newarray(self, bc):
        dim = bc["dim"]
        arrtype = bc["type"]
        size = [self.stack[0] for _ in range(dim)]
        arrnew = self.create_array(arrtype,size)

        # TODO handle type in regards to the new types from kalhauge

        self.stack.insert(0, arrnew)
        self.pc += 1

    def step_array_store(self, bc):
        value = self.stack.pop(0)
        index = self.stack.pop(0)
        arrayef = self.stack.pop(0)

        # TODO array store has a type, which must be converted to IntVar or CharVar etc.

        if arrayef is None:
            self.done = "null pointer"
        elif index >= len(arrayef):
            self.done = "out of bounds"
        elif 0 <= index < len(arrayef):
            arrayef[index] = value
        else:
            ValueError(f"Could not store array {arrayef}")

        self.pc += 1

    def step_array_load(self, bc):
        index = self.stack.pop(0)
        arrayef = self.stack.pop(0)

        # TODO array load has a type, which must be handled in regards to IntVar or CharVar etc.

        if arrayef is None:
            self.done = "null pointer"
        elif index >= len(arrayef):
            self.done = "out of bounds"
        elif 0 <= index < len(arrayef):
            self.stack.insert(0, arrayef[index])
        else:
            ValueError(f"Could not load array {arrayef}")
            
        self.pc += 1

    def step_arraylength(self, bc):
        array = self.stack.pop(0)

        if array is None:
            self.done = "null pointer"
        else:
            self.stack.insert(0, len(array))

        self.pc += 1

    def step_binary(self, bc): 
        right = self.stack.pop(0)
        left = self.stack.pop(0)
        
        result = self.compute_binary_operation(bc["operant"], right, left)
        result = self.convert_values_to_typed_value(right, result)

        self.stack.insert(0, result)
        self.pc += 1

    def step_incr(self, bc): 
        amount = bc["amount"]
        index = bc["index"]

        value = self.stack.pop(index) # Sometimes this is empty? why though, that is a mystery

        new_value = self.convert_values_to_int_value(value)
        new_value += amount

        incremented_value = self.convert_values_to_typed_value(new_value, value)

        self.stack.insert(index, incremented_value)
        self.pc += 1

    def step_cast(self, bc):
        value = self.stack.pop(0)
        
        target_type = bc["to"]
        
        if target_type == "short":
            cast_value = self.int_to_short(value)
        elif target_type == "byte":
            cast_value = self.int_to_byte(value)
        elif target_type == "char":
            cast_value = self.int_to_char(value)

        self.stack.insert(0, cast_value)
        
        self.pc += 1

    def step_invoke(self, bc):
        cls = bc["method"]["ref"]["name"]
        if cls == 'java/lang/AssertionError':
            self.stack.insert(0, "assertion error")
            # self.stack.pop(0)       
            # # self.stack.insert(0,False)
            # self.stack.insert(0,"assertion error")
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
                bytecode = MethodId.parse(method_name).load()["code"]["bytecode"]
                print("invoke_bytecode:= ", bytecode)
                sub_method = self.execute_bytecode(bytecode) # arbejder på det
                if sub_method is not None:
                    self.stack.pop()
        self.pc += 1

    #######################################################
    # HELPER METHODS
    #######################################################
    def execute_bytecode(self, bytecode):
        for instruction in bytecode:
            # print("execute_bytecode_instruction :=", instruction)
            # print("execute_bytecode_self.pc :=", self.pc)
            next = instruction
            if fn := getattr(instruction, "step_" + next["opr"], None):
                fn(next)
    
    def compute_binary_operation(self, opr: str, right, left):
        right = self.convert_values_to_int_value(right)
        left = self.convert_values_to_int_value(left)

        result = 0
        match opr:
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

        return result
    
    def compute_if_operation(self, condition: str, value1, value2, operant: str) -> bool:
        value1 = self.convert_values_to_int_value(value1)
        value2 = self.convert_values_to_int_value(value2)

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
    
    def convert_values_to_int_value(self, typed_value):
        if isinstance(typed_value, CharValue):
            typed_value = typed_value.tolocal().value # remove value when properly handling types
        elif isinstance(typed_value, int):
            pass
        elif isinstance(typed_value, IntValue):
            typed_value = typed_value.value
        else:
            raise ValueError(f"typed_value {typed_value} is not implemented.")

        return typed_value

    def convert_values_to_typed_value(self, original, modified):
        result = None
        if isinstance(original, IntValue):
            result = IntValue(modified)
        elif isinstance(original, CharValue):
            result = CharValue(modified)
        elif isinstance(original, int):
            result = modified
        else:
            raise ValueError(f"typed value {original} is not implemented.")

        return result

    def create_array(self, arrtype, sizes):
        if len(sizes) == 1:
            return [None] * sizes[0]
        else:
            x = sizes[0]
            xs = sizes[1:]
            return [self.create_array(arrtype, xs) for _ in range(x)]
        
    def int_to_short(self, value):
        value &= 0xFFFF  
        if value > 32767:
            value -= 0x10000
        return value

    def int_to_byte(self, value):
        value &= 0xFF 
        if value > 127:
            value -= 0x100 
        return value

    def int_to_char(self, value):
        value &= 0xFFFF 
        return value

#######################################################
# ENTRYPOINT
#######################################################
if __name__ == "__main__":
    methodid = MethodId.parse(sys.argv[1])
    inputs = InputParser.parse(sys.argv[2])
    m = methodid.load()
    i = SimpleInterpreter(m["code"]["bytecode"], [i.tolocal() for i in inputs], [])
    print(inputs)
    print(i.interpet())
