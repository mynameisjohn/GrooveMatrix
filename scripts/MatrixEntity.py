import abc

import StateGraph
import Drawable
import Shape

# Cells, Rows, and Columns all inherit
# from this class. MatrixEntity's have
# Drawable and Collision components, a
# reference to a GM instance, and a
# StateGraph instance that must be
# constructed with the child states
#
# Entities can modify the data of other entities during Activation,
# but this should be done with some forethought. Here I don't have any
# code where a Cell modifies its Row or Column, but I do have code where
# Rows and Columns modify their cells.
#
# I do think it's a bit strange, but the responsibility had to be split
# up somehow. In general I think an object should only modify other objects
# if the other objects are somehow owend by the original

class MatrixEntity:
    # class variable that keeps a counter
    # of entities created, which is useful
    # for generating unique IDs
    nEntsCreated = 0

    # Increment the class ID counter and return the old
    def NewID():
        nID = MatrixEntity.nEntsCreated
        MatrixEntity.nEntsCreated += 1
        return nID

    # Constructor takes in groove matrix instance
    # In the future I'd like this function to
    # construct the state graph, and it should be
    # called after the child constructor
    def __init__(self, GM, dG, s0):
        # Set ID if not already done
        if hasattr(self, 'nID') == False:
            self.nID = MatrixEntity.NewID()

        # Store GM
        self.mGM = GM

        # Init these to -1 if not already created,
        # eventually they'll be subclass specific
        if hasattr(self, 'nShIdx') == False:
            self.nShIdx = -1
        if hasattr(self, 'nDrIdx') == False:
            self.nDrIdx = -1

        # Because of the way entity state transitions work,
        # every entity should use this advance function for its graph
        def fnAdvance(SG):
            nonlocal self
            nextState = self.GetActiveState().Advance()
            if nextState is not None:
                return nextState
            return self.GetActiveState()

        # Construct state graph
        self.mSG = StateGraph.StateGraph(dG, fnAdvance, s0, True)

    # State access functions
    def GetActiveState(self):
        return self.mSG.GetActiveState()

    def GetNextState(self):
        return self.mSG.GetNextState()

    def AdvanceState(self):
        return self.mSG.AdvanceState()

    # Set the state directly, this will
    # fail if the states are not neighbors
    def SetState(self, nextState):
        if nextState != self.GetActiveState() and nextState is not None:
            self.mSG.SetState(nextState)

    # Get the collision shape from the matrix UI object
    def GetShape(self):
        if self.nShIdx < 0:
            raise RuntimeError('Error: Invalid shape index for Entity', self.nID)
        return Shape.Shape(self.mGM.cMatrixUI.GetShape(self.nShIdx))

    # Get the drawable object from the matrix UI
    def GetDrawable(self):
        if self.nDrIdx < 0:
            raise RuntimeError('Error: Invalid drawable index for Entity', self.nID)
        return Drawable.Drawable(self.mGM.cMatrixUI.GetDrawable(self.nDrIdx))

    # This syncs up the C++ components with our ID
    def SetComponentID(self):
        self.GetShape().SetEntID(self.nID)
        self.GetDrawable().SetEntID(self.nID)

    # Returns ref to GM instance
    def GetGrooveMatrix(self):
        return self.mGM

    # These are probably worthwhile
    def __hash__(self):
        return hash(self.nID)
    def __eq__(self, other):
        return self.nID == other.nID

    # Every state must implement OnLButtonUp
    def OnLButtonUp(self):
        self.SetState(self.GetActiveState().OnLButtonUp())

    # Entity's can override this as they like, but
    # the base should be called and use its return value
    # to determine if the state should keep advancing
    def Update(self):
        return self.mSG.AdvanceState()

    # The three important methods of a state are
    # Activate, OnLButtonUp, and Advance
    # The activate function (virtual to StateGraph.State)
    # is the only function that should actually modify data
    class _state(StateGraph.State):
        def __init__(self, name):
            StateGraph.State.__init__(self, str(name))

        # The OnLButtonUp function should return the state
        # expected from the entity after a click (which depends
        # on the current state, which is why its a state function)
        # Returning None means no state change
        @abc.abstractmethod
        def OnLButtonUp(self):
            pass

        # The Advance function looks at the current state of things
        # but does not change any data - instead it will return a new
        # state object if the state is advancing, or return None if
        # the state should stay the same
        @abc.abstractmethod
        def Advance(self):
            pass
