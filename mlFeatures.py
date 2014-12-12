import collections
from sudoku import *
import os

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
    if cnt == 2:
      fKeyVals["EmptyUnitSqs-" + unitType[tuple(u)] + '=2'] = 1
    elif cnt <= 3:
      fKeyVals["EmptyUnitSqs-" + unitType[tuple(u)] + '<=4'] = 1
    else:
      fKeyVals["EmptyUnitSqs-" + unitType[tuple(u)] + '>4'] = 1
    
  # Number of options in each unit
  for u in units[s]:
    cnt = unitOpts[tuple(u)]
    if cnt < 2:
      continue
    elif cnt <= 5:
      fKeyVals["UnitOptions-" + unitType[tuple(u)] + '<=5'] = 1
    elif cnt <= 10:
      fKeyVals["UnitOptions-" + unitType[tuple(u)] + '<=10'] = 1
    else:
      fKeyVals["UnitOptions-" + unitType[tuple(u)] + '>10'] = 1
    
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
  if optionPeerFreq[v] == 3:
    fKeyVals["OptFreq-in-Peers" + "<=3"] = 1
  elif optionPeerFreq[v] <= 6:
    fKeyVals["OptFreq-in-Peers" + "<=6"] = 1
  else:
    fKeyVals["OptFreq-in-Peers" + ">6"] = 1

  return fKeyVals      

global boardId
boardId = 0

def mlDataSearch(values, perfMetric, dataFile, depth):
  "Alternate between DFS and Constraint Propagation"
  if values is False:
    return False ## Failed earlier
  if all(len(values[s]) == 1 for s in squares):
    return values ## Solved!
  global boardId

  emptyUnitSqs = countEmptyUnitSqs(values)
  unitOpts = countUnitOptions(values)
  optionUnitFreq = computeOptUnitFreq(values)

  ## Sort squares in descending order of contraint
  sqs = list(zip(*sorted((len(values[s]), s) 
                         for s in squares if len(values[s]) > 1))[1])

  # sample one in K grid configurations. Objective here is to sample
  # more grid configurations earlier (closer to the root) in the search tree.
  if depth <= 3:
    K = 2**depth * 2
  else:
    K = 2**depth * 16
  if random.randint(1,2**30) % K == 0:
    exploreWidth = 4
    boardId += 1
  else:
    exploreWidth = 1

  shuffledSqs = sqs[1:]
  random.shuffle(shuffledSqs)
  sampledSqs = sqs[:1] + shuffledSqs
  dataStr = ''
  bestValues = False
  bestMetric = {'options': 2 ** 30, 'squares': 0}
  optsExploredBeforeFirstSoln = 0
  for s in sampledSqs[:exploreWidth]:
    options = list(leastConstrainingValue(values, s))
    shuffledOpts = options[1:]
    random.shuffle(shuffledOpts)
    sampledOptions = options[:1] + shuffledOpts
    optsExplored = 0
    solnFound = False
    for d in sampledOptions:
      optsExplored += 1

      localPerfMetric = collections.defaultdict(lambda: 0)
      values2 = mlDataSearch(assign(values.copy(), s, d), localPerfMetric,
                             dataFile, depth+1)
      if values2: 
        if not solnFound:
          solnFound = True
          optsExploredBeforeFirstSoln += optsExplored

      if (not bestValues and values2) or \
            (not (bestValues and not values2) and
             localPerfMetric['options'] < bestMetric['options']):
        bestValues, bestMetric = (values2, localPerfMetric)

      if exploreWidth > 1:
        f = extractFeatures(values, s, d, emptyUnitSqs,
                            unitOpts, optionUnitFreq)
        dataStr += ','.join([k + ':' + str(v) for k,v in f.items()]) + " " + \
            str(localPerfMetric['options']) + " " + \
            str(1 if values2 else 0) + '\n'
      if optsExplored >= exploreWidth and bestValues: break

  avgOptsExplored = optsExploredBeforeFirstSoln/exploreWidth
  perfMetric['options'] = bestMetric['options'] + avgOptsExplored
  perfMetric['squares'] = bestMetric['squares'] + 1

  if exploreWidth > 1:
    dataFile.write('Board-ID ' + str(boardId) + ' ' + 
                   'Opts-explored:' + str(perfMetric['options']) + ' '
                   + 'treedepth:' + str(depth) + '\n')
    dataFile.write(dataStr)
    dataFile.flush()
    os.fsync(dataFile.fileno())

  return bestValues

