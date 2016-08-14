# pyl wrapped classes
from MatrixUI import MatrixUI
import ClipLauncher as clCMD
from ClipLauncher import ClipLauncher
import Shape

# All of the UI elements are entities
from Entity import Cell, Row

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

        # No rows yet
        self.diRows = {}
        self.setEntities = set()

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
        if sdlEvent.type == sdl2.events.SDL_QUIT:
            self.cMatrixUI.SetQuitFlag(True)
        else:
            self.mInputManager.HandleEvent(sdlEvent)

    # Go through and update drawables,
    # post any messages needed to the clip launcher
    def Update(self):
        # Update ui, clip launcher
        self.cClipLauncher.Update()
        self.cMatrixUI.Update()
        self.cMatrixUI.Draw()

        # Update all our entities
        for ent in self.setEntities:
            ent.Update()

        # if the clip launcher hasn't started yet,
        # maybe start it if one of our cells wants to play
        if self.cClipLauncher.GetPlayPause() == False:
            setOn = set()
            for row in self.diRows.values():
                if row.ExchangeActiveCell():
                    setOn.add(row.mActiveCell)
            for c in setOn:
                cmd = ()
                self.cClipLauncher.HandleCommand((clCMD.cmdStartVoice, c.cClip.c_ptr, 0, c.fVolume, c.nTriggerRes))
            if len(setOn):
                self.cClipLauncher.SetPlayPause(True)
                return

        # Determine how many buffers have advanced, calculate increment
        # (this involves update the C++ Loop Manager, which locks a mutex)
        nCurNumBufs = self.cClipLauncher.GetNumBufsCompleted()
        if nCurNumBufs > self.nNumBufsCompleted:
            nNumBufs = nCurNumBufs - self.nNumBufsCompleted
            self.nCurSamplePosInc += nNumBufs * self.cClipLauncher.GetBufferSize()
            self.nNumBufsCompleted = nCurNumBufs

        # Compute the new sample pos, zero inc, don't update yet
        nNewSamplePos = self.nCurSamplePos + self.nCurSamplePosInc
        self.nCurSamplePosInc = 0

        # ultimately the end result of this is a set
        # of clips to turn on and a set to turn off
        setOn = set()
        setOff = set()
        for row in self.diRows.values():
            # Store the previous active cell
            curCell = row.mActiveCell
            if curCell is not None:
                nTrigger = curCell.nTriggerRes - self.nPreTrigger
                if self.nCurSamplePos < nTrigger and nNewSamplePos >= nTrigger:
                    # If the active cell is changing
                    if row.ExchangeActiveCell():
                        # If the original wasn't None, turn it off
                        if curCell is not None:
                            print('turning', curCell, 'off')
                            setOff.add(curCell)
                        # Turn on the new cells
                        if row.mActiveCell is not None:
                            setOn.add(row.mActiveCell)
            elif row.ExchangeActiveCell():
                # Turn on the new cells
                setOn.add(row.mActiveCell)

        # Update sample pos, maybe inc totalLoopCount and reset
        self.nCurSamplePos = nNewSamplePos
        if self.nCurSamplePos >= self.cClipLauncher.GetMaxSampleCount():
            self.nCurSamplePos %= self.cClipLauncher.GetMaxSampleCount()

        # Construct the commands
        liCmds = []
        for c in setOn:
            liCmds.append((clCMD.cmdStartVoice, c.cClip.c_ptr, 0, c.fVolume, c.nTriggerRes))
        for c in setOff:
            liCmds.append((clCMD.cmdStopVoice, c.cClip.c_ptr, 0, c.fVolume, c.nTriggerRes))

        # Post to clip launcher
        if len(liCmds):
            self.cClipLauncher.HandleCommands(liCmds)

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
