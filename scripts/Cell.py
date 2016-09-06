import StateGraph
from MatrixEntity import MatrixEntity
import contextlib

class Cell(MatrixEntity):
    # Cells are represented by a circle with this radius
    nRadius = 25

    # Constructor takes GM, row, a clip, and the initial volume
    def __init__(self, GM, row, cClip, fVolume):
        # set up ID
        super(Cell, self).__init__(GM)

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

        # Set component IDs
        self.SetComponentID()

        # Create state graph nodes
        pending = State.Pending(self)
        playing = State.Playing(self)
        stopped = State.Stopped(self)

        # Create di graph and add states
        G = nx.DiGraph()
        G.add_edge(pending, playing)
        G.add_edge(pending, stopped)
        G.add_edge(stopped, pending)
        G.add_edge(playing, stopped)

        # This is the function that advances the state graph
        # and determines if a state transition is in order
        # For cells it's very dumb, and probably unnecessary
        def fnAdvance(SG):
            # Cells will have a member _mNextState - whenever it is set,
            # the graph will advance and the new state will become active
            nonlocal self
            return self._mNextState

        # Create state graph with above variables,
        # set initial state to stopped, declare _mNextState = stopped
        self.mSG = StateGraph.StateGraph(G, fnAdvance, stopped)
        self._mNextState = self.GetActiveState()

    # Setting state assigns _mNextState and advances
    def SetState(self, stateType):
        # If they're different types, assign and advance
        if not isinstance(self.GetActiveState(), stateType):
            self._mNextState = stateType(self)
            self.mSG.AdvanceState()

    # Return the state graph's active state
    def GetActiveState(self):
        return self.mSG.GetActiveState()

    # Get our row
    def GetRow(self):
        return self.mRow

    # Get our trigger resolution
    def GetTriggerRes(self):
        return self.nTriggerRes

    # Mouse handler override
    # Clicking a cell will set the row's pending cell accordingly
    def OnLButtonUp(self):
        # If stopped, set us to pending
        if isinstance(self.GetActiveState(), State.Stopped):
            self.mRow.SetPendingCell(self)
        # If pending, set row's pending to its current active state
        elif isinstance(self.GetActiveState(), State.Pending):
            # We should have been the row's pending cell
            if self.mRow.GetPendingCell() is not self:
                raise RuntimeError('Error: whose pending cell was', self.nID, '?')
            # Set to current active, if None no harm done
            self.mRow.SetPendingCell(self.mRow.GetActiveCell())
        # If playing, a click should stop us
        elif isinstance(self.GetActiveState(), State.Playing):
            # But we should have been active
            if self.mRow.GetActiveCell() is not self:
                raise RuntimeError('Error: whose active cell was', self.nID, '?')
            # A pending cell of None means stop at the next trigger
            self.mRow.SetPendingCell(None)
        # Uh oh
        else:
            raise RuntimeError('wtf happened?')

    # Cell state declarations
    # This outer class is just so I can do things like Cell.State.Pending
    class State:
        # Inner class is what all states inherit from
        class _state(StateGraph.State):
            # Every state instance owns a ref to its cell
            def __init__(self, cell, name):
                StateGraph.State.__init__(self, str(name))
                self.mCell = cell

        # Pending state, gets set when we are queued up to play.
        class Pending(_state):
            def __init__(self, cell):
                _state.__init__(self, cell, 'Pending')

            # State lifetime management
            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # Entering the pending state should start some sort
                # of drawable cycle (i.e flashing)
                yield
                # Exiting doesn't have to do anything for now

        # The stopped state is active when we aren't playing or pending
        # that doesn't mean the actual voice isn't rendering a tail, though
        class Stopped(_state):
            def __init__(self, cell):
                _state.__init__(self, cell, 'Stopped')

            # State lifetime management
            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # We should have been the active cell
                if self.mCell.GetRow().GetActiveCell() is not self.mCell:
                    raise RuntimeError('Weird state transition')
                # self.mCell.mRow.mActiveCell = None
                # If the previous state was playing,
                # we've got to stop any playing voices
                if isinstance(prevState, Playing):
                    gm = self.mCell.GetGrooveMatrix()
                    gm.StopCell(self.mCell)
                # set the color to off
                self.mCell.GetDrawable().SetColor(self.mCell.mRow.clrOff)
                yield
                # Exiting doesn't have to do anything for now

            # The playing state is active when the cell
            # is rendering the head of the clip
            class Playing(_state):
                def __init__(self, cell):
                    _state.__init__(self, cell, 'Playing')

                # State lifetime management
                @contextlib.contextmanager
                def Activate(self, SG, prevState):
                    # We should have been the row's pending cell
                    if self.mCell.GetRow().GetPendingCell() is not self.mCell:
                        raise RuntimeError('Weird state transition')
                    # set color to on
                    self.mCell.GetDrawable().SetColor(self.mCell.mRow.clrOn)
                    # Once the pending state starts doing stuff, we'll
                    # have to reset that state (i.e some oscillator angle)
                    # Tell GM to start playing my stuff
                    self.mCell.mGM.StartCell(self.mCell)
                    yield
                    # Exit does nothing for now
