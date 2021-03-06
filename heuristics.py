from sudoku import *
import random
import numpy as np
from ml import *


def shuffledOptions(values, s):
  options = list(values[s])
  random.shuffle(options)
  return options

def leastConstrainingValue(values, s):
  options = sorted([(sum(1 for p in peers[s] if d in p), d)
                    for d in values[s]])
  options = zip(*options)[1]
  return options

def searchDepthLimited(values):
  "Alternate between DFS and Constraint Propagation"

  best = None
  #sqs = sorted((len(values[s]), s) for s in squares if len(values[s]) > 1)
  #sqs = [v[1] for v in sqs]
  
  for s in squares:
    if len(values[s]) == 1: continue
    options = leastConstrainingValue(values, s)
    for d in options[0:1]:
      vals = {k:v for k, v in values.items()}
      values2 = assign(vals, s, d)
      if values2:
        unsolvedSqs = [len(values2[s2])
                       for s2 in squares if len(values2[s2]) > 1]
        unsolvedSqsCount = len(unsolvedSqs)
        optionsCount = sum(unsolvedSqs)
        if (best is None or best[0] > unsolvedSqsCount or
            best[0] == unsolvedSqsCount and best[1] > optionsCount):
          best = (unsolvedSqsCount, optionsCount, values2, s, d)
        
  if best:
    return best[3]
  return False



def bestMove(values):
  perfMetric = defaultdict(lambda: 0)
  s = searchDepthLimited(values)
  if not s:
    _, s = min((len(values[s]), s) for s in squares if len(values[s]) > 1)
  return s


def heuristicSearch(values, perfMetric):
  "Alternate between DFS and Constraint Propagation"
  if values is False:
    return False ## Failed earlier
  if all(len(values[s]) == 1 for s in squares):
    return values ## Solved!

  """if not knobs['MOST_CONSTRAINED_VAR'] and perfMetric['options'] > 50:
    return False"""

  ## DFS: choose unfilled square s with fewest possibilities
  if knobs['MOST_CONSTRAINED_VAR']:
    n, s = min((len(values[s]), s) for s in squares if len(values[s]) > 1)
  elif knobs['RANDOM_VAR']:
    s = random.sample([s for s in squares if len(values[s]) > 1], 1)[0]
    #s = sChoices[random.randint(0,len(sChoices)-1)]
  elif knobs['ML_ENABLED']:
    pass
  else:
    s = bestMove(values)

  """emptyUnitSqs = countEmptyUnitSqs(values)
  unitOpts = countUnitOptions(values)
  optionUnitFreq = computeOptUnitFreq(values)
  def mlPredict(s, d):
    f = vectorize(extractFeatures(values, s, d, emptyUnitSqs,
                                  unitOpts, optionUnitFreq), fKeys)
    return clf.predict(f)

  options = zip(*sorted([(mlPredict(s, d), d) for d in list(values[s])]))[1]"""

  if knobs['ML_ENABLED']:
    s, options = optionsSortedbyML(values)    
    #options = optionsSortedbyML(values, s)
  elif knobs['LCV_ENABLED']:
    options = leastConstrainingValue(values, s)
  elif knobs['RANDOM_OPTIONS_ENABLED']:
    options = shuffledOptions(values, s)
  else:
    options = values[s]

  perfMetric['squares'] += 1
  for d in options:
    perfMetric['options'] += 1
    values2 = heuristicSearch(assign(values.copy(), s, d), perfMetric)
    if values2: return values2
  return False
