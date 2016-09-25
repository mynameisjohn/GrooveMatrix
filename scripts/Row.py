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

        # The stopped state of a row indicates that
        # none of its cells are playing
        class Stopped(_state):
            def __init__(self, row):
                super(type(self), self).__init__(row, 'Stopped')

            # When a row is stopped, it should set its
            # active cell to stopped if it has one -
            # if it was stopping then everything is fine,
            # and if it wasn't then we'll raise an error
            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                if self.mRow.mActiveCell is not None:
                    self.mRow.mActiveCell.SetState(Cell.State.Stopped(self.mRow.mActiveCell))
                    self.mRow.mActiveCell = None
                # set color appropriately
                yield

            # Clicking a stopped row does nothing
            def OnLButtonUp(self):
                pass

            # A stopped row will switch to any pending cells
            def Advance(self):
                for c in self.mRow.GetAllCells():
                    if isinstance(c.GetActiveState(), Cell.State.Pending):
                        return Row.State.Switching(self.mRow, c)

        # A playing row indicates that it has an active playing cell
        class Playing(_state):
            def __init__(self, row):
                super(type(self), self).__init__(row, 'Playing')

            # If we enter the playing state, we must determine
            # how we got in that state and modify cells accordingly
            # Note that we set the active cell to playing at the end of this function
            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                if not(isinstance(prevState, Column.State.Switching)):
                    raise RuntimeError('Error: How did we switch to playing?')
                # If we were already playing
                if self.mRow.mActiveCell is not None:
                    # If our active cell stopped, we have a new active cell
                    if isinstance(self.mRow.mActiveCell.GetActiveState(), Cell.State.Stopped):
                        self.mRow.mActiveCell = self.mRow.mPendingCell
                    # If the active cell isn't stopped, it means we cancelled a switch
                    # In that case, stop the pending cell and clear it
                    else:
                        self.mRow.mPendingCell.SetState(Cell.State.Stopped(self.mRow.mPendingCell))
                        self.mRow.mPendingCell = self.mRow.mActiveCell
                # We are just starting to play, the active cell should now be stopped, make pending active
                else:
                    if not isinstance(self.mRow.mActiveCell.GetActiveState(), Cell.State.Stopped):
                        raise RuntimeError('Error: What is our active cell doing?')
                    self.mRow.mActiveCell = self.mRow.mPendingCell
                # Start playing the active cell
                self.mRow.mActiveCell.SetState(Cell.State.Playing(self.mRow.mActiveCell))
                yield

            # Switch to None if clicked
            def OnLButtonUp(self):
                return Row.State.Switching(self.mRow, None)

            # We'll go to switching if we have a pending cell
            # or to stopping if our active cell is stopping
            def Advance(self):
                # If any of our cells are pending, switch to that cell
                for c in self.mRow.GetAllCells():
                    if isinstance(c.GetActiveState(), Cell.State.Pending):
                        return Row.State.Switching(self.mRow, c)
                # If none were pending and our active state is stopping, we are stopping
                if isinstance(self.mRow.mActiveCell.GetActiveState(), Cell.State.Stopping):
                    return Row.State.Switching(self.mRow, None)

        # The switching state denotes that the row's active cell is
        # changing - this could mean that the row is pending, switching
        # to a different active cell, or stopping
        class Switching(_state):
            def __init__(self, row, nextCell = None):
                super(type(self), self).__init__(row, 'Switching')
                # store next cell, don't assign yet
                self.mPrevCell = self.mRow.mActiveCell
                self.mNextCell = nextCell

            # When a row becomes switching, it's pending
            # cell is set to this state's next cell member
            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # The next cell shouldn't be the row's current active cell
                if self.mNextCell is self.mRow.mActiveCell:
                    raise RuntimeError('Error: Why was row switching to active?')
                # If the previous state wasn't stopped, we are switching to a new voice
                if not(isinstance(prevState, Row.State.Stopped)):
                    self.mRow.mActiveCell.SetState(Cell.State.Stopping(self.mRow.mActiveCell))
                # If we had a pending cell that was different from the next cell, stop it
                if self.mRow.mPendingCell is not None and self.mNextCell is not self.mRow.mPendingCell:
                    self.mRow.mPendingCell.SetState(Cell.State.Stopped(self.mRow.mPendingCell))
                # Set row's pending to our next
                self.mRow.mPendingCell = self.mNextCell
                # If our new pending cell isn't None, set it to pending
                if self.mRow.mPendingCell is not None:
                    self.mRow.mPendingCell.SetState(Cell.State.Pending(self.mRow.mPendingCell))
                # Depending on what the next cell is
                # we could be starting, stopping, or switching
                # Update UI appropriately
                yield

            # If we're switching and clicked, revert to playing
            def OnLButtonUp(self):
                return Row.State.Playing(self.mRow)

            # If we were switching, maybe advance to playing or stopped
            def Advance(self):
                # A None pending cell means we were stopping
                if self.mNextCell is None:
                    if self.mRow.mActiveCell is None:
                        raise RuntimeError('Error: Why stop twice?')
                    # If our active cell is stopped, we are stopped
                    if isinstance(self.mActiveCell, Cell.State.Stopped):
                        return Row.State.Stopped(self.mRow)
                    # If it's playing again, then we are playing
                    if isinstance(self.mActiveCell, Cell.State.Playing):
                        return Row.State.Playing(self.mRow)
                # We are switching to another cell
                else:
                    # If we have a new pending cell, return a new switching state
                    for c in self.mRow.liCells:
                        if c is not self.mNextCell:
                            if isinstance(c.GetActiveState(), Cell.State.Pending):
                                # This needs to be treated as a context switch
                                return Row.State.Switching(self.mRow, c)
                    # If the next cell starts playing, return playingS
                    if isinstance(self.mNextCell, Cell.State.Playing):
                        return Row.State.Playing(self.mRow)
                    # If it went to stopped, revert to either stopped or playing
                    if isinstance(self.mNextCell, Cell.State.Stopped):
                        if self.mRow.mActiveCell is None:
                            return Row.State.Stopped(self.mRow)
                        else:
                            return Row.State.Playing(self.mRow)

from Cell import Cell
