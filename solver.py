from typing import Tuple, List
import numpy as np
import cvxpy as cp
from constants import *
from board import Board


class MinesweeperLPSolver():
    """Solving Minesweeper using LP

    Use Linear Programming to solve minesweeper interactively

    Attributes
    ---------
    board : Board
        The board the solver is going to try to solve.
    verbose : int
        Controls the verbosity.
    x : cp.Variable
        Variables that go into the cvxpy problem. A value of one means that block (x, y) is a mine.
    constraints : List[cvxpy.constraints.constraint.Constraint]
        Linear Program constraints to be used for iterative solving.
    objective : cvxpy.problems.objective.Objective
        Zero objective that needs to be provided to the Linear Problem.
    last_solution : List[List[float]]
        Solution values from previous iteration, can be used to speed up computation of new solution.
    known : numpy.ndarray
        Number of mines in each revealed square or -1.
    clicked : set
        Which blocks have been clicked.
    flagged : set
        Which blocks have been flagged.
    prob : cvxpy.Problem
        CVXPY problem that is iteratively used.
    """
    def __init__(self, board: Board, verbose: int = 0) -> None:
        self.board = board
        self.verbose = verbose

        self.x = cp.Variable((self.board.windowWidth, self.board.windowHeight), 'x')
        self.constraints: List[cp.constraints.constraint.Constraint] = [cp.sum(self.x) == self.board.mines, 0 <= self.x, self.x <= 1]
        self.objective: cp.problems.objective.Objective = cp.Maximize(0)
        self.last_solution = np.ones((self.board.windowWidth, self.board.windowHeight)) * (self.board.mines / (self.board.windowHeight * self.board.windowWidth))
        self.known = - np.ones(((self.board.windowWidth, self.board.windowHeight)))
        self.clicked = set()
        self.flagged = set()
        self.prob: cp.Problem 


    def get_next(self) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """Returns the coordinates of the next blocks to click or flag

        Construct the problem, solve it, use the solution to decide on what blocks to click.

        Parameters
        ----------

        Returns
        -------
        zero_pos : List[Tuple[int, int]
            Blocks with the smallest probability to contain a mine that haven't been clicked yet.
        one_pos : List[Tuple[int, int]
            Blocks with probability close to enough to one that have not been flagged.
        """
        # Solve problem
        self.prob = cp.Problem(self.objective, self.constraints)
        self.prob.solve(warm_start=True)

        
        
        # Find blocks with smallest probability
        zero_pos = []
        one_pos = []
        min_prob = 1
        for i in range(self.board.windowWidth):
            for j in range(self.board.windowHeight):
                if (i, j) not in self.clicked:
                    if abs(self.x[i, j].value - self.last_solution[i, j]) < 1e-6:
                        self.clicked.add((i, j))
                        return [(i, j)], []
                    if self.x[i, j].value < min_prob:
                        min_prob = self.x[i, j].value
                        zero_pos = [(i, j)]
                        continue
                    elif abs(self.x[i, j].value - min_prob) < 1e-6:
                        zero_pos.append((i, j))
                        continue
                # Find blocks close enough to 1
                if (i, j) not in self.flagged:
                    if abs(self.x[i, j].value - 1) < 1e-6:
                        one_pos.append((i, j))
        
        # Update clicked and flagged sets
        self.clicked.update(set(zero_pos))
        self.flagged.update(set(one_pos))
        
        return zero_pos, one_pos

    def add_constraint(self, i: int, j: int, mine_count: int) -> None:
        """Add a constraint based on the value of block (i, j)

        Parameters
        ----------
        i : int
            Which column the block is in.
        j : int
            Which row the block is in.
        mine_count : int
            How many mines there are in the block (i, j).

        Returns
        -------
        """
        if self.verbose > 2:
            print("Adding", i, j, mine_count)
        neighbors = [(x, y) for x in range(i-1, i+2) for y in range(j-1, j+2) if x >= 0 and y >= 0 and x < self.board.windowWidth and y < self.board.windowHeight and (x != i or y != j) and ((x, y) not in self.clicked)]
        self.constraints.append(cp.sum([self.x[x, y] for x, y in neighbors]) == mine_count)
        self.constraints.append(self.x[i, j] == 0)
