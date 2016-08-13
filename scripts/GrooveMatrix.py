from MatrixUI import MatrixUI
from ClipLauncher import ClipLauncher

from Entity import Cell, Row
from Util import Constants, ctype_from_addr
import InputManager

class GrooveMatrix:
    # Get refs to c objects, init diRows empty
    def __init__(self, pMatrixUI, pClipLauncher, inputManager):
        self.cMatrixUI = MatrixUI(pMatrixUI)
        self.cClipLauncher = ClipLauncher(pClipLauncher)
        self.mInputManager = inputManager
        self.diRows = {}

    # To add a row, provide a name, colors, and list of cliips
    def AddRow(self, strName, clrOn, clrOff, liClips):
        # Determine the y pos of this row
        nRows = len(self.diRows.keys())
        nPosY0 = Constants.nGap + Row.nHeaderH / 2
        nPosY = nPosY0 + nRows * (Row.nHeaderH + Constants.nGap)

        # Construct row and add to dict (Cells constructed by Row)
        self.diRows[strName] = Row(self, liClips, clrOn, clrOff, nPosY)

    def GetMatrixUI(self):
        return self.cMatrixUI

    def GetClipLauncher(self):
        return self.cClipLauncher
