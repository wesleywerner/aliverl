import pygame
from pygame.locals import *
from pytmx import tmxloader
from eventmanager import *

class GameEngine(object):
    """
    Tracks the game state.
    """

    def __init__(self, evManager):
        """
        evManager controls Post()ing and notify()ing events.
        
        Attributes:
        running (bool): True while the engine is online. Changed via QuitEvent().
        state (StateMachine): controls the game mode stack.
        level (?): 
        """
        
        self.evManager = evManager
        evManager.RegisterListener(self)
        self.running = True
        self.state = StateMachine()
        self.level = None

    def notify(self, event):
        """
        Called by an event in the message queue. 
        """

        if isinstance(event, QuitEvent):
            self.running = False
        elif isinstance(event, StateChangeEvent):
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
        
        # for testing we play immediately. remove this and uncomment below for reality.
        self.evManager.Post(StateChangeEvent(STATE_PLAY))
        # # set up the state machine
        # self.evManager.Post(StateChangeEvent(STATE_MENU))
        # self.evManager.Post(StateChangeEvent(STATE_INTRO))
        # tell all listeners to prepare themselves before we start
        self.evManager.Post(InitializeEvent())
        self.levelup()
        while self.running:
            newTick = TickEvent()
            self.evManager.Post(newTick)
    
    def levelup(self):
        """
        Proceed to the next level.
        """
        
        if self.level:
            nextlevel = self.level.number + 1
        else:
            nextlevel = 1
        trace.write('going to the next level: %s ' % (nextlevel,))
        self.level = GameLevel(nextlevel)
        self.evManager.Post(NextLevelEvent())


class GameLevel(object):
    """
    Contains level specific data. Nothing here should persist across levels.
    """
    
    def __init__ (self, number):
        """
        Attributes:
        
        number (int): the current level number.
        filename (str): relative path to the level file.
        data (pytmx.TiledMap): the .tmx map data.
        """
        self.number = number
        self.objects = []
        self.filename = 'maps/level%s.tmx' % (number,)
        self.data = tmxloader.load_pygame(self.filename, pixelalpha=False)
        trace.write('loaded tmx data OK')
        for obj in self.data.getObjects():
            self.objects.append(LevelObject(obj))
        trace.write('load level objects OK')


class LevelObject(object):
    """
    Represents an interactable, movable level object.
    """
    
    def __init__ (self, baseobject):
        """
        Create this from baseobject.
        Inherits it's base values and save additional attributes in properties.
        """
        
        self.name = None
        self.type = None
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.gid = 0
        self.props = {}
        defaultprops = self.__dict__.keys()
        for p in baseobject.__dict__.keys():
            if p in defaultprops:
                # inherit a base value
                setattr(self, p, baseobject.__dict__[p])
            else:
                # propertize all other values
                self.props[p] = baseobject.__dict__[p]

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
