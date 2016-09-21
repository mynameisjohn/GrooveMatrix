import networkx as nx
import abc
import random
import contextlib

# Generic state class, must have a
# context management function and a name
class State(abc.ABC):
    def __init__(self, name):
        self.name = name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return str(self.name)

    @abc.abstractmethod
    @contextlib.contextmanager
    def Activate(self, SG, prevState):
        yield

# A graph of states, edges denote possible transitions
class StateGraph:
    def __init__(self, graph, fnAdvance, initialState, bPrime, **kwargs):
        if not hasattr(fnAdvance, '__call__'):
            raise ValueError('Error: Invalid advance function for SG!')

        # The graph, the initial state, and the advancement function
        self.G = graph
        self.activeState = initialState
        self._fnAdvance = fnAdvance
        self._mNextStateOverride = None

        # A coroutine that manages active state contexts
        def stateCoro(self):
            prevState = None
            if self.activeState is None:
                nextState = self._fnAdvance(self)
            else:
                nextState = self.activeState

            while True:
                self.activeState = nextState
                with self.activeState.Activate(self, prevState):
                    while nextState is self.activeState:
                        yield self.activeState
                        if self._mNextStateOverride is not None:
                            nextState = self._mNextStateOverride
                            self._mNextStateOverride = None
                        else:
                            nextState = self._fnAdvance(self)
                    if nextState not in self.G.neighbors(self.activeState):
                        raise RuntimeError('Error: Invalid state transition!')
                prevState = self.activeState

        # Declare coro, do not prime (?)
        self._stateCoro = stateCoro(self)
        if bPrime:
            self.AdvanceState()

        # Optional attrdict argument
        if kwargs is not None:
            for k, v in kwargs.items():
                setattr(self, k, v)

    # Returns the current active state
    def GetActiveState(self):
        return self.activeState

    def SetState(self, nextState):
        if nextState not in self.G.neighbors(self.activeState):
            raise RuntimeError('Error: Invalid state transition!')
        self._mNextStateOverride = nextState
        next(self._stateCoro)

    # Returns next state without advancing
    def GetNextState(self):
        return self._fnAdvance(self)

    # Actually advance the state coro
    # return true if state changes
    def AdvanceState(self):
        prevState = self.GetActiveState()
        next(self._stateCoro)
        return prevState is not self.GetActiveState()

    # Just returns states in a container
    def GetAllStates(self):
        return self.G.nodes()
