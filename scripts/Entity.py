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

import Shape
import Drawable

from Util import Constants

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
		self.cGM = GM

		self.nShIdx = -1
		self.nDrIdx = -1

	def GetShape(self):
		return Shape.Shape(self.cGM.cMatrixUI.GetShape(self.nShIdx))

	def GetDrawable(self):
		return Drawable.Drawable(self.cGM.cMatrixUI.GetDrawable(self.nDrIdx))

	def SetComponentID(self):
		self.GetShape().SetEntID(self.nID)
		self.GetDrawable().SetEntID(self.nID)

	@abc.abstractmethod
	def OnLButtonUp(self):
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
	nRadius = 50
	def __init__(self, GM, cClip, fVolume):
		# set up ID
		super(Cell, self).__init__(GM)

		# Store cClip ref and volume
		self.cClip = cClip
		self.fVolume = float(fVolume)

		# Set up UI components
		self.nShIdx = GM.cMatrixUI.AddShape(Shape.Circle, [0, 0], {'r' : Cell.nRadius})
		self.nDrIdx = GM.cMatrixUI.AddDrawableIQM('../models/circle.iqm', [0, 0], 2 * [Cell.nRadius], [0, 0, 0, 1], 0. )

		# Set component IDs
		self.SetComponentID()

	# Mouse handler override
	def OnLButtonUp(self):
		print('here I go down the jope')

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

	# Constructor takes list of cells and GM, on/off color
	def __init__(self, GM, liClips, clrOn, clrOff, nPosY):
		# Get ID
		super(Row, self).__init__(GM)

		# Create UI components
		nRowX = Constants.nGap + Row.nHeaderW / 2
		self.nShIdx = GM.cMatrixUI.AddShape(Shape.AABB, [nRowX, nPosY], {'w' : Row.nHeaderW, 'h': Row.nHeaderH})
		self.nDrIdx = GM.cMatrixUI.AddDrawableIQM('../models/quad.iqm', [nRowX, nPosY], [Row.nHeaderW, Row.nHeaderH], clrOff, 0. )

		# Move cells to correct pos, set colors
		self.clrOn = clrOn
		self.clrOff = clrOff
		nCellPosX = Row.nHeaderW + 2 * Constants.nGap + Cell.nRadius
		nCellPosDelta = 2 * Cell.nRadius + Constants.nGap

		# Construct cells from cClips
		self.liCells = []
		for i in range(len(liClips)):
			# Construct the cell
			cell = Cell(GM, liClips[i], 1.)

			# Determine x pos
			liCellPos = [nCellPosX, nPosY]
			nCellPosX += nCellPosDelta
			# Set position for shape
			cShape = cell.GetShape()
			cShape.SetCenterPos(liCellPos)

			# Set position for drawable
			cDrawable = cell.GetDrawable()
			cDrawable.SetPos2D(liCellPos)
			#cDrawable.SetColor(clrOff)

			# Add to our list
			self.liCells.append(cell)

		# Set up play state
		self.mActiveCell = None
		self.mActiveCell = None

		# Set Component IDs
		self.SetComponentID()

	# Mouse handler override
	def OnLButtonUp(self):
		print('here I go down the slope')

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
