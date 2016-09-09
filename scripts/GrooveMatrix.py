# pyl wrapped classes
from MatrixUI import MatrixUI
import ClipLauncher as clCMD
from ClipLauncher import ClipLauncher
import Camera
import Camera
import Shape

# All of the UI elements are entities
from Cell import Cell
from Row import Row
from Column import Column

# Input manager... handles input
from InputManager import InputManager, MouseManager, KeyboardManager, Button

# Some misc stuff
from Util import Constants, ctype_from_addr

# for input handling
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

        # No rows or columns yet
        self.diRows = {}            # Rows are keyed by name
        self.liCols = []            # Columsn are in a list - for now
        self.setEntities = set()    # All entities are here

        # Reset play state
        self.Reset()

        # construct the keyboard button handler functions
        # Quit function
        def fnQuit(btn, keyMgr):
            nonlocal self
            self.cClipLauncher.SetPlayPause(False)
            self.cMatrixUI.SetQuitFlag(True)
        keyQuit = Button(sdl2.keycode.SDLK_ESCAPE, fnUp = fnQuit)
        # Play/pause
        def fnPlayPause(btn, keyMgr):
            nonlocal self
            self.cClipLauncher.SetPlayPause(not(self.cClipLauncher.GetPlayPause()))
        keyPlayPause = Button(sdl2.keycode.SDLK_SPACE, fnUp = fnPlayPause)
        # Construct the keyboard manager
        keyMgr = KeyboardManager([keyQuit, keyPlayPause])

        # Create ref to camera for fnLBDown to capture
        cCamera = Camera.Camera(self.cMatrixUI.GetCameraPtr())

        # Mouse handling function
        # LButtonDown sets mouse circ active, moves to mousePos
        def fnLBDown(btn, mouseMgr):
            nonlocal self, cCamera
            # Convert SDL mouse pos to screen pos
            mX = mouseMgr.mousePos[0]
            mY = cCamera.GetScreenHeight() - mouseMgr.mousePos[1]

            # Move mouse circle to pos, activate
            cMouseCirc = Shape.Shape(self.cMatrixUI.GetShape(self.nHitShapeIdx))
            cMouseCirc.SetCenterPos([mX, mY])
            cMouseCirc.SetIsActive(True)

        # LButtonDown sets mouse circ active, moves to mousePos
        def fnLBUp(btn, mouseMgr):
            nonlocal self
            cMouseCirc = Shape.Shape(self.cMatrixUI.GetShape(self.nHitShapeIdx))
            for ent in self.setEntities:
                if self.cMatrixUI.GetIsOverlapping(ent.GetShape().c_ptr, cMouseCirc.c_ptr):
                    ent.OnLButtonUp()
                    break
            # Deactivate mouse circ
            cMouseCirc.SetIsActive(False)

        mouseMgr = MouseManager([Button(sdl2.SDL_BUTTON_LEFT, fnDown = fnLBDown, fnUp = fnLBUp)])

        # Construct input manager
        self.mInputManager = InputManager(keyMgr, mouseMgr)

    def HandleEvent(self, sdlEvent):
        if sdlEvent.type == sdl2.events.SDL_QUIT:
            self.cClipLauncher.SetPlayPause(False)
            self.cMatrixUI.SetQuitFlag(True)
        else:
            self.mInputManager.HandleEvent(sdlEvent)

    def StartCell(self, cell):
        self.setOn.add(cell)

    def StopCell(self, cell):
        self.setOff.add(cell)

    def GetCurrentSamplePos(self):
        return self.nCurSamplePos

    def GetCurrentSamplePosInc(self):
        return self.nCurSamplePosInc

    def GetPreTrigger(self):
        return self.nPreTrigger

    def Reset(self):
        # The current sample pos is incremented by
        # the curSamplePos inc, which is a multiple of
        # the loop manager's bufsize (every buf adds to inc)
        self.nCurSamplePos = 0
        self.nCurSamplePosInc = 0
        self.nNumBufsCompleted = 0

        # the preTrigger is the amount of samples
        # we wait to be remaining in the current playing
        # cell before we flush any changes to the CL
        self.nPreTrigger = 3 * self.cClipLauncher.GetBufferSize()

        # Our entities will tell us what to turn on/off,
        # and we clear these sets in Update
        self.setOn = set()
        self.setOff = set()

    # Go through and update drawables,
    # post any messages needed to the clip launcher
    def Update(self):
        # Update ui, clip launcher
        # (clip launcher locks mutex)
        self.cClipLauncher.Update()
        self.cMatrixUI.Update()
        self.cMatrixUI.Draw()

        # if the clip launcher hasn't started yet,
        # maybe start it if some cells wants to play
        if self.cClipLauncher.GetPlayPause() == False:
            # reset sample counters
            self.Reset()

            # Update all rows, determine if any should play
            for row in self.diRows.values():
                row.Update()
                if isinstance(row.GetActiveState(), Row.State.Pending):
                    # This is stupid... but in order to convince the row to start playing,
                    # we set ourselves to be one sample away from the row trigger... dumb
                    # I feel like it's only a matter of time before this screws me over
                    self.nCurSamplePos = row.GetTriggerRes() - self.nPreTrigger - 1
                    self.nCurSamplePosInc = 1
                    row.Update()

            # Reset these two after advancing any pending rows
            self.nCurSamplePos = 0
            self.nCurSamplePosInc = 0

            # If there is anything to turn on
            if len(self.setOn):
                liCmds = []
                # Turn stuff on and start playing
                for c in self.setOn:
                    if c is not None:
                        liCmds.append((clCMD.cmdStartVoice, c.cClip.c_ptr, c.nID, c.fVolume, c.nTriggerRes))
                self.Reset()
                self.cClipLauncher.HandleCommands(liCmds)
                self.cClipLauncher.SetPlayPause(True)

            # Get out
            return

        # Determine how many buffers have advanced, calculate increment
        nCurNumBufs = self.cClipLauncher.GetNumBufsCompleted()
        if nCurNumBufs > self.nNumBufsCompleted:
            nNumBufs = nCurNumBufs - self.nNumBufsCompleted
            self.nCurSamplePosInc += nNumBufs * self.cClipLauncher.GetBufferSize()
            self.nNumBufsCompleted = nCurNumBufs

        # Allow all cells/rows to update themselves given this increment
        for row in self.diRows.values():
            row.Update()

        # Construct commands for any changing voices
        liCmds = []
        for c in self.setOn:
            liCmds.append((clCMD.cmdStartVoice, c.cClip.c_ptr, c.nID, c.fVolume, c.nTriggerRes))
        for c in self.setOff:
            liCmds.append((clCMD.cmdStopVoice, c.cClip.c_ptr, c.nID, c.fVolume, c.nTriggerRes))

        # Post to clip launcher
        if len(liCmds):
            self.cClipLauncher.HandleCommands(liCmds)

        # Clear these sets
        self.setOn = set()
        self.setOff = set()

        # Update sample pos, maybe inc totalLoopCount and reset
        self.nCurSamplePos += self.nCurSamplePosInc
        self.nCurSamplePosInc = 0
        if self.nCurSamplePos >= self.cClipLauncher.GetMaxSampleCount():
            self.nCurSamplePos %= self.cClipLauncher.GetMaxSampleCount()

    def GetCamera(self):
        return Camera.Camera(self.cMatrixUI.GetCameraPtr())

    # To add a row, provide a name, colors, and list of clips
    def AddRow(self, strName, rowData):
        nWindowHeight = self.GetCamera().GetScreenHeight()

        # Determine the y pos of this row
        nRows = len(self.diRows.keys())
        nPosY0 = Constants.nGap + Row.nHeaderH / 2
        nPosY = nPosY0 + nRows * (Row.nHeaderH + Constants.nGap)

        # Construct row and add to dict (Cells constructed by Row)
        r = Row(self, rowData, nPosY)

        # Store row and all its cells in one container
        self.diRows[strName] = r
        self.setEntities.add(r)
        self.setEntities.update(c for c in r.liCells)

        # Get the previous col count and the new one
        nPrevCols = len(self.liCols)
        nNewCols = max(nPrevCols, len(r.liCells))

        # zip by default does shortest
        for col, cell in zip(self.liCols, r.liCells):
            col.AddCell(cell)

        # If there are columns left to add, add them now
        for colIdx in range(nPrevCols, nNewCols):
            if len(r.liCells):
                nPosX = r.liCells[0].GetDrawable().GetPos()[0]
                self.liCols.append(Column(self, nPosX, {r.liCells[colIdx]}))
