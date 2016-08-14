# Used for debugging
# secret@localhost:5678
# import ptvsd
# ptvsd.enable_attach(secret = None)
# ptvsd.wait_for_attach()

import sdl2
import ctypes

import Camera
import Shader
import Drawable
from MatrixUI import MatrixUI
from ClipLauncher import ClipLauncher

from Util import Constants, ctype_from_addr
from GrooveMatrix import Row, Cell, GrooveMatrix

import InputManager

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

    # Declare all clips (clip creation args as tuples)
    nFadeMs = 5
    strClipDir = '../audio/'
    diRowClips = {'Drums' : [('drum1', strClipDir+'drum1.wav', '', nFadeMs)]}

    # Transform each rowname / tup pair into a rowname / cClip pair
    for rowName in diRowClips.keys():
        # Try and get a cClip
        liClips = []
        for tupClip in diRowClips[rowName]:
            # If we can register the clip
            if cClipLauncher.RegisterClip(*tupClip):
                # Get the cClip and store in a list
                liClips.append(cClipLauncher.GetClip(tupClip[0]))
        diRowClips[rowName] = liClips

    # Remove any empty clips
    diRowClips = {k : v for k, v in diRowClips.items() if len(v)}

    # The window width and height are a function of the cells we'll have
    nWindowWidth = Constants.nGap + Row.nHeaderW
    nWindowHeight = Constants.nGap
    for i in range(len(diRowClips.keys())):
        nWindowWidth += Constants.nGap + 2 * Cell.nRadius
        nWindowHeight += Row.nHeaderH + Constants.nGap

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
        raise RuntimeError('Error initializing Scene Display')

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
    clrOff = [.2,.2,.2,1.]
    clrOn = [.6,.6,.6,1.]
    for rowName, liClips in diRowClips.items():
        g_GrooveMatrix.AddRow(rowName, clrOn, clrOff, liClips)

    return True

def HandleEvent(pSdlEvent):
    global g_GrooveMatrix
    sdlEvent = ctype_from_addr(pSdlEvent, sdl2.events.SDL_Event)
    g_GrooveMatrix.HandleEvent(sdlEvent)

import time
def Update():
    global g_GrooveMatrix
    g_GrooveMatrix.cMatrixUI.Update()
    g_GrooveMatrix.cMatrixUI.Draw()
