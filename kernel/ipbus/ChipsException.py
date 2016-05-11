'''
Exceptions specific to the PyChips package.

@author: Robert Frazier

March 2011
'''



class ChipsException(Exception):
  """Base exception for all PyChips exceptions"""
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return str(self.value)
