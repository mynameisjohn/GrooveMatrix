# Used for debugging
# secret@localhost:5678
import ptvsd
ptvsd.enable_attach(secret = None)
#ptvsd.wait_for_attach(30)

import sdl2
import ctypes
from collections import namedtuple

import Camera
import Shader
import Drawable
from MatrixUI import MatrixUI
from ClipLauncher import ClipLauncher, Clip

from Util import Constants, ctype_from_addr
from GrooveMatrix import Row, Cell, GrooveMatrix, Column
import InputManager

import random

# global groove matrix instance
g_GrooveMatrix = None

# Sets up the groove matrix, creates all content
def Initialize(pMatrixUI, pClipLauncher):
    # Create wrapped C++ objects
    cMatrixUI = MatrixUI(pMatrixUI)
    cClipLauncher = ClipLauncher(pClipLauncher)

    # Init audio
    audioSpec = sdl2.SDL_AudioSpec(44100, sdl2.AUDIO_F32, 1, 4096)
    if cClipLauncher.Init(ctypes.addressof(audioSpec)) == False:
        return False

    # Dumb function ot make on off colors
    def makeColor(ix):
        dif=.4
        clrOn = [.5 - dif if i==ix else 0 for i in range(3)]+[1]
        clrOff = [.5 + dif if i==ix else 0 for i in range(3)]+[1]
        return (clrOn, clrOff)

    # Like above but makes a random color
    def makeRndColor():
        clrOn = [0. for i in range(4)]
        for i in range(len(clrOn)):
            clrOn[i] = random.uniform(0.5, 0.9)
        clrOff = [c/2 for c in clrOn]
        return (clrOn, clrOff)

    # Declare all clips (clip creation args as tuples)
    # formatClipTup sets up args for RegisterClip
    def formatClipTup(strName,  nFadeMS = 5):
        strCD = '../sounds/'
        return (strName, strCD+strName+'_Head.wav', strCD+strName+'_Tail.wav', nFadeMS )
    #diRowClips = {  'Drums' :       Row.RowData(liClipData = [formatClipTup('drum1_'), formatClipTup('drum2_')],
    #                                            clrOff = makeColor(0)[0],
    #                                            clrOn = makeColor(0)[1]),
    #                'Bass' :        Row.RowData(liClipData = [formatClipTup('bass1_')],
    #                                            clrOff = makeColor(1)[0],
    #                                            clrOn =  makeColor(1)[1]),
    #                'Sustain' :     Row.RowData(liClipData = [formatClipTup('sus1_')],
    #                                            clrOff =  makeColor(2)[0],
    #                                            clrOn =  makeColor(2)[1])}

    diRowClips = dict()
    for strRow, fVol0 in [('Bass', .5), ('Drums', .5), ('Chords', .5), ('Lead', .4)]:
        clr = makeRndColor()
        diRowClips[strRow] = Row.RowData([formatClipTup(strRow)], clr[0], clr[1], fVol0)
                                          
    #diRowClips = {
    #    'Drums' :   [formatClipTup('drum_gr_'+str(i) for i in range(3)],
    #    'Bass' :    [formatClipTup('bass_gr_1')],
    #    'FastArp' : [formatClipTup('fastarp_'+str(i) for i in range(3)],
    #    'SlowArp' : [formatClipTup('fastarp_'+str(i) for i in range(3)],
    #    'DelayArp' :[formatClipTup('delayarp_'+str(i) for i in range(2))],
    #    'HardArp' : [formatClipTup('hardarp_1')],
    #    'Batman' :  [formatClipTup('batman_1')],
    #    'Air' :     [formatClipTup('air_1')],
    #    'Horu' :    [formatClipTup('horu_1')],
    #    'Nice' :    [formatClipTup('nice_1')],
    #    'Guitar' :  [formatClipTup('guitar_'+str(i) for i in range(6))
    #    formatClipTup('nice_1')],
    #}

    # Transform each rowname / tup pair into a rowname / cClip pair
    for rowName in diRowClips.keys():
        # Try and get a cClip
        liClips = []
        liClipData = diRowClips[rowName].liClipData
        for ix in range(len(liClipData)):
            # If we can register the clip
            tupClip = liClipData[ix]
            if cClipLauncher.RegisterClip(*tupClip):
                liClipData[ix] = Clip(cClipLauncher.GetClip(tupClip[0]))

    # Remove any empty rows
    diRowClips = {k : v for k, v in diRowClips.items() if len(v.liClipData)}

    # The window width and height are a function of the cells we'll have
    nCols = max(len(rd.liClipData) for rd in diRowClips.values())
    nWindowWidth = 2 * Constants.nGap + Row.nHeaderW + nCols * (Constants.nGap + 2 * Cell.nRadius)
    nWindowHeight = 2 * Constants.nGap + Column.nTriDim + len(diRowClips.keys()) * (Row.nHeaderH + Constants.nGap)

    # init the UI display
    if cMatrixUI.InitDisplay('SimpleRB1', [.1,.1,.1,1.],{
        'posX' : sdl2.video.SDL_WINDOWPOS_UNDEFINED,
        'posY' : sdl2.video.SDL_WINDOWPOS_UNDEFINED,
        'width' : nWindowWidth,
        'height' : nWindowHeight,
        'flags' : sdl2.video.SDL_WINDOW_OPENGL | sdl2.video.SDL_WINDOW_SHOWN,
        'glMajor' : 3,
        'glMinor' : 0,
        'doubleBuf' : 1,
        'vsync' : 1
        }) == False:
        raise RuntimeError('Error initializing UI')

    # Set up shader
    cShader = Shader.Shader(cMatrixUI.GetShaderPtr())
    if cShader.Init('../shaders/simple.vert', '../shaders/simple.frag', True) == False:
        raise RuntimeError('Error initializing Shader')

    # Set up camera such that screen/world dims are same, as above
    Camera.SetCamMatHandle(cShader.GetHandle('u_PMV'))
    cCamera = Camera.Camera(cMatrixUI.GetCameraPtr())
    cCamera.InitOrtho(nWindowWidth, nWindowHeight, 0, nWindowWidth, 0, nWindowHeight)

    # Set up static drawable handles
    Drawable.SetPosHandle(cShader.GetHandle('a_Pos'))
    Drawable.SetColorHandle(cShader.GetHandle('u_Color'))

    # Construct Groove Matrix
    global g_GrooveMatrix
    g_GrooveMatrix = GrooveMatrix(pMatrixUI, pClipLauncher)

    # Add rows to groove Matrix
    for rowName, rowData in diRowClips.items():
        g_GrooveMatrix.AddRow(rowName, rowData)

    return True

def HandleEvent(pSdlEvent):
    global g_GrooveMatrix
    sdlEvent = ctype_from_addr(pSdlEvent, sdl2.events.SDL_Event)
    g_GrooveMatrix.HandleEvent(sdlEvent)

def Update():
    global g_GrooveMatrix
    g_GrooveMatrix.Update()
