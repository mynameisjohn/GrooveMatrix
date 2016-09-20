import abc

import StateGraph
import Drawable
import Shape

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
	def __init__(self, GM):
	    # Set ID, store GM
		self.nID = MatrixEntity.NewID()
		self.mGM = GM

		# Init these to -1
		# (eventually these will be subclass specific)
		self.nShIdx = -1
		self.nDrIdx = -1

        # Stategraph will have to be constructed by children
        self.mSG = None

    def GetActiveState(self):
        return self.mSG.GetActiveState()

    def GetNextState(self):
        return self.mSG.GetNextState()

    def AdvanceState(self):
        return self.mSG.AdvanceState()

    def SetState(self, nextState):
        if nextState != self.GetActiveState():
            self.mSG.SetState(stateType(self))

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

    def OnLButtonUp(self):
        self.SetState(self.GetActiveState().OnLButtonUp())

    def fnAdvance(SG):
        nonlocal self
        nextState = self.GetActiveState().Advance()
        if nextState is not None:
            return nextState
        return self.GetActiveState()

	class _state(StateGraph.State):
		def __init__(self, name):
			StateGraph.State.__init__(self, str(name))
		@abc.abstractmethod
		def OnLButtonUp(self):
			pass
		@abc.abstractmethod
		def Advance(self):
			pass
