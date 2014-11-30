import collections
from sudoku import *

def squareToBox(s):
  bu = [u for u in boxUnits if s in u][0]
  return unitName[tuple(bu)]

def countEmptyUnitSqs(values):
  emptyUnitSqs = collections.Counter()
  for u in unitlist:
    emptyUnitSqs[tuple(u)] = sum(1 for s in u if len(values[s]) > 1)
  return emptyUnitSqs

def countUnitOptions(values):
  unitOpts = collections.Counter()
  for u in unitlist:
    unitOpts[tuple(u)] = sum(len(values[s]) for s in u if len(values[s]) > 1)
  return unitOpts

def computeOptUnitFreq(values):
  unitFreqs = {}
  for u in unitlist:
    unitFreqs[tuple(u)] = \
        collections.Counter(''.join(values[s] for s in u if len(values[s]) > 1))
  return unitFreqs

def extractFeatures(values, s, v, emptyUnitSqs, unitOpts, optionUnitFreq):
  fKeyVals = {}

  emptySqs = sum(1 for s1 in squares if len(values[s1]) > 1)
  if emptySqs <= 5:
    fKeyVals["EmptySqs<=5"] = 1
  elif emptySqs <= 25:
    fKeyVals["EmptySqs<=25"] = 1

  # For a given empty square, how many other squares are empty in the same
  # column, row or box.
  for u in units[s]:
    cnt = emptyUnitSqs[tuple(u)]
    if cnt == 1:
      fKeyVals["EmptyUnitSqs-" + unitType[tuple(u)] + '=1'] = 1
    elif cnt <= 3:
      fKeyVals["EmptyUnitSqs-" + unitType[tuple(u)] + '<=3'] = 1
    else:
      fKeyVals["EmptyUnitSqs-" + unitType[tuple(u)] + '>3'] = 1
    
  # Number of options in each unit
  for u in units[s]:
    cnt = unitOpts[tuple(u)]
    if cnt < 2:
      continue
    elif cnt == 2:
      fKeyVals["UnitOptions-" + unitType[tuple(u)] + '==2'] = 1
    elif cnt <= 8:
      fKeyVals["UnitOptions-" + unitType[tuple(u)] + '<=8'] = 1
    else:
      fKeyVals["UnitOptions-" + unitType[tuple(u)] + '>8'] = 1
    
  # Number of option in the given sqaure  
  sqOpts = len(values[s])
  if sqOpts == 2:
    fKeyVals["SqOptions" + '=2'] = 1
  elif sqOpts <= 4:
    fKeyVals["SqOptions" + '<=4'] = 1
  else:
    fKeyVals["SqOptions" + '>4'] = 1

  # Is this the most constrained square
  minOpts = min(len(values[s1]) for s1 in squares if len(values[s1]) > 1)    
  if sqOpts == minOpts:
    fKeyVals["MCVar"] = 1

  
  optionPeerFreq = collections.Counter(''.join(values[s1] for s1 in peers[s]
                                               if len(values[s1]) > 1))
  for v1 in values[s]:
    optionPeerFreq[v1] += 1

  # v has min freq among other digits in s across peers of s
  if optionPeerFreq[v] == min(optionPeerFreq.values()):
    fKeyVals["LCVal"] = 1

  # freq of v
  print v, optionPeerFreq
  if optionPeerFreq[v] == 2:
    fKeyVals["OptFreq-in-Peers" + "=2"] = 1
  elif optionPeerFreq[v] <= 8:
    fKeyVals["OptFreq-in-Peers" + "<=8"] = 1
  else:
    fKeyVals["OptFreq-in-Peers" + ">8"] = 1

  return fKeyVals      


def mlDataSearch(values, perfMetric, dataFile):
  "Alternate between DFS and Constraint Propagation"
  if values is False:
    return False ## Failed earlier
  if all(len(values[s]) == 1 for s in squares):
    return values ## Solved!

  emptyUnitSqs = countEmptyUnitSqs(values)
  unitOpts = countUnitOptions(values)
  optionUnitFreq = computeOptUnitFreq(values)

  ## DFS: choose unfilled square s with fewest possibilities
  sqs = zip(*sorted((len(values[s]), s) 
                    for s in squares if len(values[s]) > 1))[1]

  """if random.randint(0, 1) == 0:
    n, s = min((len(values[s]), s) for s in squares if len(values[s]) > 1)

  else:
    s = random.sample([s for s in squares if len(values[s]) > 1], 1)[0]"""

  options = leastConstrainingValue(values, s)
  """if random.randint(0, 1) == 0:
    options = leastConstrainingValue(values, s)
  else:
     options = shuffledOptions(values, s)"""

  bestValues = False
  bestMetric = 2 ** 30
  j = 0
  for s in sqs[:4]:
    i = 0
    solnFound = False
    for d in options:
      i += 1
      if not solnFound: j += 1
      localPerfMetric = {}
      values2 = mlDataSearch(assign(values.copy(), s, d), localPerfMetric)
      if values2: solnFound = True
      if (not bestValues and values2) or \
            localPerfMetric['options'] < bestMetric['options']:
        bestValues, bestMetric = (values2, localPerfMetric)
      f = extractFeatures(values, s, d, emptyUnitSqs, unitOpts, optionUnitFreq)
      dataFile.write(','.join([k + ':' + str(v) for k,v in f.items()]) + " " +
                     str(localPerMetric['options']) + " " +
                     (1 if values2 else 0))
      if i >= 4 and bestValues: break

  avgOptsExplored = j/4
  perfMetric['options'] = bestMetric['options'] + avgOptsExplored
  perfMetric['squares'] = bestMetric['squares'] + 1
  return bestValues

