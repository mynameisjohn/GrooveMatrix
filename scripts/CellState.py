from StateGraph import State
import RowState

import contextlib
import abc

class Pending(State):
    def __init__(self, cell):
        State.__init__(self, 'pending')
        self.mCell = cell

    @contextlib.contextmanager
    def Activate(self, SG, prevState):
        # I think this can only happen if stopped
        if not(isinstance(prevState, Stopped)):
            raise RuntimeError('Weird state transition!')
        # We also have to start oscillating color
        yield

    def OnLButtonUp(self):
        # If pending, set row's pending to none
        # (which will set our cell to stopping)
        self.mRow.SetPendingCell(None)

class Stopped(State):
    def __init__(self, cell):
        State.__init__(self, 'stopped')
        self.mCell = cell

    @contextlib.contextmanager
    def Activate(self, SG, prevState):
        # set the color to off
        self.mCell.GetDrawable().SetColor(self.mCell.mRow.clrOff)
        # If the previous state was playing,
        # we've got to stop any playing voices
        if isinstance(prevState, Playing):
            gm = self.mCell.GetGrooveMatrix()
            gm.StopCell(self.mCell)
        yield

    def OnLButtonUp(self):
        # If we're stopped, click to set pending
        self.mCell.GetRow().SetPendingCell(self.mCell)

class Playing(State):
    def __init__(self, cell):
        State.__init__(self, 'playing')
        self.mCell = cell
        pass

    @contextlib.contextmanager
    def Activate(self, SG, prevState):
        self.mCell.mRow.mActiveCell = self.mCell
        # set color to on
        self.mCell.GetDrawable().SetColor(self.mCell.mRow.clrOn)
        # If the previous state was pending,
        # reset any of that state (osc float)
        # Tell GM to start playing my stuff
        self.mCell.mGM.StartCell(self.mCell)
        yield

    def OnLButtonUp(self):
        # If we're playing, a click will stop us
        self.mCell.mRow.SetPendingCell(None)
