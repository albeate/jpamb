#!/usr/bin/env python3

from dataclasses import dataclass
from typing import TypeAlias, Literal

from hypothesis import given
from hypothesis.strategies import integers, sets

Sign : TypeAlias = Literal["+"] | Literal["-"] | Literal["0"]

@dataclass
class SignSet:
  signs : set[Sign]
  
  def __contains__(self, member : int): 
      if (member == 0 and "0" in self.signs): 
          return true
  @staticmethod
  def abstract(items : set[int]):
      return SignSet(...)

  @given(sets(integers()))
  def test_valid_abstraction(xs):
      s = SignSet.abstract(xs) 
      assert all(x in s for x in xs)