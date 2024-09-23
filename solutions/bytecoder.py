#!/usr/bin/env python3
""" A very stupid syntatic bytecode analysis, that only checks for assertion errors.
"""

import sys, logging
from jpamb_utils import MethodId

l = logging
l.basicConfig(level=logging.DEBUG)

(name,) = sys.argv[1:]

l.debug("check assertion")
l.debug("read the method name")
method = MethodId.parse(name)

l.debug("looking up method")
m = method.load()

l.debug("trying to find an assertion error being created")
for inst in m["code"]["bytecode"]:
    if (
        inst["opr"] == "invoke"
        and inst["method"]["ref"]["name"] == "java/lang/AssertionError"
    ):
        break
else:
    # I'm pretty sure the answer is no
    l.debug("did not find it")
    print("assertion error;20%")
    sys.exit(0)

l.debug("Found it")
# I'm kind of sure the answer is yes.
print("assertion error;80%")
