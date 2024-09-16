#!/usr/bin/env python3
""" The skeleton for writing an interpreter given the bytecode.
"""

from dataclasses import dataclass
from pathlib import Path
import sys, logging
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
            pc=0,
        )


@dataclass
class SimpleInterpreter:
    bytecode: list
    locals: list
    stack: list
    pc: int
    done: Optional[str] = None

    def interpet(self, limit=10):
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

    def step_push(self, bc):
        self.stack.insert(0, bc["value"]["value"])
        self.pc += 1

    def step_return(self, bc):
        if bc["type"] is not None:
            self.stack.pop(0)
        self.done = "ok"


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
    print(methodid.create_interpreter(inputs).interpet())
