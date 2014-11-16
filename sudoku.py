from collections import *
import time
import random
from logicStrategies.py import *
from heuristics import *

HEURISTICS_ENABLED = 1
LOGIC_STRATEGIES = 1
ex = [1]
#
# Game definition
#

def cross(A, B):
  "Cross product of elements in A with elements in B"
  return [a + b for a in A for b in B]

digits = "123456789"
rows = "ABCDEFGHI"

cols = digits
squares = cross(rows, cols)
colUnits = [cross(rows, c) for c in cols]
rowUnits = [cross(r, cols) for r in rows]
boxUnits = [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI')
            for cs in ('123', '456', '789')]
unitlist = colUnits + rowUnits + boxUnits
units = dict((s, [u for u in unitlist if s in u]) for s in squares)
peers = dict((s, set(sum(units[s],[]))-set([s])) for s in squares)

            
def test():
    "A set of unit tests."
    assert len(squares) == 81
    assert len(unitlist) == 27
    assert all(len(units[s]) == 3 for s in squares)
    assert all(len(peers[s]) == 20 for s in squares)
    assert units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'],
                           ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'],
                           ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']]
    assert peers['C2'] == set(['A2', 'B2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2',
                               'C1', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9',
                               'A1', 'A3', 'B1', 'B3'])
    print 'All tests pass.'

#
# Constraint Propagation
#

def parse_grid(grid):
  """ Convert grid to a dict of posible values, {square:digits} or return
  return False if a contradiction is detected."""
  ## To start, every square can be any digit; then assign values from the grid
  values = dict((s, digits) for s in squares)
  for s, d in grid_values(grid).items():
    if d in digits and not assign(values, s, d):
      return False ## Fail if we could not assign d to square s
  return values

def grid_values(grid):
  "Convert grid into a {squares: char} map with '0' or '.' for empties"
  chars = [c for c in grid if c in digits or c in '0.']
  assert len(chars) == 81
  return dict(zip(squares, chars))

def assign(values, s, d):
  otherValues = values[s].replace(d, '')
  if all(eliminate(values, s, d2) for d2 in otherValues):
    return values
  else:
    return False

def eliminate(values, s, d):
  if d not in values[s]:
    return values ## Already gone
  values[s] = values[s].replace(d, '')
  if len(values[s]) == 0:
    return False ## Contradiction: removed last value
  if not CPRule1(values, s):
    return False
  for u in units[s]:
    if not CPRule2(values, u, d):
      return False
  if LOGIC_STATEGIES:
    if not eliminateByLogicStrategies(values, s, d):
      return False
  return values

## CP rule 1: if a square is reduced to only one value, then eliminate that
## value from peers of that square
def CPRule1(values, s):
  if len(values[s]) == 1:
    d2 = values[s]
    if ex[0] == 1: #example
      print "before CP1", s, values[s]
      display(values)
    if not all(eliminate(values, s2, d2) for s2 in peers[s]):
      return False
    if ex[0] == 1: #example
      print "after CP1"
      display(values)
      ex[0] = 2
  return values  

## CP rule 2: if a unit has only one place left for a value, then put it there
def CPRule2(values, unit, d):
  dplaces = [s for s in unit if d in values[s]]
  if len(dplaces) == 0:
    return False ## Contradiction: removed last value
  elif len(dplaces) == 1:
    if ex[0] == 2 and len(values[dplaces[0]]) > 1: #example
      print "before CP2 ", dplaces[0], d
      display(values)
      ex[0] = 3
    if not assign(values, dplaces[0], d):
      return False
    if ex[0] == 3: #example
      print "after CP2 "
      display(values)
      ex[0] = 4
  return values  

# Grid Display
def display(values):
  "Display these values as a grid"
  width = 1 + max(len(values[s]) for s in squares)
  line = "+".join(['-' *(width*3)]*3)
  for r in rows:
    print ''.join(values[r+c].center(width) + ('|' if c in '36' else '')
                  for c in cols)
    if r in 'CF': print line
  print

def display2(values):
  "Display these values as a grid"
  width = 1 + max(1 for s in squares)
  line = "+".join(['-' *(width*3)]*3)
  for r in rows:
    print ''.join((values[r+c] + ' ' if len(values[r+c]) == 1 else '. ') + ('|' if c in '36' else '')
                  for c in cols)
    if r in 'CF': print line
  print

def gridValuesToString(values):
  "Convert a grid disctionary into a string"
  return ''.join(values[r+c] if values[r+c] != 0 else '.'
                 for r in rows for c in cols)
#    
# Search
#

def solve(grid, perfMetric): return search(parse_grid(grid), perfMetric)

def search(values, perfMetric):
  "Alternate between DFS and Constraint Propagation"

  if HEURISTICS_ENABLED:
    return heuristicSearch(values, perfMetric)

  if values is False:
    return False ## Failed earlier
  if all(len(values[s]) == 1 for s in squares):
    return values ## Solved!

  ## DFS: choose unfilled square s with fewest possibilities
  n, s = min((len(values[s]), s) for s in squares if len(values[s]) > 1)

  perfMetric['squares'] += 1
  for d in values[s]:
    perfMetric['options'] += 1
    values2 = search(assign(values.copy(), s, d), perfMetric)
    if values2: return values2
  return False

def some(seq):
  "Return some element of sequence that is true"
  for e in seq:
    if e: return e
  return False


def solve_all(grids, name='', showif=0.0, writeFile=None):
  def time_solve(grid, f):
    start = time.clock()
    perfMetric = defaultdict(lambda: 0)
    values = solve(grid, perfMetric)
    t = time.clock() - start
    ## Display puzzles that take long enough
    if showif is not None and t > showif:
      display(grid_values(grid))
      if f: f.write(grid + '\n')
      if values: display(values)
      print "Performance Metric: ", perfMetric
      print '(%.2f seconds)\n' % t
    return (t, solved(values), perfMetric)
  f = None
  if writeFile: f = open(writeFile, 'w+')
  l = [time_solve(grid, f) for grid in grids]
  if f: f.close()
  #print l
  times, results, perf = zip(*l)
  N = len(grids)
  if N > 1:
    print "Solved %d of %d %s puzzles (avg %.2f secs (%d Hz), max %.2f secs)"%(
      sum(results), N, name, sum(times)/N, N/sum(times), max(times))
    print "Total exploration: %d squares, %d options" \
        % (sum([d['squares'] for d in perf]), sum([d['options'] for d in perf]))
  return times, perf

def solved(values):
  "A puzzle is solved if each unit is a permutation of the digits 1 to 9"
  def unitsolved(unit): return set(values[s] for s in unit) == set(digits)
  return values is not False and all(unitsolved(unit) for unit in unitlist)

def from_file(filename, sep='\n'):
  "Parse a file into a list of strings, separated by sep"
  return file(filename).read().strip().split(sep)

def random_puzzle(N=17):
  """Make a random puzzle with N or more assignments. Restart on contradictions.
  Note the reulting puzzle is not guaranteed to be solvable, but empirically,
  about 99.8% of them are solvable. Some have multiple solutions."""
  values = dict((s, digits) for s in squares)
  for s in shuffled(squares):
    if not assign(values, s, random.choice(values[s])):
      break
    ds = [values[s] for s in squares if len(values[s]) == 1]
    if len(ds) >= N and len(set(ds)) >= 8:
      return ''.join([values[s] if len(values[s]) == 1 else '.'
                      for s in squares])
  return random_puzzle(N) ## Give up and make a new puzzle

def shuffled(seq):
  "Return a randomly shuffled copy of the input sequence"
  seq = list(seq)
  random.shuffle(seq)
  return seq

grid1  = '003020600900305001001806400008102900700000008006708200002609500800203009005010300'
grid2  = '4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......'
hard1  = '.....6....59.....82....8....45........3........6..3.54...325..6..................'    

