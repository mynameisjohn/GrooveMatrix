# I'd like to make this agnostic of
# SDL events, but for now this works
import sdl2.events
import abc

# Button class, own an identifier (code)
# and a callback that is called when the
# button is pressed and released
# TODO repeat?
class Button:
    def __init__(self, code, **kwargs):
        # Store code, set state to false
        self.code = code
        self.state = False

        # Try and get fnDown if they provided it
        self.fnDown = None
        if 'fnDown' in kwargs.keys():
            if hasattr(kwargs['fnDown'], '__call__'):
                self.fnDown = kwargs['fnDown']
            else:
                raise ValueError('Error: button down function not callable!')

        # same with fnUp
        self.fnUp = None
        if 'fnUp' in kwargs.keys():
            if hasattr(kwargs['fnUp'], '__call__'):
                self.fnUp = kwargs['fnUp']
            else:
                raise ValueError('Error: button up function not callable!')

        # Is this necessary?
        if self.fnDown is None and self.fnUp is None:
            raise ValueError('Error: no button functions provided!')

    # This isn't really helpful, but why not?
    def __hash__(self):
        return hash(self.code)

    # Gets called when the button is pressed
    def Toggle(self, mgr):
        # Update toggle state
        oldState = self.state
        self.state = not(self.state)
        # depending on new state, do fnUp or fnDown
        fnToggle = self.fnDown if self.state else self.fnUp
        if fnToggle is not None:
            fnToggle(self, mgr)

class ButtonManager:
    def __init__(self, liButtons):
        if not(all(isinstance(k, Button) for k in liButtons)):
            raise TypeError('Error: All keys registered must be Buttons')

        self.diButtons = {b.code : b for b in liButtons}
        self.setSDLEventsHandled = set()

    def GetButton(self, btnCode):
        if btnCode in self.diButtons.keys():
            if isinstance(self.diButtons[btnCode], Button):
                return self.diButtons[btnCode]
        return None

    def IsButtonPressed(self, btnCode):
        if btnCode in self.diButtons.keys():
            if isinstance(self.diButtons[btnCode], Button):
                return self.diButtons[btnCode].state
            else:
                return bool(self.diButtons[btnCode])
        return False

    @abc.abstractmethod
    def HandleEvent(self, sdlEvent):
        return sdlEvent.type in self.setSDLEventsHandled

class KeyboardManager(ButtonManager):
    def __init__(self, liKeys):
        ButtonManager.__init__(self, liKeys)
        self.setSDLEventsHandled = {sdl2.events.SDL_KEYDOWN, sdl2.events.SDL_KEYUP}

    # Handle an SDL2 key event
    def HandleEvent(self, sdlEvent):
        # check set
        if not(ButtonManager.HandleEvent(self, sdlEvent)):
            return False
        # unpack the key event
        keyEvent = sdlEvent.key
        # Get the keycode
        keyCode = keyEvent.keysym.sym
        # I only care about non-repeated for now
        if keyEvent.repeat == False:
            # If we have this in our dict
            if keyCode in self.diButtons.keys():
                # If it's a registered button
                if isinstance(self.diButtons[keyCode], Button):
                    # Delegate to the button
                    self.diButtons[keyCode].Toggle(self)
                # Otherwise it should be a bool, so flip it
                else:
                    self.diButtons[keyCode] = not(self.diButtons[keyCode])
            # If it's new and it's a keydown event, add a bool to the dict
            elif keyEvent.type == sdl2.events.SDL_KEYDOWN:
                self.diButtons[keyCode] = True

        return True

# Mouse manager, handles motion and lb/rb buttons
class MouseManager(ButtonManager):
    def __init__(self, liButtons, **kwargs):
        ButtonManager.__init__(self, liButtons)
        self.setSDLEventsHandled = {sdl2.events.SDL_MOUSEBUTTONUP, sdl2.events.SDL_MOUSEBUTTONDOWN,
                                    sdl2.events.SDL_MOUSEWHEEL, sdl2.events.SDL_MOUSEMOTION}

        # initial mouse pos
        self.mousePos = [0, 0]

        # Better be a function if provided
        if 'fnMotion' in kwargs.keys():
            fnMotion = kwargs['fnMotion']
            if hasattr(fnMotion, '__call__'):
                self.fnMotion = fnMotion
        else:
            self.fnMotion = None
        if 'fnWheel' in kwargs.keys():
            fnWheel = kwargs['fnWheel']
            if hasattr(fnWheel, '__call__'):
                self.fnWheel = fnWheel
        else:
            self.fnWheel = None

    # Handle sdl2 mouse and motion events
    def HandleEvent(self, sdlEvent):
        if not(ButtonManager.HandleEvent(self, sdlEvent)):
            return False

        # buttons
        if (sdlEvent.type == sdl2.events.SDL_MOUSEBUTTONUP or sdlEvent.type == sdl2.events.SDL_MOUSEBUTTONDOWN):
            btn = sdlEvent.button.button
            if btn in self.diButtons.keys():
                self.diButtons[btn].Toggle(self)
        # motion
        elif sdlEvent.type == sdl2.events.SDL_MOUSEMOTION:
            m = sdlEvent.motion
            self.mousePos = [m.x, m.y]
            if self.fnMotion is not None:
                self.fnMotion(self)
        # wheel
        elif sdlEvent.type == sdl2.events.SDL_MOUSEWHEEL:
            if self.fnWheel is not None:
                self.fnWheel(self, sdlEvent.wheel)

        return True

# Input manager, owns a mouse and keyboard handler
# as well as reference to C++ scene class (needed?)
class InputManager:
    def __init__(self, keyMgr, mouseMgr):
        self.keyMgr = keyMgr
        self.mouseMgr = mouseMgr

    # Handle some sdl2 event
    def HandleEvent(self, sdlEvent):
        # Give key events to the keyboard manager
        if self.keyMgr is not None:
            self.keyMgr.HandleEvent(sdlEvent)

        # And mouse events to the mouse manager (will get motion and button)
        if self.mouseMgr is not None:
            self.mouseMgr.HandleEvent(sdlEvent)
