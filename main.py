from collections import *
import time
import random
from sudoku import *
from logicStrategies import *
from heuristics import *
from mlFeatures import *

if __name__ == '__main__':
  gs = from_file('rh.txt')
  solve_all(gs, showif=0.05)
