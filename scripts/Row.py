import StateGraph
from MatrixEntity import MatrixEntity
from Util import Constants

import Shape

import contextlib
import networkx as nx
from collections import namedtuple

class Row(MatrixEntity):
    # Rows are represented by a rect
    nHeaderW = 100    # width of row header
    nHeaderH = 50    # height of row header

    # Useful when constructing
    RowData = namedtuple('RowData', ('liClipData', 'clrOn', 'clrOff'))

    # Constructor takes rowData, GM, and y position
    def __init__(self, GM, rowData, nPosY):
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

        # Create state graph nodes
        playing = Row.State.Playing(self)
        switching = Row.State.Switching(self)
        stopped = Row.State.Stopped(self)

        # Create di graph and add states
        G = nx.DiGraph()
        G.add_edge(switching, playing)
        G.add_edge(stopped, switching)
        G.add_edge(playing, switching)
        G.add_edge(switching, playing)
        G.add_edge(switching, stopped)

        # Call base constructor to construct state graph
        super(Row, self).__init__(GM, G, stopped)

        # Set Component IDs
        self.SetComponentID()

    # Get the pending or active cell
    def GetPendingCell(self):
        return self.mPendingCell

    def GetActiveCell(self):
        return self.mActiveCell

    def GetAllCells(self):
        return self.liCells

    # Row state and base class, inherits from
    # MatrixEntity state and caches Row ref
    class State:
        class _state(MatrixEntity._state):
            def __init__(self, row, name):
                MatrixEntity._state.__init__(self, name)
                self.mRow = row

        ## The Pending Row state
        #class Pending(_state):
        #    def __init__(self, row):
        #        super(type(self), self).__init__(row, 'Pending')

        #    # Ideally this would kick off some animation
        #    # indicating that the row is pending playback
        #    @contextlib.contextmanager
        #    def Activate(self, SG, prevState):
        #        yield

        #    # Revert to stopped if clicked
        #    def OnLButtonUp(self):
        #        return Row.State.Stopped(self.mRow)

        #    # Pending to playing if pending is playing,
        #    # otherwise to stopped if pending is stopped
        #    def Advance(self):
        #        if isinstance(self.mRow.GetPendingCell().GetActiveState(), Cell.State.Playing):
        #            return Row.State.Playing(self.mRow)
        #        if isinstance(self.mRow.GetPendingCell().GetActiveState(), Cell.State.Stopped):
        #            return Row.State.Stopped(self.mRow)

        class Playing(_state):
            def __init__(self, row):
                super(type(self), self).__init__(row, 'Playing')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # The pending cell is now active
                self.mRow.mActiveCell = self.mRow.mPendingCell
                yield

            # Switch to None if clicked
            def OnLButtonUp(self):
                return Row.State.Switching(self.mRow, None)

            # Pending to playing if pending is playing,
            # otherwise to stopped if pending is stopped
            def Advance(self):
                # If I'm playing and any of my cells are pending, we are switchinig to that cell
                for c in self.mRow.GetAllCells():
                    if isinstance(c.GetActiveState(), Cell.State.Pending):
                        return Row.State.Switching(self.mRow, c)
                # If none were pending and any are stopping, then we're stopping (switching to None)
                if any(isinstance(c, Cell.State.Stopping) for c in self.mRow.GetAllCells()):
                    return Row.State.Switching(self.mRow, None)

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
                if self.mRow.mPendingCell is not None:
                    if isinstance(self.mRow.mPendingCell, Cell.State.Playing):
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
                if any(isinstance(c.GetActiveState(), Cell.State.Playing) for c in self.mRow.GetAllCells()):
                    raise RuntimeError('Error: Weird state transtion!')
                # If any cells are pending, we are switching to that cell
                for c in self.mRow.GetAllCells():
                    if isinstance(c.GetActiveState(), Cell.State.Pending):
                        return Row.State.Switching(self.mRow, c)

from Cell import Cell
