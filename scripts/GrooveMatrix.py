# pyl wrapped classes
from MatrixUI import MatrixUI
from ClipLauncher import ClipLauncher
import Shape

# All of the UI elements are entities
from Entity import Cell, Row

# Input manager... handles input
from InputManager import InputManager, MouseManager, KeyboardManager, Button

# Some misc stuff
from Util import Constants, ctype_from_addr

import sdl2

class GrooveMatrix:
    # Get refs to c objects, init diRows empty
    def __init__(self, pMatrixUI, pClipLauncher):
        # Get the C++ wrapped objects
        self.cMatrixUI = MatrixUI(pMatrixUI)
        self.cClipLauncher = ClipLauncher(pClipLauncher)

        # Construct a circle for mouse hit detection
        nMouseRad = 3
        self.nHitShapeIdx = self.cMatrixUI.AddShape(Shape.Circle, [0,0], {'r' : nMouseRad})

        # No rows yet
        self.diRows = {}
        self.setEntities = set()

        # construct the keyboard button handler functions
        # Quit function
        def fnQuit(btn, keyMgr):
            nonlocal self
            self.cMatrixUI.SetQuitFlag(True)
        keyQuit = Button(sdl2.keycode.SDLK_ESCAPE, fnUp = fnQuit)
        # Play/pause
        def fnPlayPause(btn, keyMgr):
            nonlocal self
            self.cClipLauncher.SetPlayPause(not(self.cClipLauncher.GetPlayPause()))
        keyPlayPause = Button(sdl2.keycode.SDLK_SPACE, fnUp = fnPlayPause)
        # Construct the keyboard manager
        keyMgr = KeyboardManager([keyQuit, keyPlayPause])

        # Mouse handling function
        # LButtonDown sets mouse circ active, moves to mousePos
        def fnLBDown(btn, mouseMgr):
            nonlocal self
            # Move mouse circle to pos, activate
            cMouseCirc = Shape.Shape(self.cMatrixUI.GetShape(self.nHitShapeIdx))
            cMouseCirc.SetCenterPos(mouseMgr.mousePos)
            cMouseCirc.SetIsActive(True)
        # LButtonDown sets mouse circ active, moves to mousePos
        def fnLBUp(btn, mouseMgr):
            nonlocal self
            cMouseCirc = Shape.Shape(self.cMatrixUI.GetShape(self.nHitShapeIdx))
            for ent in self.setEntities:
                if self.cMatrixUI.GetIsOverlapping(ent.GetShape().c_ptr, cMouseCirc.c_ptr):
                    ent.OnLButtonUp()
            # Deactivate mouse circ
            cMouseCirc.SetIsActive(False)
        mouseMgr = MouseManager([Button(sdl2.SDL_BUTTON_LEFT, fnDown = fnLBDown, fnUp = fnLBUp)])

        # Construct input manager
        self.mInputManager = InputManager(keyMgr, mouseMgr)

    def HandleEvent(self, sdlEvent):
        self.mInputManager.HandleEvent(sdlEvent)

    # To add a row, provide a name, colors, and list of cliips
    def AddRow(self, strName, clrOn, clrOff, liClips):
        # Determine the y pos of this row
        nRows = len(self.diRows.keys())
        nPosY0 = Constants.nGap + Row.nHeaderH / 2
        nPosY = nPosY0 + nRows * (Row.nHeaderH + Constants.nGap)

        # Construct row and add to dict (Cells constructed by Row)
        r = Row(self, liClips, clrOn, clrOff, nPosY)

        # Store row and all its cells in one container
        self.diRows[strName] = r
        self.setEntities.add(r)
        self.setEntities.update(c for c in r.liCells)
