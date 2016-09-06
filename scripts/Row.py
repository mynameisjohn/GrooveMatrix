import StateGraph
from MatrixEntity import MatrixEntity
import contextlib

class Row(MatrixEntity):
    # Cells are represented by a rect
    nHeaderW = 200	# width of row header
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
        pending = State.Pending(self)
        playing = State.Playing(self)
        stopped = State.Stopped(self)

        # Create di graph and add states
        G = nx.DiGraph()
        G.add_edge(pending, playing)
        G.add_edge(pending, stopped)
        G.add_edge(stopped, pending)
        G.add_edge(playing, stopped)

        # The state advance function
        def fnAdvance(SG):
            nonlocal self, pending, playing, stopped
            # If we are stopped but have a pending cell, we're now pending
            if self.GetActiveState() == stopped and self.mPendingCell is not None:
                return pending

            # If we're pending and my pending cell is None, we're stopped
            if self.GetActiveState() == pending and self.mPendingCell is None:
                return stopped

            # Otherwise, we must determine if enough samples have advanced
            # to transition from pending to playing or playing to stopped
            # Determine if our trigger res will be hit
            nCurPos = self.mGM.GetCurrentSamplePos()
            nNewPos = nCurPos + self.mGM.GetCurrentSamplePosInc()
            nTrigger = self.GetTriggerRes() - self.mGM.GetPreTrigger()
            # If we'll hit the trigger
            if nCurPos < nTrigger and nNewPos >= nTrigger:
                # If we were pending, we're now playing
                if self.GetActiveState() == pending:
                    return playing
                # If we were playing
                elif self.GetActiveState() == playing:
                    # A pending none means we're stopped
                    if self.GetPendingCell() is None:
                        return stopped
                    # If not None, if changing, update our cells directly
                    elif self.GetPendingCell() is not self.GetActiveCell():
                        # The reason we have to set these by hand is because
                        # we're going from playing to playing, meaning no
                        # state transition occurs. Maybe make a new state?
                        self._makePendingActive()

            # Nothing to be done
            return self.GetActiveState()

        # Create state graph member, init state to stopped
        self.mSG =  StateGraph.StateGraph(G, fnAdvance, stopped)

    # Set the pending cell
    # Note that this doesn't actually transition the cell
    # into a pending state unless we were pending
    # If we were not, then the transition to pending takes care of it
    def SetPendingCell(self, cell):
        # If not None, it better be one of ours
        if cell is not None and cell not in self.liCells:
            raise RuntimeError('Pending Cell not in row!')
        # If changing
        if self.mPendingCell is not cell:
            # If we have an actual pending cell, make sure it knows it's stopped
            if self.mPendingCell is not self.mActiveCell:
                if self.mPendingCell is not None:
                    self.mPendingCell.SetState(Cell.State.Stopped)
            # Assign mPendingCell, set it to pending
            self.mPendingCell = cell
            self.mPendingCell.SetState(Cell.State.Pending)

    # Assign active as pending, if possible
    def _makePendingActive(self):
        # If the pending is not the active
        if self.mPendingCell is not self.mActiveCell:
            # If we had an active cell, set it to stopped
            if self.GetActiveCell() is not None:
                # The active cell should have been playing
                if not(isinstance(self.GetActiveCell().GetState(), Cell.State.Playing)):
                    raise RuntimeError('Error: Weird state transition!')
                # Set it to stopped
                self.GetActiveCell().SetState(Cell.State.Stopped)
            # If we had a pending cell,set it to playing
            if self.GetPendingCell() is not None:
                self.GetPendingCell().SetState(Cell.State.Playing)
            # Assign active to pending, leave pending alone
            self.mActiveCell = self.mPendingCell

    # Get graph's active state
    def GetActiveState(self):
        return self.mSG.GetActiveState()

    def GetTriggerRes(self):
        # Return our active cell's if possible
        if self.mActiveCell is not None:
            return self.mActiveCell.GetTriggerRes()
            # Otherwise take it to be the shortest of all (?)
            return min(c.nTriggerRes for c in self.liCells)

    # Mouse handler override
    def OnLButtonUp(self):
        # Clicking a row should stop any playing cells
        if isinstance(self.GetActiveState(), Row.State.Playing):
            self.SetPendingCell(None)

    # Get the pending or active cell
    def GetPendingCell(self):
        return self.mPendingCell

    def GetActiveCell(self):
        return self.mActiveCell

    # Update function advances state graph
    # and gives each cell a chance to Update
    def Update(self):
        self.mSG.AdvanceState()
        for cell in self.liCells:
            cell.Update()

    # Row state declarations
    # This outer class is just so I can do things like Row.State.Pending
    class State:
        # Inner class is what all states inherit from
        def __init__(self, row, name):
            StateGraph.State.__init__(self, str(name))
            self.mRow = row

        # Pending state means no cells are playing and one is pending
        class Pending(_state):
            def __init__(self, row):
                _state.__init__(self, row, 'Pending')

            # State lifetime management
            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # WE should have had a pending cell before this occurred
                if self.mRow.GetPendingCell() is None:
                    raise RuntimeError('Weird state transition!')
                # But this actually transitions the cell to pending...?
                # self.mRow.GetPendingCell().SetState(CellState.Pending)
                # We also have to start oscillating color
                yield

        # The Row.Stopped state means all cells in row are stopped
        class Stopped(_state):
            def __init__(self, row):
                _state.__init__(self, row, 'Stopped')

            # When the stopped state is activated, the active cell
            # will be set to stopped and the color will change
            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # There should have been an active or pending cell
                if self.mRow.GetActiveCell() is None:
                    if self.mRow.GetPendingCell() is None:
                        raise RuntimeError('Weird state transition!')
                else:
                    # Tell our active cell (if any) to stop (sets mActiveCell)
                    self.mRow.GetActiveCell().SetState(Cell.State.Stopped)
                # Set the color of our row rect (Cell handles itself)
                self.mRow.GetDrawable().SetColor(self.mRow.clrOff)
                yield
                # No exit for now

        # The row playing state means one of our cells is playing
        class Playing(_state):
            def __init__(self, row):
                _state.__init__(self, row, 'Playing')

            # When the Playing state is activated, the pending cell
            # will be set to playing and the color will change
            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # None should have been playing
                if any(isinstance(c, Cell.State.Playing) for c in self.mRow.liCells):
                    raise RuntimeError('Weird state transition!')
                # I just want to try and catch everything
                if self.mPendingCell is None or self.mActiveCell is not None:
                    raise RuntimeError('Weird state transition!')
                # Make pending cell active
                self._makePendingActive()
                # set color to on
                self.mRow.GetDrawable().SetColor(self.mRow.clrOn)
                yield
                # No exit for now
