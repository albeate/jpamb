#!/usr/bin/env python3

"""
https://docs.python.org/3/library/dataclasses.html

dataclass := 
>> dataclasses.dataclass(*, init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False, match_args=True, kw_only=False, slots=False, weakref_slot=False)
>> The @dataclass decorator examines the class to find fields. A field is defined as a class variable that has a type annotation. With two exceptions described below, nothing in @dataclass examines the type specified in the variable annotation.
The order of the fields in all of the generated methods is the order in which they appear in the class definition.
The @dataclass decorator will add various “dunder” methods to the class, described below. If any of the added methods already exist in the class, the behavior depends on the parameter, as documented below. The decorator returns the same class that it is called on; no new class is created.

field := 
>> dataclasses.field(*, default=MISSING, default_factory=MISSING, init=True, repr=True, hash=None, compare=True, metadata=None, kw_only=MISSING)
>> For common and simple use cases, no other functionality is required. There are, however, some dataclass features that require additional per-field information. To satisfy this need for additional information, you can replace the default field value with a call to the provided field() function. For example:
"""
from dataclasses import dataclass, field
from typing import TypeAlias, Literal

from hypothesis import given
from hypothesis.strategies import integers, sets
from random import randrange, sample

# Define Sign as a type alias that can be "+", "-", or "0"
Sign: TypeAlias = Literal["+"] | Literal["-"] | Literal["0"]

@dataclass
class SignSet:
    # 'signs' is a set of 'Sign' elements, initialized as an empty set by default
    signs: set[Sign] = field(default_factory=set)
    
    def add(self, sign: Sign) -> None:
        """
        Adds a sign to the set. The set automatically handles duplicates.
        """
        if sign == 0:
             self.signs.add("0")
        elif sign > 0:
            self.signs.add("+")
        elif sign < 0: 
            self.signs.add("-")     
        #self.signs.add(sign)

    def remove(self, sign: Sign) -> None:
        """
        Removes a sign from the set if it exists.
        """
        self.signs.discard(sign)  # Discard does not raise an error if the sign is absent

    def contains(self, sign: Sign) -> bool:
        """
        Checks if the set contains a specific sign.
        :return: True if the sign is in the set, False otherwise.
        """
        if sign == 0 and "0" in self.signs:
            return True
        elif sign > 0 and "+" in self.signs:
            return True
        elif sign < 0 and "-" in self.signs:
            return True
        else:
            return False 
        #return sign in self.signs

    def size(self) -> int:
        """
        Returns the size of the set.
        :return: The number of elements in the set.
        """
        return len(self.signs)

    def is_empty(self) -> bool:
        """
        Checks if the set is empty.
        :return: True if the set has no elements, False otherwise.
        """
        return len(self.signs) == 0

    def clear(self) -> None:
        """
        Clears all signs from the set.
        """
        self.signs.clear()
    
    #def poset(self, sign: Sign) -> bool:
    def poset(self) -> bool:
        """
        reflexive := every element is related to itself
        antisymetric := no two distinct elements precede each other
        transitive := if a <= b and b <= c then a <= c
        
        set.issubset(other) := set <= other 
        >> test whether every element in the set is in other
        """
        return self.signs.issubset(self.signs)

    @staticmethod
    def abstract(items : set[int]): 
        # mangler at få lavet den her del
        return SignSet(items)
    
    @given(sets(integers(), min_size=3, max_size=10))
    def test_valid_abstraction(xs):
        s = SignSet.abstract(xs) 
        assert all(x in s for x in xs)
    
# Example usage
if __name__ == "__main__":
    # print(SignSet.test_valid_abstraction())
    sign_set = SignSet()
    c = 11
    while c > 0:
        sign_set.add(randrange(-11,11))
        c -= 1
    print(sign_set.signs)          # Output: {'+', '-'}
    print(sign_set.contains(2))   # Output: True
    print(sign_set.poset(sign_set.signs))
    print(sign_set.size())         # Output: 2
    sign_set.remove(2)
    print(sign_set.signs)          # Output: {'-'}
    print(sign_set.is_empty())   # Output: False
    sign_set.clear()
    print(sign_set.is_empty())   # Output: True
    
