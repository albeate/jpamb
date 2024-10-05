#!/usr/bin/env python3

import re

# Define the string
string = "jpamb.cases.Arrays.arraySometimesNull:(I)V"

# Define the regex pattern
pattern = r'^(.*)\.(.*):\(([^)]+)\)(\w)$'

# Perform the match
match = re.match(pattern, string)

# Extract and print the groups if a match is found
if match:
    group1 = match.group(1)  # jpamb.cases.Arrays
    group2 = match.group(2)  # arraySometimesNull
    group3 = match.group(3)  # I (or I, B)
    group4 = match.group(4)  # V
    
    print(f"Group 1: {group1}")
    print(f"Group 2: {group2}")
    print(f"Group 3: {group3}")
    print(f"Group 4: {group4}")
else:
    print("No match found")
