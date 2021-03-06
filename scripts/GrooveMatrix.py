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

        # detect collision at the point of mouse up, handle it
        def fnLBUp(btn, mouseMgr):
            nonlocal self
            # Get mouse circle collider
            cMouseCirc = Shape.Shape(self.cMatrixUI.GetShape(self.nHitShapeIdx))
            # Convert SDL mouse pos to screen pos
            mX = mouseMgr.mousePos[0]
            mY = cCamera.GetScreenHeight() - mouseMgr.mousePos[1]
            # Move to mouse position and activate
            cMouseCirc.SetCenterPos([mX, mY])
            cMouseCirc.SetIsActive(True)
            # Look for a collision, handle it if so
            for ent in self.setEntities:
                if self.cMatrixUI.GetIsOverlapping(ent.GetShape().c_ptr, cMouseCirc.c_ptr):
                    ent.OnLButtonUp()
                    break
            # Deactivate mouse circ
            cMouseCirc.SetIsActive(False)

        mouseMgr = MouseManager([Button(sdl2.SDL_BUTTON_LEFT, fnUp = fnLBUp)])

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

    def GetClipLauncher(self):
        return self.cClipLauncher

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

    # Update all entities till they don't update no more,
    # raise an error if some sanity limit is reached
    def _SolveStateGraph(self):
        nMaxIters = 15
        for i in range(nMaxIters):
            if all(e.Update() == False for e in self.setEntities):
                break
        else:
            raise RuntimeError('Error: Too many iterations needed to solve state graph!')

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

            # Jostle the graph to let any rows start pending
            self._SolveStateGraph()

            # If any rows have pending cells, set them to playing
            bStartPlaying = False
            for row in self.diRows.values():
                if isinstance(row.GetActiveState(), Row.State.Switching):
                    row.GetPendingCell().SetState(Cell.State.Playing(row.GetPendingCell()))
                    bStartPlaying = True

            # Get out if no rows are pending
            if bStartPlaying == False:
                return

            # After having done that, solve the state graph again to
            # get any cells that should be playing to start playing
            self._SolveStateGraph()

            # As a sanity check, the above should have put something in setOn
            if len(self.setOn) == 0:
                raise RuntimeError('Error: Why weren\'t there any playing cells?')

            # If there is anything to turn on,
            # construct command list
            if len(self.setOn):
                liCmds = []
                for c in self.setOn:
                    liCmds.append((clCMD.cmdStartVoice, c.cClip.c_ptr, c.nID, c.fVolume, c.nTriggerRes))

                # Reset our state and sets, post commands, start playback and get out
                self.Reset()
                self.cClipLauncher.HandleCommands(liCmds)
                self.cClipLauncher.SetPlayPause(True)
                return

        # Determine how many buffers have advanced, calculate increment
        nCurNumBufs = self.cClipLauncher.GetNumBufsCompleted()
        if nCurNumBufs > self.nNumBufsCompleted:
            nNumBufs = nCurNumBufs - self.nNumBufsCompleted
            self.nCurSamplePosInc += nNumBufs * self.cClipLauncher.GetBufferSize()
            self.nNumBufsCompleted = nCurNumBufs

        # Give entity's a chance to transition before applying the increment
        self._SolveStateGraph()

        # Update sample position and the like, zero increment
        self.nCurSamplePos += self.nCurSamplePosInc
        self.nCurSamplePosInc = 0
        if self.nCurSamplePos >= self.cClipLauncher.GetMaxSampleCount():
            self.nCurSamplePos %= self.cClipLauncher.GetMaxSampleCount()

        # Construct commands for any changing voices
        liCmds = []
        for c in self.setOn:
            liCmds.append((clCMD.cmdStartVoice, c.cClip.c_ptr, c.nID, c.fVolume, c.nTriggerRes))
        for c in self.setOff:
            liCmds.append((clCMD.cmdStopVoice, c.cClip.c_ptr, c.nID, c.fVolume, c.nTriggerRes))

        # Clear these sets
        self.setOn = set()
        self.setOff = set()

        # Post to clip launcher
        if len(liCmds):
            self.cClipLauncher.HandleCommands(liCmds)

    # Construct and return C++ camera
    def GetCamera(self):
        return Camera.Camera(self.cMatrixUI.GetCameraPtr())

    # To add a row, provide a name, colors, and list of clips
    def AddRow(self, strName, rowData):
        # Determine the y pos of this row
        nRows = len(self.diRows.keys())
        nPosY0 = Constants.nGap + Row.nHeaderH / 2
        nPosY = nPosY0 + nRows * (Row.nHeaderH + Constants.nGap)

        # Construct row and add to dict (Cells constructed by Row)
        r = Row(self, rowData, nPosY)

        # Store this row keyed by its name
        self.diRows[strName] = r

        # Get the previous col count and the new one
        nPrevCols = len(self.liCols)
        nNewCols = max(nPrevCols, len(r.liCells))

        # zip by default does shortest
        for col, cell in zip(self.liCols, r.liCells):
            col.AddCell(cell)

        # If there are columns left to add, add them now
        for colIdx in range(nPrevCols, nNewCols):
            if len(r.liCells):
                nPosX0 = r.liCells[0].GetDrawable().GetPos()[0]
                nPosX = nPosX0 + len(self.liCols) * (Constants.nGap + Column.nTriDim)
                self.liCols.append(Column(self, nPosX, {r.liCells[colIdx]}))

        # Store all entities together for updating and whatnot
        self.setEntities.add(r)
        self.setEntities.update(c for c in r.liCells)
        self.setEntities.update(c for c in self.liCols)
