from StateGraph import State
import CellState

import contextlib
import abc

class Pending(State):
    def __init__(self, row):
        State.__init__(self, 'pending')
        self.mRow = row
        pass

    @contextlib.contextmanager
    def Activate(self, SG, prevState):
        # I think this can only happen if stopped
        if not(isinstance(prevState, Stopped)):
            raise RuntimeError('Weird state transition!')
        if self.mRow.GetPendingCell() is None:
            raise RuntimeError('Weird state transition!')
        self.mRow.GetPendingCell().SetState(CellState.Pending)
        # We also have to start oscillating color
        yield

class Stopped(State):
    def __init__(self, row):
        State.__init__(self, 'stopped')
        self.mRow = row
        pass

    @contextlib.contextmanager
    def Activate(self, SG, prevState):
        # set the color to off (cell handles itself)
        print('Stopping', self.mRow.GetActiveCell())
        if self.mRow.GetActiveCell() is not None:
            self.mRow.GetActiveCell().SetState(CellState.Stopped)
            self.mRow.mActiveCell = None
        self.mRow.GetDrawable().SetColor(self.mRow.clrOff)
        yield

class Playing(State):
    def __init__(self, row):
        State.__init__(self, 'playing')
        self.mRow = row
        pass

    @contextlib.contextmanager
    def Activate(self, SG, prevState):
        # set color to on
        self.mRow.GetPendingCell().SetState(CellState.Playing)
        self.mRow.GetDrawable().SetColor(self.mRow.clrOn)
        yield
