import pygame
from eventmanager import *

class GameEngine(object):
    """
    Tracks the game state.
    """

    def __init__(self, evManager):
        self.evManager = evManager
        evManager.RegisterListener(self)
        self.running = True
        self.state = StateMachine()

    def notify(self, event):
        """
        Called by an event in the message queue. 
        """

        if isinstance(event, QuitEvent):
            self.running = False
        if isinstance(event, StateChangeEvent):
            if event.state:
                self.state.push(event.state)
            else:
                self.state.pop()
            trace.write('game state is now %s' % (self.state.peek(),))
            # No state, we quit
            if not self.state.peek():
                self.evManager.Post(QuitEvent())

    def run(self):
        """
        Starts the game engine loop.

        This pumps a Tick event into the message queue for each loop.
        The loop ends when this object hears a QuitEvent in notify(). 
        """
        
        # set up the state machine
        self.evManager.Post(StateChangeEvent(STATE_MENU))
        self.evManager.Post(StateChangeEvent(STATE_INTRO))
        # tell all listeners to prepare themselves before we start
        self.evManager.Post(InitializeEvent())
        while self.running:
            newTick = TickEvent()
            self.evManager.Post(newTick)


# State machine constants for the StateMachine class below
STATE_INTRO = 1
STATE_MENU = 2
STATE_HELP = 3
STATE_ABOUT = 4
STATE_PLAY = 5
STATE_DIALOG = 6

class StateMachine(object):
    """
    Manages a stack based state machine.
    peek(), pop() and push() perform as traditionally expected.
    peeking and popping an empty stack returns None.
    """
    
    def __init__ (self):
        self.statestack = []
    
    def peek(self):
        """
        Returns the current state without altering the stack.
        Returns None if the stack is empty.
        """
        try:
            return self.statestack[-1]
        except IndexError:
            # empty stack
            return None
    
    def pop(self):
        """
        Returns the current state and remove it from the stack.
        Returns None if the stack is empty.
        """
        try:
            self.statestack.pop()
        except IndexError:
            # empty stack
            return None
    
    def push(self, state):
        """
        Push a new state onto the stack.
        Returns the pushed value.
        """
        self.statestack.append(state)
        return state
