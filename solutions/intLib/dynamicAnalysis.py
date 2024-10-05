#!/usr/bin/env python3

import interpret as ip

methodid = ip.MethodId.parse('jpamb.cases.Simple.checkBeforeDivideByN2:(I)I')
inputs = ip.InputParser.parse('(0)')
m = methodid.load()