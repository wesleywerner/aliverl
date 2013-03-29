import os
import sys
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
        level (GameLevel): stores level related data.
        story (object): imports from story.py
        """
        
        self.evManager = evManager
        evManager.RegisterListener(self)
        self.running = True
        self.state = StateMachine()
        self.level = None
        self.story = None

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
        if self.loadstory('1-in-the-beginning'):
            self.levelup()
            while self.running:
                newTick = TickEvent()
                self.evManager.Post(newTick)
    
    def loadstory(self, storyname):
        """
        Loads the story data for the given story name.
        The name is essentially the directory name of the story.
        We expect the story.py file to exist.
        """
        
        # this loads the 'story.py' file from the story directory.
        try:
            storypath = os.path.abspath(os.path.join('stories', storyname))
            sys.path.append(storypath)
            self.story = __import__('story')
            setattr(self.story, 'path', storypath)
            sys.path.remove(storypath)
            trace.write('loaded story OK')
            return True
        except Exception as e:
            trace.error(e)
    
    def applystats(self):
        """
        Apply any story character stats to the level object list.
        """
        # apply story stats to any matching objects
        for obj in self.level.objects:
            # case insensitive match
            if obj.name.lower() in [e.lower() for e in self.story.stats.keys()]:
                # apply all properties from story to this object
                [setattr(obj, k, v) 
                    for k, v 
                    in self.story.stats[obj.name.lower()].items()
                    ]

    def levelup(self):
        """
        Proceed to the next level.
        """
        
        if self.level:
            nextlevel = self.level.number + 1
        else:
            nextlevel = 1
        trace.write('warping to level: %s ' % (nextlevel,))
        self.level = GameLevel(
                nextlevel, 
                os.path.join(self.story.path, self.story.levels[nextlevel-1])
                )
        self.applystats()
        self.evManager.Post(NextLevelEvent())


class GameLevel(object):
    """
    Contains level specific data.
    Nothing here should persist across levels.
    """
    
    def __init__ (self, number, filename):
        """
        Attributes:
        
        number (int): the current level number.
        filename (str): relative path to the level file.
        data (pytmx.TiledMap): the .tmx map data.
        """
        self.number = number
        self.objects = []
        self.filename = filename
        self.data = tmxloader.load_pygame(self.filename, pixelalpha=False)
        self.objects = self.data.getObjects()
        trace.write('loaded tmx data OK')


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
