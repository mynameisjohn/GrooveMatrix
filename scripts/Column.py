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
        # Move cells to correct pos, set colors
        self.clrOn = [1,1,1,1]
        self.clrOff = [1,1,1,1]

        # Create UI components
        # column triangles will be above the cells, but right now
        # that placement code is kind of split up. Please centralize it
        nHalfTri = Column.nTriDim / 2
        nColY = GM.GetCamera().GetScreenHeight() - (Constants.nGap + nHalfTri)
        triVerts = [[-nHalfTri, -nHalfTri], [nHalfTri, -nHalfTri], [0, nHalfTri]]

        # Create triangle shape
        self.nShIdx = GM.cMatrixUI.AddShape(Shape.Triangle, [nPosX, nColY], {
            'aX' : triVerts[0][0], 'aY' : triVerts[0][1],
            'bX' : triVerts[1][0], 'bY' : triVerts[1][1],
            'cX' : triVerts[2][0], 'cY' : triVerts[2][1]})

        # Create triangle drawable, column needs an ID now
        self.nID = MatrixEntity.NewID()
        self.nDrIdx = GM.cMatrixUI.AddDrawableTri('col'+str(self.nID), triVerts, [nPosX, nColY], [1, 1], self.clrOff, 0. )

        # If a GM instance is making us with cells, they get stored here
        self.setCells = {c for c in setCells if isinstance(c, Cell)}
        for c in self.setCells:
            c.SetCol(self)

        stopped = Column.State.Stopped(self)
        pending = Column.State.Pending(self)
        playing = Column.State.Playing(self)
        stopping = Column.State.Stopping(self)

        # Create di graph and add states
        G = nx.DiGraph()
        G.add_edge(pending, playing)
        G.add_edge(stopped, pending)
        G.add_edge(playing, stopping)
        G.add_edge(stopping, playing)
        G.add_edge(stopping, stopped)

        # Call base constructor to construct state graph
        super(Column, self).__init__(GM, G, stopped)

        # Set Component IDs
        self.SetComponentID()

    # A GM instance will own a list of rows and columns. Every time
    # a row is added to the GM, it will look at its columns and add
    # any cells needed - if a column is missing, it will be constructed
    def AddCell(self, cell):
        self.setCells.add(cell)
        cell.SetCol(self)

    # Column states are a bit odd
    class State:
        class _state(MatrixEntity._state):
            def __init__(self, col, name):
                MatrixEntity._state.__init__(self, name)
                self.mCol = col

        # When a column is stopped, it is meant to indicate
        # that all its cells are stopped and that a click
        # will set all cells to pending
        class Stopped(_state):
            def __init__(self, col):
                super(type(self), self).__init__(col, 'Stopped')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # When a column is set to stopped, set all its cells to stopped
                for c in self.mCol.setCells:
                    c.SetState(Cell.State.Stopped(c))
                # Set color to off
                yield

            def Advance(self):
                # If any of our cells are pending, then we are pending
                if any(isinstance(c.GetActiveState(), Cell.State.Pending) for c in self.mCol.setCells):
                    return Column.State.Pending(self.mCol)

            # When a stopped column is clicked,
            # it should set itself to pending.
            # its cells should see this and set
            # themselves to pending accordingly
            def OnLButtonUp(self):
                return Column.State.Pending(self.mCol)

        # The pending state is entered when a stopped column is clicked,
        # or any of our cells start pending. It can be used to clear that
        # pending state, and will advance to Playing if any start playing
        class Pending(_state):
            def __init__(self, col):
                super(type(self), self).__init__(col, 'Pending')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # When a column is set to pending, set all its cells
                # to pending. If that isn't possible, there's probably
                # some exception I should be handling...
                for c in self.mCol.setCells:
                    c.SetState(Cell.State.Pending(c))
                yield

            # Revert to stopped if clicked
            def OnLButtonUp(self):
                return Column.State.Stopped(self.mCol)

            def Advance(self):
                # Pending to Playing if any cells are playing
                if any(isinstance(c.GetActiveState(), Cell.State.Playing) for c in self.mCol.setCells):
                    return Column.State.Playing(self)
                # Stopped if all are stopped
                if all(isinstance(c.GetActiveState(), Cell.State.Stopped) for c in self.mCol.setCells):
                    return Column.State.Stopped(self)

        # The playing state of a column indicates that
        # at least one of our cells is playing - clicking
        # the column will set the column and  playing cells to stopping
        class Playing(_state):
            def __init__(self, col):
                super(type(self), self).__init__(col, 'Playing')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # Set our color to on
                yield

            # Stopping if clicked
            def OnLButtonUp(self):
                return Column.State.Stopping(self.mCol)

            def Advance(self):
                # Stopping if all are stopping
                if all(isinstance(c.GetActiveState(), Cell.State.Stopping) for c in self.mCol.setCells):
                    return Column.State.Stopping

        # The stopping state of a column is entered if it is clicked while playing,
        # or if all of its cells are set to stopping
        class Stopping(_state):
            def __init__(self, col):
                super(type(self), self).__init__(col, 'Stopping')

            @contextlib.contextmanager
            def Activate(self, SG, prevState):
                # When a column is set to stopping,
                # all of its cells should be stopping as well
                for c in self.mCol.setCells:
                    c.SetState(Cell.State.Stopping(c))
                yield

            # A column will advance to stopped if all its cells are stopped,
            # and it will revert to playing if all its cells have been set to playing
            def Advance(self):
                if all(isinstance(c.GetActiveState(), Cell.State.Stopped) for c in self.mCol.setCells):
                    return Column.State.Stopped(self.mCol)
                if all(isinstance(c.GetActiveState(), Cell.State.Playing) for c in self.mCol.setCells):
                    return Column.State.Playing(self.mCol)

            # If a column is stopping and it gets clicked,
            # it should revert to playing (I think)
            def OnLButtonUp(self):
                return Column.State.Playing(self.mCol)
