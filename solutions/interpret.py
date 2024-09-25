#!/usr/bin/env python3
""" The skeleton for writing an interpreter given the bytecode.
"""

from dataclasses import dataclass
import sys, logging
from typing import Optional

from jpamb_utils import InputParser, IntValue, CharValue, BoolValue, JvmType, MethodId

l = logging
l.basicConfig(level=logging.DEBUG, format="%(message)s")

# Some useful CLI copy pasta. Golden log can be useful to look at when trying to debug
# Test all cases: python bin/test.py -o golden.log -- python solutions/interpret.py
# Test cases but filter by methods: python bin/test.py --filter-methods=divideByN\: -o golden.log -- python solutions/interpret.py
# Test one method: python solutions/interpret.py 'jpamb.cases.Simple.divideByN:(I)I' '(2)'

@dataclass
class SimpleInterpreter:
    bytecode: list
    locals: list
    stack: list
    pc: int = 0
    current_iteration: int = 0
    state = []
    done: Optional[str] = None

    def interpet(self, current_iteration=0, max_iterations=5000):
        running_state = []
        state_cycles = []

        limit = max_iterations - current_iteration
        self.current_iteration = current_iteration

        for i in range(limit):
            next = self.bytecode[self.pc]
            l.debug(f"STEP {i}:")
            l.debug(f"  PC: {self.pc} {next}")
            l.debug(f"  LOCALS: {self.locals}")
            l.debug(f"  STACK: {self.stack}")

            current_pc = self.pc
            self.current_iteration += 1

            if fn := getattr(self, "step_" + next["opr"], None):
                fn(next)
            else:
                return f"can't handle {next['opr']!r}"

            running_state.append([self.pc, next["opr"], self.locals, self.stack])
            self.state.append([i, running_state])

            if next["opr"] == "goto" and next["target"] != current_pc:
                state_cycles.append(running_state)
                running_state = []

            if i == int(limit * 0.33) or i == int(limit * 0.66) or i == int(limit * 0.99):
                self.detect_repeated_cycle_groups(state_cycles)

            if self.done:
                break
        else:
            self.done = "out of time"

        l.debug(f"DONE {self.done}")
        l.debug(f"  LOCALS: {self.locals}")
        l.debug(f"  STACK: {self.stack}")
        # l.debug(f"\nSTATE:\n{self.state}")
        # l.debug(f"\nSTATE CYCLES:\n{state_cycles}")

        return self.done
    
    def detect_repeated_cycles(self, cycles, loop_cycle_limit=5):
        for i in range(len(cycles)): # len(cycles) to see all
            for j in range(i + 1, len(cycles)):
                if self.compare_cycles(cycles[i], cycles[j]):
                    l.debug(f"Cycle {i} and cycle {j} are identical.")
                else:
                    l.debug(f"Cycle {i} and cycle {j} are not identical.")

    def detect_repeated_cycle_groups(self, cycles, group_size=5):
        total_cycles = len(cycles)

        if total_cycles < group_size + 5:
            l.debug(f"Not enough cycles to compare {group_size}-cycle groups.")
            return

        last_group = cycles[-group_size:]
        
        for i in range(total_cycles - group_size, group_size - 1, -group_size):
            previous_group = cycles[i - group_size:i]
            
            if not self.compare_groups(last_group, previous_group):
                l.debug(f"Last group of {group_size} cycles does not match previous group.")
                return
        
        l.debug(f"The last {group_size} cycles are identical to the previous sets of {group_size} cycles.")
        self.done = "*"

    def compare_groups(self, group1, group2):
        if len(group1) != len(group2):
            return False

        for cycle1, cycle2 in zip(group1, group2):
            if not self.compare_cycles(cycle1, cycle2):
                return False
        return True

    def compare_cycles(self, cycle1, cycle2):
        if len(cycle1) != len(cycle2):
            return False
        for state1, state2 in zip(cycle1, cycle2):
            if state1[0] != state2[0]:  # pc comparison
                return False
            if state1[1] != state2[1]:  # opr comparison
                return False
            if state1[2] != state2[2]:  # locals comparison
                return False
            if state1[3] != state2[3]:  # stack comparison
                return False
        return True

    #######################################################
    # OPERATOR METHODS
    #######################################################
    def step_push(self, bc):
        val = bc["value"]
        if val is not None:
            type = val["type"]
            match type:
                case "integer":
                    val = IntValue(val["value"])
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
                result = BoolValue(False) # Hardcoded for now
            case _:
                raise ValueError(f"step_get not implemented for {field_name}")
            
        self.stack.insert(0, result)
        self.pc += 1

    def step_goto(self, bc):
        if self.pc == bc["target"]:
            self.done = "*"
        else:
            self.pc = bc["target"]

    def step_ifz(self, bc): 
        condition = bc["condition"]
        right = 0
        left = self.get_typed_value_value(self.stack.pop(0))

        result = self.compute_if_operation(condition, left, right, "ifz")
        self.pc = bc["target"] if result else self.pc + 1

    def step_if(self, bc): 
        condition = bc["condition"]
        right = self.get_typed_value_value(self.stack.pop(0))
        left = self.get_typed_value_value(self.stack.pop(0))

        result = self.compute_if_operation(condition, left, right, "if")
        self.pc = bc["target"] if result else self.pc + 1

    def step_dup(self, bc): 
        if len(self.stack) > 0 and self.stack[0] == "new java/lang/AssertionError()":
           pass # Hardcoded for now, should this be done?, maybe not
        else: 
            self.stack.insert(0, self.stack[0])
        self.pc += 1

    def step_load(self, bc):
        index = bc["index"]
        variable_to_load = self.locals[index]
        self.stack.insert(0, variable_to_load)
        self.pc += 1

    def step_store(self, bc):
        index = bc["index"]
        variable_to_store = self.stack.pop(0)
        if len(self.locals) > index:
            self.locals[index] = variable_to_store
        else:
            self.locals.insert(index, variable_to_store)
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

        arrnew = self.create_array_recursively(arrtype, size)

        self.stack.insert(0, arrnew)
        self.pc += 1

    def step_array_store(self, bc):
        value = self.stack.pop(0)
        index = self.get_typed_value_value(self.stack.pop(0))
        arrayef = self.stack.pop(0)

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
        index = self.get_typed_value_value(self.stack.pop(0))
        arrayef = self.stack.pop(0)

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
            self.stack.insert(0, IntValue(len(array)))

        self.pc += 1

    def step_binary(self, bc): 
        right = self.get_typed_value_value(self.stack.pop(0))
        left = self.get_typed_value_value(self.stack.pop(0))
        
        type = bc["type"]
        opr = bc["operant"]

        result = None
        match type:
            case "int":
                value = int(self.compute_binary_operation(opr, right, left, type))
                result = IntValue(value)
            case _:
                raise ValueError(f"type {type} not implemented.")

        self.stack.insert(0, result)
        self.pc += 1

    def step_incr(self, bc): 
        amount = bc["amount"]
        index = bc["index"]
        
        value_type = self.locals.pop(index)

        new_value = self.get_typed_value_value(value_type)
        new_value += amount

        incremented_value = None
        if isinstance(value_type, IntValue):
            incremented_value = IntValue(new_value)
        elif isinstance(value_type, CharValue):
            incremented_value = CharValue(new_value)
        else:
            raise ValueError(f"typed value {value_type} is not implemented.")

        self.locals.insert(index, incremented_value)
        self.pc += 1

    def step_cast(self, bc):
        value = self.get_typed_value_value(self.stack.pop(0))
        
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
        else:
            name = bc["method"]["name"]
            args = bc["method"]["args"]
            returns = bc["method"]["returns"]

            INV_TYPE_LOOKUP: dict[JvmType, str] = {
                "boolean": "Z",
                "int": "I",
                "char": "C",
                "int[]": "[I",  # ]
                "char[]": "[C",  # ]
                "null": "V",
                "None": "V"
            }

            arg_type = ""
            if args:
                arg_type = "".join(INV_TYPE_LOOKUP[arg] for arg in args if arg in INV_TYPE_LOOKUP)

            return_type = ""
            if returns:
                if isinstance(returns, str):
                    return_type = "".join(INV_TYPE_LOOKUP[returns])
                else:
                    returnss = returns["type"]
                    if returns["kind"] == "array":
                        returnss += "[]"
                    
                    return_type = "".join(INV_TYPE_LOOKUP[returnss])
            else:
                return_type = "".join(INV_TYPE_LOOKUP["None"])

            method_locals = self.stack

            method_name = cls.replace('/','.')+'.'+name+':('+arg_type+')'+return_type
            bc2 = MethodId.parse(method_name).load()["code"]["bytecode"] 
            # l.debug(bc2)

            l.debug("## Entering a method")
            i2 = SimpleInterpreter(bc2, method_locals, [], 0)
            i2.interpet(self.current_iteration)
            l.debug("## Leaving a method")

            if i2.done and i2.done != "ok":
                self.done = i2.done

        self.pc += 1

    #######################################################
    # HELPER METHODS
    #######################################################    
    def compute_binary_operation(self, opr: str, right, left, type: str):
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
    
    def get_typed_value_value(self, value):
        if isinstance(value, int):
            return value
        elif isinstance(value, CharValue):
            return value.tolocal()
        else:
            return value.value

    def create_array_recursively(self, arrtype, sizes):
        value = self.get_typed_value_value(sizes[0])
        if len(sizes) == 1:
            match arrtype:
                case "int":
                    return [IntValue(None) for _ in range(value)]
                case "char":
                    return [CharValue(None) for _ in range(value)]
                case _:
                    raise ValueError(f"array type {arrtype} is not implemented.")
        else:
            x = sizes[0]
            xs = sizes[1:]
            return [self.create_array_recursively(arrtype, xs) for _ in range(x)]
        
    def int_to_short(self, value):
        value &= 0xFFFF  
        if value > 32767:
            value -= 0x10000
        return IntValue(value) # Maybe there will be a ShortValue in the future? There is none atm

    def int_to_byte(self, value):
        value &= 0xFF 
        if value > 127:
            value -= 0x100 
        return IntValue(value) # Maybe there will be a ByteValue in the future? There is none atm

    def int_to_char(self, value):
        value &= 0xFFFF 
        return CharValue(value)

#######################################################
# ENTRYPOINT
#######################################################
if __name__ == "__main__":
    methodid = MethodId.parse(sys.argv[1])
    inputs = InputParser.parse(sys.argv[2])
    m = methodid.load()
    i = SimpleInterpreter(m["code"]["bytecode"], [i.tolocal() for i in inputs], [])
    print(i.interpet())
