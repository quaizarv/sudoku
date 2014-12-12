Sudoku solver for CS221

Sudoku Solver using CSP with backtracking can be run as follows:

- To run the baseline:

  python sudoku.py <file-name>

Example:

  python sudoku.py data/randomHard.txt


- To run the fastest version (which includes all the generalized AC3 
  strategies as well as heuristics)

  $python sudoku.py <file-name> -f

Example:

  python sudoku.py data/randomHard.txt -f


- To turn on generalize AC3 strategies and heuristics selectively

  python sudoku.py <filename>  -o SE:TS:MCV:LCV:RO:MLDC:ML

  Options are separated by ':'. Options are:

  SE:   enable Subregion-Excluson
  GT:   enable Generalized Twin Strategy
  MCV:  enable Most Constrained Variable Selection
  LCV:  enable Least Constrained Value Selection
  RO:   enable Random Value (i.e. Digit in a square) Selection
  MLDC: turn on Machine Learning Data Collection
  ML:   turn on Machine Learning based Move Selection (Note that you should
        have collected data by running "python sudoku.py -o MLDC) beforehand

  Example:

    # Turn on Generalize Twins & Subregion-Exclusion AC3 Strategies along with
    # Most Constrained Var and Random Value (Digit) Selection
    python sudoku.py data/randomHard.txt -o TS:SE:MCV:RO

    # Turn on just Subregion-Exclusion Strategy
    python sudoku.py data/randomHard.txt -o SE

    # Turn on Subregion-Exclusion Strategy with Most Constrained Var heuristic
    python sudoku.py data/randomHard.txt -o SE:MCV

    

    
  
