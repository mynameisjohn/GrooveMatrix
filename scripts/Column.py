import StateGraph
from MatrixEntity import MatrixEntity
from Util import Constants

import Shape

import contextlib
import networkx as nx
from collections import namedtuple

from Util import Constants
from Cell import Cell

class Column(MatrixEntity):
    nTriDim = 50

    # Constructor takes rowData, GM, and y position
    def __init__(self, GM, nPosX, setCells):
        # Get ID
        super(Column, self).__init__(GM)

        # Move cells to correct pos, set colors
        self.clrOn = [1,1,1,1]
        self.clrOff = [1,1,1,1]

        # Create UI components
        # column triangles will be above the cells, but right now
        # that placement code is kind of split up. Please centralize it
        nHalfTri = Column.nTriDim / 2
        nColY = GM.GetCamera().GetScreenHeight() - Constants.nGap + nHalfTri
        triVerts = [[-nHalfTri, -nHalfTri], [-nHalfTri, nHalfTri], [0, nHalfTri]]
        self.nShIdx = GM.cMatrixUI.AddShape(Shape.Triangle, [nPosX, nColY], {
            'aX' : triVerts[0][0], 'aY' : triVerts[0][1],
            'bX' : triVerts[1][0], 'bY' : triVerts[1][1],
            'cX' : triVerts[2][0], 'cY' : triVerts[2][1]})
        self.nDrIdx = GM.cMatrixUI.AddDrawableTri('col'+str(self.nID), triVerts, [nPosX, nColY], [1, 1], self.clrOff, 0. )

        # Set Component IDs
        self.SetComponentID()

        # Create state graph nodes
 #       pending = Column.State.Pending(self)
 #       playing = Column.State.Playing(self)
#        stopped = Column.State.Stopped(self)

        # Create di graph and add states
 #       G = nx.DiGraph()
 #       G.add_edge(pending, playing)
 #       G.add_edge(pending, stopped)
 #       G.add_edge(stopped, pending)
#        G.add_edge(playing, stopped)

        # The state advance function
#        def fnAdvance(SG):
#            nonlocal self, pending, playing, stopped
#            # Nothing to be done
#            return self.GetActiveState()

        # Create state graph member, init state to stopped
        # self.mSG =  StateGraph.StateGraph(G, fnAdvance, stopped, True)

        # If a GM instance is making us with cells, they get stored here
        self.setCells = {c for c in setCells if isinstance(c, Cell)}

    # A GM instance will own a list of rows and columns. Every time
    # a row is added to the GM, it will look at its columns and add
    # any cells needed - if a column is missing, it will be constructed
    def AddCell(self, cell):
        self.setCells.add(cell)

#     # Set the pending cell
#     # Note that this doesn't actually transition the cell
#     # into a pending state unless we were pending
#     # If we were not, then the transition to pending takes care of it
#     def SetPendingCell(self, cell):
#         # If not None, it better be one of ours
#         if cell is not None and cell not in self.liCells:
#             raise RuntimeError('Pending Cell not in row!')
#         # If changing
#         if self.mPendingCell is not cell:
#             # If we have an actual pending cell, make sure it knows it's stopped
#             if self.mPendingCell is not self.mActiveCell and self.mPendingCell is not None:
#                 self.mPendingCell.SetState(Cell.State.Stopped)
#             # Assign mPendingCell, set it to pending if not None
#             self.mPendingCell = cell
#             if self.mPendingCell is not None:
#                 self.mPendingCell.SetState(Cell.State.Pending)
#
#     # Assign active as pending, if possible
#     def _makePendingActive(self):
#         # If the pending is not the active
#         if self.mPendingCell is not self.mActiveCell:
#             # If we had an active cell, set it to stopped
#             if self.GetActiveCell() is not None:
#                 # The active cell should have been playing
#                 if not(isinstance(self.GetActiveCell().GetActiveState(), Cell.State.Playing)):
#                     raise RuntimeError('Error: Weird state transition!')
#                 # Set it to stopped
#                 self.GetActiveCell().SetState(Cell.State.Stopped)
#             # If we had a pending cell,set it to playing
#             if self.GetPendingCell() is not None:
#                 self.GetPendingCell().SetState(Cell.State.Playing)
#             # Assign active to pending, leave pending alone
#             self.mActiveCell = self.mPendingCell
#
#     # Get graph's active state
#     def GetActiveState(self):
#         return self.mSG.GetActiveState()
#
#     def GetTriggerRes(self):
#         # Return our active cell's if possible
#         if self.mActiveCell is not None:
#             return self.mActiveCell.GetTriggerRes()
#         # Otherwise take it to be the shortest of all (?)
#         return min(c.nTriggerRes for c in self.liCells)
#
#     # Mouse handler override
#     def OnLButtonUp(self):
#         # Clicking a row should stop any playing cells
#         if isinstance(self.GetActiveState(), Row.State.Playing):
#             self.SetPendingCell(None)
#
#     # Get the pending or active cell
#     def GetPendingCell(self):
#         return self.mPendingCell
#
#     def GetActiveCell(self):
#         return self.mActiveCell
#
#     # Update function advances state graph
#     # and gives each cell a chance to Update
#     def Update(self):
#         self.mSG.AdvanceState()
#         for cell in self.liCells:
#             cell.Update()
#
#     # Row state declarations
#     # This outer class is just so I can do things like Row.State.Pending
#     class State:
#         # Inner class is what all states inherit from
#         class _state(StateGraph.State):
#             def __init__(self, row, name):
#                 StateGraph.State.__init__(self, str(name))
#                 self.mRow = row
#
#         # Pending state means no cells are playing and one is pending
#         class Pending(_state):
#             def __init__(self, row):
#                 super(type(self), self).__init__(row, 'Pending')
#
#             # State lifetime management
#             @contextlib.contextmanager
#             def Activate(self, SG, prevState):
#                 # We should have had a pending cell before this occurred
#                 if self.mRow.GetPendingCell() is None:
#                     raise RuntimeError('Weird state transition!')
#                 # Ideally we'd start oscillating our color or something
#                 yield
#
#         # The Row.Stopped state means all cells in row are stopped
#         class Stopped(_state):
#             def __init__(self, row):
#                super(type(self), self).__init__(row, 'Stopped')
#
#             # When the stopped state is activated, the active cell
#             # will be set to stopped and the color will change
#             @contextlib.contextmanager
#             def Activate(self, SG, prevState):
#                 # Our pending cell should have been None
#                 if self.mRow.GetPendingCell() is not None:
#                     raise RuntimeError('Weird state transition!')
#                 # Advance, which sets active to stopped and assigns None
#                 self.mRow._makePendingActive()
#                 # Set the color of our row rect (Cell handles itself)
#                 self.mRow.GetDrawable().SetColor(self.mRow.clrOff)
#                 yield
#                 # No exit for now
#
#         # The row playing state means one of our cells is playing
#         class Playing(_state):
#             def __init__(self, row):
#                 super(type(self), self).__init__(row, 'Playing')
#
#             # When the Playing state is activated, the pending cell
#             # will be set to playing and the color will change
#             @contextlib.contextmanager
#             def Activate(self, SG, prevState):
#                 # None should have been playing
#                 if any(isinstance(c, Cell.State.Playing) for c in self.mRow.liCells):
#                     raise RuntimeError('Weird state transition!')
#                 # I just want to try and catch everything
#                 if self.mRow.GetPendingCell() is None or self.mRow.GetActiveCell() is not None:
#                     raise RuntimeError('Weird state transition!')
#                 # Make pending cell active
#                 self.mRow._makePendingActive()
#                 # set color to on
#                 self.mRow.GetDrawable().SetColor(self.mRow.clrOn)
#                 yield
#                 # No exit for now
#
# # These have to be imported at the end of
# # the file because of cyclical imports
# # (Row imports Cell, Cell imports Row)
# from Cell import Cell
