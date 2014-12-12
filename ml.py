import re
import collections
import random
from sudoku import *
from sklearn import linear_model
from sklearn import svm
from heuristics import *

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
  fKeyVals = collections.defaultdict(lambda: 0)

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

def readData(fileName):
  gridId = 0
  grids = {}
  featureKeys = set()
  for line in file(fileName):
    items = re.split('\s+', line.strip())
    print items
    if items[0] == 'Board-ID':
      gridId += 1
      grids[gridId] = []
      treeDepth = int(items[2].split(':')[1])
      continue
    else:
      if len(items) < 3: continue
      featStr = items[0]
      optExplored = int(items[1])
      solved = int(items[2])
      feats = re.split('[:,]', featStr)
      fKeyVal = collections.defaultdict(lambda: 0)
      fKeyVal['treeDepth='] = treeDepth
      for k, v in zip(feats[::2], feats[1:][::2]):
        fKeyVal[k] = int(v) 
      grids[gridId].append((fKeyVal, optExplored, solved))
      featureKeys = featureKeys.union(set(fKeyVal.keys()))
  featureKeys.add('treeDepth=')
  return grids, featureKeys

def compareCost((explCost1, solved1), (explCost2, solved2)):
  if solved1 < solved2:
    return -1
  if solved1 > solved2:
    return +1
  if explCost1 < explCost2:
    return +1
  if explCost1 > explCost2:
    return -1
  return 0

def vectorize(f1, featureKeys):
  return [f1[k] for k in list(featureKeys)]

def lrData(grids, featureKeys):
  X = []
  Y = []
  for gridData in grids.values():
    for i in range(len(gridData)):
      f1, cost1, solved1 = gridData[i]
      v = vectorize(f1, featureKeys)
      X.append(v)
      Y.append(cost1)
  return X, Y

clf = None
if knobs['ML_ENABLED']:
  g, fKeys = readData('sudoku.ml.data')
  clf = linear_model.LinearRegression()
  X, Y = lrData(g,fKeys)
  clf.fit(X, Y)
  """if knobs['ML_SVM']:
    clf = svm.SVC(kernel='linear', C=.1)
    X, Y = pairwiseData(g,fKeys)
    clf.fit(X, Y)"""

def optionsSortedbyML(values):
  emptyUnitSqs = countEmptyUnitSqs(values)
  unitOpts = countUnitOptions(values)
  optionUnitFreq = computeOptUnitFreq(values)
  
  options = [(s,d) for s in squares for d in list(values[s]) 
             if len(values[s]) > 1]
  
  def mlPredict(s, d):
    f = vectorize(extractFeatures(values, s, d, emptyUnitSqs,
                                  unitOpts, optionUnitFreq), fKeys)
    return clf.predict(f)
  #options = zip(*sorted([(mlPredict(s, d), d) for d in list(values[s])]))[1]
  sortedOpts = zip(*sorted([(mlPredict(s, d), (s, d)) for s,d in options]))[1]
  bestSq,_ = sortedOpts[0]
  options = [d for s, d in sortedOpts if s == bestSq]
  return bestSq, options

def compareCost((explCost1, solved1), (explCost2, solved2)):
  if solved1 < solved2:
    return -1
  if solved1 > solved2:
    return +1
  if explCost1 < explCost2:
    return +1
  if explCost1 > explCost2:
    return -1
  return 0

def vectorDiff(f1, f2, featureKeys):
  return [f1[k] - f2[k] for k in featureKeys]

def pairwiseData(grids, featureKeys):
  X = []
  Y = []
  for gridData in grids.values():
    for i in range(len(gridData)):
      for j in range(i+1, len(gridData)):
        f1, cost1, solved1 = gridData[i]
        f2, cost2, solved2 = gridData[j]
        cmpVal = compareCost((cost1, solved1), (cost2, solved2))
        if cmpVal == 0:
          continue
        # Balance the +ve and -ve results
        if random.randint(0,1) is 0: # +ve result
          y = +1
          if cmpVal > 0: dv = vectorDiff(f1, f2, featureKeys)
          else: dv = vectorDiff(f2, f1, featureKeys)
        else:
          y = -1
          if cmpVal < 0: dv = vectorDiff(f1, f2, featureKeys)
          else: dv = vectorDiff(f2, f1, featureKeys)
        if any(dv):
          X.append(dv)
          Y.append(y)
  return X, Y

