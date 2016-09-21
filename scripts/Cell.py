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

    class State:
        class _state(MatrixEntity._state):
            def __init__(self, cell, name):
                MatrixEntity._state.__init__(self, name)
                self.mCell = cell

        class Pending(_state):
            def __init__(self, cell):
                super(type(self), self).__init__(cell, 'Pending')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                yield

            # Revert to stopped if clicked
            def OnLButtonUp(self):
                return Cell.State.Stopped(self.mCell)

            def Advance(self):
                # Pending to Playing if we'll hit our trigger res
                if self.mCell.WillTriggerBeHit():
                    return Cell.State.Playing(self.mCell)
                # Pending to playing if our row is set to playing
                if isinstance(self.mCell.GetRow().GetActiveState(), Row.State.Playing):
                    # Although as a sanity check, this doesn't really happen unless
                    # the clip launcher is stopped (and is about to start playing)
                    if self.mCell.GetGrooveMatrix().GetClipLauncher().GetPlayPause():
                        raise RuntimeError('Error: Cell set to playing by Row during playback')
                    return Cell.State.Playing(self.mCell)

        class Playing(_state):
            def __init__(self, cell):
                super(type(self), self).__init__(cell, 'Playing')

            @contextlib.contextmanager
            # When a cell starts playing, it tells the GM what to play
            def Activate(self, SG, prevState):
                # We should have been the row's pending cell
                if self.mCell.GetRow().GetPendingCell() is not self.mCell:
                    raise RuntimeError('Weird state transition')
                # set color to on
                self.mCell.GetDrawable().SetColor(self.mCell.mRow.clrOn)
                # Tell GM to start playing my stuff
                self.mCell.mGM.StartCell(self.mCell)
                yield

            # Set to stopping if clicked
            def OnLButtonUp(self):
                return Cell.State.Stopping(self.mCell)

            # Pending to Playing if we'll hit our trigger res
            def Advance(self):
                # If we're playing and our row is switching to something else, we are stopping
                if isinstance(self.mCell.GetRow().GetActiveState(), Row.State.Switching):
                    if self.mCell.GetRow().GetPendingCell() != self.mCell:
                        return Cell.State.Stopping(self.mCell)
                # If our column is stopping, we're stopping
                if isinstance(self.mCell.GetCol().GetActiveState(), Column.State.Stopping):
                    return Cell.State.Stopping(self.mCell)

        class Stopping(_state):
            def __init__(self, cell):
                super(type(self), self).__init__(cell, 'Stopping')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                yield

            # Revert to playing if stopping clicked
            def OnLButtonUp(self):
                return Cell.State.Playing(self.mCell)

            # Pending to Playing if we'll hit our trigger res
            def Advance(self):
                # If we're stopping and either our row or column is playing, we're playing
                if isinstance(self.mCell.GetCol().GetActiveState(), Column.State.Playing):
                    return Cell.State.Playing(self.mCell)
                if isinstance(self.mCell.GetRow().GetActiveState(), Row.State.Playing):
                    return Cell.State.Playing(self.mCell)
                # Otherwise, if our trigger will be hit, we're stopped
                if self.mCell.WillTriggerBeHit():
                    return Cell.State.Stopped(self.mCell)

        class Stopped(_state):
            def __init__(self, cell):
                super(type(self), self).__init__(cell, 'Stopped')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # If the previous state was playing,
                # we've got to stop any playing voices
                if isinstance(prevState, Cell.State.Playing):
                    self.mCell.GetGrooveMatrix().StopCell(self.mCell)
                # set the color to off
                self.mCell.GetDrawable().SetColor(self.mCell.mRow.clrOff)
                yield

            # Clicking a stopped cell will make it pending
            def OnLButtonUp(self):
                return Cell.State.Pending(self.mCell)

            # We'll advance to Pending if our column is pending
            def Advance(self):
                if isinstance(self.mCell.GetCol().GetActiveState(), Column.State.Pending):
                    return Cell.State.Pending(self.mCell)

from Row import Row
from Column import Column
