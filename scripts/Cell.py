import StateGraph
from MatrixEntity import MatrixEntity

import contextlib
import networkx as nx

import Shape

class Cell(MatrixEntity):
    # Cells are represented by a circle with this radius
    nRadius = 25

    # Constructor takes GM, row, a clip, and the initial volume
    def __init__(self, GM, row, cClip, fVolume):
        # Store cClip ref and volume
        self.cClip = cClip
        self.fVolume = float(fVolume)
        self.mRow = row

        # Every cell has a trigger resolution
        # which for now is just its duration
        self.nTriggerRes = self.cClip.GetNumSamples(False)

        # Set up UI components
        self.nShIdx = GM.cMatrixUI.AddShape(Shape.Circle, [0, 0], {'r' : Cell.nRadius})
        self.nDrIdx = GM.cMatrixUI.AddDrawableIQM('../models/circle.iqm', [0, 0], 2 * [2*Cell.nRadius], [0, 0, 0, 1], 0. )

        # Create state graph nodes
        pending = Cell.State.Pending(self)
        playing = Cell.State.Playing(self)
        stopping = Cell.State.Stopping(self)
        stopped = Cell.State.Stopped(self)

        # Create di graph and add states
        G = nx.DiGraph()
        G.add_edge(pending, playing)
        G.add_edge(pending, stopped)
        G.add_edge(stopped, pending)
        G.add_edge(playing, stopping)
        G.add_edge(stopping, stopped)

        # Call base constructor to construct state graph
        super(Cell, self).__init__(GM, G, stopped)

        # Set component IDs
        self.SetComponentID()

    # Until I can find a way to get both row and col in constructor
    # Column constructor should call this
    def SetCol(self, col):
        if isinstance(col, Column):
            self.mCol = col

    def GetRow(self):
        return self.mRow

    def GetCol(self):
        return self.mCol

    # Get our trigger resolution
    def GetTriggerRes(self):
        return self.nTriggerRes

    def WillTriggerBeHit(self):
        nCurPos = self.mGM.GetCurrentSamplePos()
        nNewPos = nCurPos + self.mGM.GetCurrentSamplePosInc()
        nTrigger = self.GetTriggerRes() - self.mGM.GetPreTrigger()
        return nCurPos < nTrigger and nNewPos >= nTrigger

    # Cell States
    class State:
        class _state(MatrixEntity._state):
            def __init__(self, cell, name):
                MatrixEntity._state.__init__(self, name)
                self.mCell = cell

        # The stopped cell indicates that this cell's voice is quiet
        # It will go to pending if clicked or if the column is pending
        class Stopped(_state):
            def __init__(self, cell):
                super(type(self), self).__init__(cell, 'Stopped')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # If we were stopping, stop any voices
                if isinstance(prevState, Cell.State.Stopping):
                    self.mCell.GetGrooveMatrix().StopCell(self.mCell)
                # set the color to off
                self.mCell.GetDrawable().SetColor(self.mCell.mRow.clrOff)
                yield

            # Clicking a stopped cell will make it pending
            def OnLButtonUp(self):
                return Cell.State.Pending(self.mCell)

            # The column will set us pending if clicked
            def Advance(self):
                pass

        # A pending cell will go to playing if the trigger res is hit
        # and stopped if clicked. Rows and colums will see a pending cell
        # and advance if necessary
        class Pending(_state):
            def __init__(self, cell):
                super(type(self), self).__init__(cell, 'Pending')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # The cell should start flashing or something
                yield

            # Revert to stopped if clicked
            def OnLButtonUp(self):
                return Cell.State.Stopped(self.mCell)

            def Advance(self):
                # Pending to Playing if we'll hit our trigger res
                if self.mCell.WillTriggerBeHit():
                    return Cell.State.Playing(self.mCell)

        # Playing state means this cell's voice is playing
        class Playing(_state):
            def __init__(self, cell):
                super(type(self), self).__init__(cell, 'Playing')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # We should have been the row's pending cell
                if self.mCell.GetRow().GetPendingCell() is not self.mCell:
                    raise RuntimeError('Weird state transition')
                # If we weren't already playing, tell GM to play our stuff
                if not(isinstance(prevState, Cell.State.Stopping)):
                    self.mCell.mGM.StartCell(self.mCell)
                # set color to on
                self.mCell.GetDrawable().SetColor(self.mCell.mRow.clrOn)
                yield

            # Set to stopping if clicked
            def OnLButtonUp(self):
                return Cell.State.Stopping(self.mCell)

            # Our row will advance us to stopping if pending changes,
            # and our column will set us to stopping if it is stopping,
            # so I don't think there's much to do here
            def Advance(self):
                pass

        class Stopping(_state):
            def __init__(self, cell):
                super(type(self), self).__init__(cell, 'Stopping')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                yield

            # Revert to playing if stopping clicked
            def OnLButtonUp(self):
                return Cell.State.Playing(self.mCell)

            # The column will set us to playing if it is no longer stopping,
            # as will the row. OTherwise we go to stopped when the time comes,
            # so all we need to do is check trigger res for our stop
            def Advance(self):
                if self.mCell.WillTriggerBeHit():
                    return Cell.State.Stopped(self.mCell)

from Row import Row
from Column import Column
