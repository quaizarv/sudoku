from sudoku import *

ex2 = [4]

def isRow(unit):
  if len(set([s[0] for s in unit])) == 1: return True
  return False

def isCol(unit):
  if len(set([s[1] for s in unit])) == 1: return True
  return False

def getRow(s):
  return cross(s[0], cols)

def getCol(s):
  return cross(rows, s[1])

def getBox(s):
  for u in boxUnits:
    if s in u: return u

def singleRow(places):
  if len(set([s[0] for s in places])) == 1: return True
  return False

def singleCol(places):
  if len(set([s[1] for s in places])) == 1: return True
  return False

def inSingleSubregion(places):
  if len(places) is 1 or len(places) > 3: return False
  if singleRow(places) or singleCol(places):
    boxes = set([tuple(getBox(s)) for s in places])
    if len(boxes) == 1: return True
  return False

def CPSubregionExclusion(values, unit, d):
  """Subregion exclusion - if a number is restricted to a row (column) of a
  single box then it can be removed as a choice from other squares in that row
  (column) (the trigger here is changes happening in the box).  The other way
  round is also true, i.e. if a number is restricted to 2 or 3 sqaures in a row
  (column) and those squares happen to be in the same box then the number can be
  removed as a choice from the rest of the box (here the trigger is changes
  happening to a row/column."""
  dplaces = [s for s in unit if d in values[s]]
  if not inSingleSubregion(dplaces): return values
  if isRow(unit) or isCol(unit):
    u2 = getBox(dplaces[0])
  else:
    if singleRow(dplaces):
      u2 = getRow(dplaces[0])
    else:
      u2 = getCol(dplaces[0])
  otherPlaces = [s2 for s2 in u2 if s2 not in dplaces and d in values[s2]]
  if not otherPlaces: return values
  if ex2[0] == 8: #example
    print "before subregion ", unit, u2, d
    display(values)
    ex2[0] = 9
  if not all(eliminate(values, s2, d) for s2 in u2 if s2 not in dplaces):
    return False
  if ex2[0] == 9: #example
    print "after subregion "
    display(values)
    ex2[0] = 10
  return values  

def twinsStrategy(values, u, s):

  if len(values[s]) == 1: return values

  """Naked twins - if there are a set of n < 9 numbers which are the only
  possibilities in exactly n squares of a unit, then these numbers can be
  discarded as option from other squares in the unit. Note that this is a
  generalized version of Naked Twin Strategy"""
  exactTwins = [s2 for s2 in u if values[s] == values[s2]]
  if len(values[s]) < len(exactTwins):
    return False ## Contradiction: fewer options than squares 

  if len(values[s]) == len(exactTwins):
    for s2 in u:
      if s2 in exactTwins: continue
      if ex2[0] == 4 and len(values[s]) < 6: #example
        if set(values[s2]).intersection(set(values[s])):
          print "before naked twin ", s, values[s], u
          display(values)
          ex2[0] = 5
      if not all(eliminate(values, s2, d) for d in values[s]):
        return False
    if ex2[0] == 5: #example
      print "after naked twin "
      display(values)
      ex2[0] = 6
    return values  ##: Nakes Twins & Hidden Twins are mutually exclusive
  
  """Hidden twins - if there are a set of n numbers (n < 9) which are
  restricted as options to exactly n squares in a unit, then any other options
  (beside these n numbers) in these n squares can be discarded. Note that this
  is a generalized version of Hidden Twins Strategy
  domain = [s2 for s2 in u if set(values[s]).intersection(set(values[s2]))]
  if len(values[s]) == len(domain):
    #print "applying hidden Twin"
    for s2 in domain:
      otherValues = set(values[s2]).difference(set(values[s]))
      if (otherValues):
        if ex2[0] == 6 and len(values[s]) < 6: #example
          print "before hidden twin ", s, values[s], domain
          display(values)
          ex2[0] = 7
        if all(eliminate(values, s2, d) for d in otherValues):
          if ex2[0] == 7 and otherValues: #example
            print "after hidden twin ", values[s], otherValues, s, s2
            display(values)
            ex2[0] = 8
        else:
          return False"""
  return values


def chainStrategy(values, u, s):

  """Naked Chain"""
  domain = [s2 for s2 in u if set(values[s]).intersection(set(values[s2]))]
  domainValues = set(''.join(values[s2] for s2 in domain))
  if len(domainValues) < len(domain):
    return False ## Contradiction: fewer options than squares 

  if len(domainValues) == len(domain):
    #print "applying Naked Chain"
    for s2 in u:
      if s2 in domain: continue
      if not all(eliminate(values, s2, d) for d in domainValues):
        return False
    return values  ##: Naked chain & Hidden chains are mutually exlusive

  return values

def eliminateByLogicStrategies(values, s, d):
  for u in units[s]:
    if not CPSubregionExclusion(values, u, d):
      return False
    if not twinsStrategy(values, u, s):
      return False
    for s2 in u:
      if d in values[s2]:
        if not twinsStrategy(values, u, s2):
          return False
        break
  return values  
