'''
Conventions:
	nVariableName = signed integer
	pVariableName = pointer to C++ object
	cVariableName = pyl backed
	mVariableName = class member
	fVariableName = float
	strVariableName = string
	liVariableName = list
	setVariableName = set
	diVariableName = dict
	clrVariableName = color
'''

import abc

import networkx as nx

import Shape
import Drawable

from Util import Constants
import CellState
import RowState
import StateGraph

from collections import namedtuple

# All entities will have a unique ID,
# A drawable and shape component,
# a way of dealing with mouse clicks
# and be hashable
class Entity:
	# class variable that keeps a counter
	# of entities created, which is useful
	# for generating unique IDs
	nEntsCreated = 0
	# Increment the class ID counter and return the old
	def NewID():
		ret = Entity.nEntsCreated
		Entity.nEntsCreated += 1
		return ret

	# Constructor takes in groove matrix instance
	def __init__(self, GM):
		self.nID = Entity.NewID()
		self.mGM = GM

		self.nShIdx = -1
		self.nDrIdx = -1

	def GetShape(self):
		return Shape.Shape(self.mGM.cMatrixUI.GetShape(self.nShIdx))

	def GetDrawable(self):
		return Drawable.Drawable(self.mGM.cMatrixUI.GetDrawable(self.nDrIdx))

	def SetComponentID(self):
		self.GetShape().SetEntID(self.nID)
		self.GetDrawable().SetEntID(self.nID)

	def GetGrooveMatrix(self):
		return self.mGM

	@abc.abstractmethod
	def OnLButtonUp(self):
		pass

	def Update(self):
		pass

	# These are probably worthwhile
	def __hash__(self):
		return hash(self.nID)
	def __eq__(self, other):
		return self.nID == other.nID

# Cells will own an actual clip
# object, and it will know its
# Name,
# Head filename and duration,
# Tail filename and duration,
# Fade duration,
# Volume
# Actual cliplauncher clip
class Cell(Entity):
	# Cells are a circle
	nRadius = 25
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
		pending = CellState.Pending(self)
		playing = CellState.Playing(self)
		stopped = CellState.Stopped(self)

		# Create di graph and add states
		G = nx.DiGraph()
		G.add_edge(pending, playing)
		G.add_edge(pending, stopped)
		G.add_edge(stopped, pending)
		G.add_edge(playing, stopped)

		# The graph advance function, dumb for now
		def fnAdvance(SG):
			nonlocal self, pending, playing, stopped
			if self.mNextState is not self.GetActiveState():
				if self.mNextState in self.mSG.G.neighbors(self.mSG.activeState):
					return self.mNextState
			return self.GetActiveState()

		# Create state graph member, init state to stopped
		self.mSG =  StateGraph.StateGraph(G, fnAdvance, stopped)
		self.mNextState = self.GetActiveState()

	def SetState(self, stateType):
		if not isinstance(self.GetActiveState(), stateType):
			self.mNextState = stateType(self)
			self.mSG.AdvanceState()

	def GetActiveState(self):
		return self.mSG.GetActiveState()

	def GetRow(self):
		return self.mRow

	def GetTriggerRes(self):
		return self.nTriggerRes

	# Mouse handler override
	def OnLButtonUp(self):
		print(self.cClip.GetName())
		if not(isinstance(self.mSG.GetActiveState(), StateGraph.State)):
			raise ValueError('Error! Invalid cell state!')
		self.GetActiveState().OnLButtonUp()
		# # I guess the voice ID is just the ent ID... why not
		# if self.mRow.mActiveCell is not None:
		# 	if self.mRow.mActiveCell == self:
		# 		self.mRow.SetPendingCell(None)
		# 		return
		# self.mRow.SetPendingCell(self)

	def Update(self):
		self.mSG.AdvanceState()

# Rows will own a list of clips
# and can have one active clip,
# one pending clip,
# a row-specific on/off color
# A rect indicating its header
# and a rect indicating its range
class Row(Entity):
	# Make these dimensions class shared
	nHeaderW = 200	# width of row header
	nHeaderH = 50	# height of row header

	RowData = namedtuple('RowData', ('liClipData', 'clrOn', 'clrOff'))

	# Constructor takes list of cells and GM, on/off color
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

		# Set up play state
		self.mActiveCell = None
		self.mPendingCell = None

		# Set Component IDs
		self.SetComponentID()

		# Create state graph nodes
		pending = RowState.Pending(self)
		playing = RowState.Playing(self)
		stopped = RowState.Stopped(self)

		# Create di graph and add states
		G = nx.DiGraph()
		G.add_edge(pending, playing)
		G.add_edge(pending, stopped)
		G.add_edge(stopped, pending)
		G.add_edge(playing, stopped)

		# The graph advance function, dumb for now
		self.mNextState = None
		def fnAdvance(SG):
			nonlocal self, pending, playing, stopped
			# If stopped and we have a pending cell, we're now pending
			if self.GetActiveState() == stopped and self.mPendingCell is not None:
				return pending

			# Determine if our trigger res will be hit
			nCurPos = self.mGM.GetCurrentSamplePos()
			nNewPos = nCurPos + self.mGM.GetCurrentSamplePosInc()
			nTrigger = self.GetTriggerRes() - self.mGM.GetPreTrigger()
			if nCurPos < nTrigger and nNewPos >= nTrigger:
				# If we're pending, now we're playing
				if self.GetActiveState() == pending:
					return playing
				# If we're playing and the pending is None, we're stopped
				elif self.GetActiveState() == playing:
					if self.mPendingCell is None:
						return stopped
					elif self.mPendingCell is not self.GetActiveCell():
						self.GetActiveCell().SetState(CellState.Stopped)
						self.mPendingCell.SetState(CellState.Playing)

			# Nothing to be done, return current
			return self.GetActiveState()

		# Create state graph member, init state to stopped
		self.mSG =  StateGraph.StateGraph(G, fnAdvance, stopped)

	def SetPendingCell(self, cell):
		if cell is not None:
			if cell not in self.liCells:
				raise RuntimeError('Pending Cell not in row!')
			# I foresee some problems with updating before assigning...
			cell.SetState(CellState.Pending)
		self.mPendingCell = cell

	def GetActiveState(self):
		return self.mSG.GetActiveState()

	def GetTriggerRes(self):
		# Return our active cell's if possible
		if self.mActiveCell is not None:
			return self.mActiveCell.GetTriggerRes()
		# Otherwise take it to be the shortest of all
		return min(c.nTriggerRes for c in self.liCells)

	# Mouse handler override
	def OnLButtonUp(self):
		print('here I go down the slope')

	# def SetPendingCell(self, cell):
	# 	if cell is None:
	# 		self.mPendingCell = None
	# 		return True
	# 	if cell in self.liCells:
	# 		self.mPendingCell = cell
	# 		return True
	# 	return False

	def ExchangeActiveCell(self):
		if self.mPendingCell is not self.mActiveCell:
			self.mActiveCell = self.mPendingCell
			self.mActiveCell.GetDrawable().SetColor(self.clrOn)
			return True
		return False

	def GetPendingCell(self):
		return self.mPendingCell

	def GetActiveCell(self):
		return self.mActiveCell

	def Update(self):
		self.mSG.AdvanceState()
		for cell in self.liCells:
			cell.Update()

# A column is like a Scene in Ableton
# Rather than own a list of clips,
# colums will own an x index corresponding
# to its clip in each row
# When pressed, columns will set each row's
# pending clip to be the one in its column
# For convenience the entire class will own
# a list of all rows from which it can Toggle
# cell states at its index
class Col(Entity):
	liRows = None
	nTriDim = 100
	triVerts = [[-1, -1], [1, -1], [0, 1]]
	clrOff = None
	clrPending = None
	def __init__(self, GM, liRows, nRowIdx):
		if Col.liRows is not None:
			Col.liRows = liRows
		if any(len(r.liCells) <= nRowIdx for r in liRows) is False:
			raise RuntimeError('Creating column with no cells')

		# Create UI components, set x pos to be that of the first cell
		cMatrixUI = GM.cMatrixUI
		nPosX = liRows[0].liCells[0].GetShape().GetPosition()[0]
		strDrName = 'ColTri'+str(self.nIdx)
		diTriangleDetails = { 	'aX' : triVerts[0][0], 'aY' : triVerts[0][1],
	                            'bX' : triVerts[1][0], 'bY' : triVerts[1][1],
	                            'cX' : triVerts[2][0], 'cY' : triVerts[2][1]}
		self.nDrIdx = cMatrixUI.AddDrawableTri(strDrName, Col.triVerts, [nPosX, Col.nTriDim], [nTriDim, nTriDim], clrOff, 0.)
		self.nShIdx = cMatrixUI.AddShape(Shape.Triangle, [nPosX, Col.nTriDim], diTriangleDetails )
