import StateGraph
from MatrixEntity import MatrixEntity
from Util import Constants

import Shape

import contextlib
import networkx as nx
from collections import namedtuple

class Row(MatrixEntity):
    # Rows are represented by a rect
    nHeaderW = 100	# width of row header
    nHeaderH = 50	# height of row header

    # Useful when constructing
    RowData = namedtuple('RowData', ('liClipData', 'clrOn', 'clrOff'))

    # Constructor takes rowData, GM, and y position
    def __init__(self, GM, rowData, nPosY):
        # Get ID
        super(Row, self).__init__(GM)

        # Create UI components
        nRowX = Constants.nGap + Row.nHeaderW / 2
        self.nShIdx = GM.cMatrixUI.AddShape(Shape.AABB, [nRowX, nPosY], {'w' : Row.nHeaderW, 'h': Row.nHeaderH})
        self.nDrIdx = GM.cMatrixUI.AddDrawableIQM('../models/quad.iqm', [nRowX, nPosY], [Row.nHeaderW, Row.nHeaderH], rowData.clrOff, 0. )

        # Move cells to correct pos, set colors
        self.clrOn = rowData.clrOn
        self.clrOff = rowData.clrOff
        nCellPosX = Row.nHeaderW + 2 * Constants.nGap + Cell.nRadius
        nCellPosDelta = 2 * Cell.nRadius + Constants.nGap

        # Construct cells from cClips
        self.liCells = []
        for clip in rowData.liClipData:
            # Construct the cell
            cell = Cell(GM, self, clip, 1.)

            # Determine x pos
            liCellPos = [nCellPosX, nPosY]

            # Set position for shape
            cShape = cell.GetShape()
            cShape.SetCenterPos(liCellPos)

            # Set position for drawable
            cDrawable = cell.GetDrawable()
            cDrawable.SetPos2D(liCellPos)

            cDrawable.SetColor(rowData.clrOff)
            nCellPosX += nCellPosDelta

            # Add to our list
            self.liCells.append(cell)

        # Set up play state, active and pending are None
        self.mActiveCell = None
        self.mPendingCell = None

        # Set Component IDs
        self.SetComponentID()

        # Create state graph nodes
        pending = Row.State.Pending(self)
        playing = Row.State.Playing(self)
        switching = Row.State.Switching(self)
        stopped = Row.State.Stopped(self)

        # Create di graph and add states
        G = nx.DiGraph()
        G.add_edge(pending, playing)
        G.add_edge(stopped, pending)
        G.add_edge(playing, switching)
        G.add_edge(switching, playing)
        G.add_edge(switching, stopped)

        # Create state graph member, init state to stopped
        self.mSG =  StateGraph.StateGraph(G, MatrixEntity.fnAdvance, stopped, True)

    # Get the pending or active cell
    def GetPendingCell(self):
        return self.mPendingCell

    def GetActiveCell(self):
        return self.mActiveCell

    def GetAllCells(self):
        return self.liCells

    class State:
        class _state(MatrixEntity._state):
            def __init__(self, row, name):
                MatrixEntity._state.__init__(self, name)
                self.mRow = row

        class Pending(_state):
            def __init__(self, row):
                super(type(self), self).__init__(row, 'Pending')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                yield

            # Revert to stopped if clicked
            def OnLButtonUp(self):
                return Row.State.Stopped(self.mRow)

            # Pending to playing if pending is playing,
            # otherwise to stopped if pending is stopped
            def Advance(self):
                if isinstance(self.mRow.GetPendingCell().GetState(), Cell.State.Playing):
                    return Row.State.Playing(self.mRow)
                if isinstance(self.mRow.GetPendingCell().GetState(), Cell.State.Stopped):
                    return Row.State.Stopped(self.mRow)

        class Playing(_state):
            def __init__(self, row):
                super(type(self), self).__init__(row, 'Playing')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # If we are set to playing, our pending cell should be playing
                # and our active cell should be None
                if not(isinstance(self.mRow.GetPendingCell().GetActiveState(), Cell.State.Playing) and self.mRow.GetActiveCell() == None)
                    raise RuntimeError('Error: Weird state transition!')
                # The pending cell is now active
                self.mRow.mActiveCell = self.mRow.mPendingCell
                yield

            # Switch to None if clicked
            def OnLButtonUp(self):
                return Row.State.Switching(self.mRow, None)

            # Pending to playing if pending is playing,
            # otherwise to stopped if pending is stopped
            def Advance(self):
                if isinstance(self.mRow.GetPendingCell().GetState(), Cell.State.Playing):
                    return Row.State.Playing(self.mRow)
                if isinstance(self.mRow.GetPendingCell().GetState(), Cell.State.Stopped):
                    return Row.State.Stopped(self.mRow)

        class Switching(_state):
            def __init__(self, row, nextCell = None):
                super(type(self), self).__init__(row, 'Switching')
                # store next cell, don't assign yet
                self.mNextCell = nextCell

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # When state is entered, change row member
                self.mRow.mPendingCell = self.mNextCell
                # If none, indicate stopping state
                yield

            # If we're switching and clicked, revert to playing
            def OnLButtonUp(self):
                return Row.State.Playing(self.mRow)

            # If we were switching, maybe advance to playing or stopped
            def Advance(self):
                if self.mPendingCell is not None:
                    if isinstance(self.mPendingCell, Cell.State.Playing):
                        return Row.State.Playing(self.mRow)
                else:
                    if self.mActiveCell is None:
                        raise RuntimeError('Error: Weird state transtion!')
                    if isinstance(self.mActiveCell, Cell.State.Stopped):
                        return Row.State.Stopped(self.mRow)

        class Stopped(_state):
            def __init__(self, row):
                super(type(self), self).__init__(row, 'Stopped')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                yield

            # Clicking a stopped row does nothing
            def OnLButtonUp(self):
                pass

            def Advance(self):
                # None of our cells should have been playing
                if any(isinstance(c.GetActiveState(), Cell.State.Playing for c in self.mRow.GetAllCells())):
                    raise RuntimeError('Error: Weird state transtion!')
                # go to pending if any cells are pending
                if any(isinstance(c, Cell.State.Pending for c in self.mRow.GetAllCells())):
                    return Row.State.Pending

from Cell import Cell
