import os
import sys
from tmxparser import TMXParser
from eventmanager import *

# fixes
# a bug in tiled map editor saves objects y-position with one tile's worth more.
# we offset Y by one tile less as workaround.
# https://github.com/bjorn/tiled/issues/91
FIX_YOFFSET=1

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
        self.playing = False
        self.state = StateMachine()
        self.level = None
        self.story = None
        self.player = None
        self.objects = None

    def notify(self, event):
        """
        Called by an event in the message queue. 
        """

        if isinstance(event, QuitEvent):
            self.running = False
        elif isinstance(event, StateChangeEvent):
            if not self.state.process(event.state):
                self.evManager.Post(QuitEvent())
        elif isinstance(event, PlayerMoveRequestEvent):
            self.movecharacter(self.player, event.direction)
        elif isinstance(event, CombatEvent):
            self.combatcharacters(event)
        elif isinstance(event, KillCharacterEvent):
            self.killcharacter(event.character)
        elif isinstance(event, GameOverEvent):
            self.endgame()
        elif isinstance(event, GameStartEvent):
            self.begingame(event)

    def run(self):
        """
        Starts the game engine loop.

        This pumps a Tick event into the message queue for each loop.
        The loop ends when this object hears a QuitEvent in notify(). 
        """
        
        self.evManager.Post(StateChangeEvent(STATE_MENU))
        #self.evManager.Post(StateChangeEvent(STATE_INTRO))
        # tell all listeners to prepare themselves before we start
        self.evManager.Post(InitializeEvent())
        while self.running:
            newTick = TickEvent()
            self.evManager.Post(newTick)
        
    def begingame(self, event):
        """
        Begins a new game.
        event.story contains the campaign to play.
        """
        
        if self.loadstory(event.story):
            self.level = None
            self.playing = True
            self.levelup()
            # signal to play
            self.evManager.Post(StateChangeEvent(STATE_PLAY))

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
    
    def levelup(self):
        """
        Proceed to the next level.
        """
        
        if self.level:
            nextlevel = self.level.number + 1
        else:
            nextlevel = 1
        trace.write('warping to level: %s ' % (nextlevel,))
        levelfilename = os.path.join(self.story.path, self.story.levels[nextlevel-1])
        self.level = GameLevel(nextlevel, levelfilename)
        self.loadcharacters()
        self.evManager.Post(NextLevelEvent(levelfilename))

    def loadcharacters(self):
        """
        Apply any character stats to the level object list.
        Stats are stored in the current story.
        """
        
        self.player = None
        self.objects = []
        for objectgroup in self.level.tmx.objectgroups:
            for obj in objectgroup:
                self.objects.append(obj)
                objname = obj.name.lower()
                # remember the player object
                if objname == 'player':
                    self.player = obj
                    trace.write('player is at (%s, %s)' % (obj.x, obj.y))
                if objname in self.story.stats.keys():
                    # apply all properties from story to this object
                    [setattr(obj, k, v) 
                        for k, v in self.story.stats[objname].items()
                        ]

    def movecharacter(self, character, direction):
        """
        Moves the given character by offset direction (x, y)
        """
        
        if not self.playing:
            return False
        
        newx, newy = (character.x + direction[0],
                      character.y + direction[1])
        # tile collisions
        for layer in self.level.tmx.tilelayers:
            gid = layer.at((newx, newy - FIX_YOFFSET))
            if gid in self.story.blocklist:
                return False
        
        # other object collision detection
        for obj in self.objects:
            if obj.x == newx and obj.y == newy:
                # AI's always block, in fact, it means combat!
                if obj.type == 'ai':
                    # of course ai don't fight each other.
                    # the code works but in this world they all fight you.
                    if obj is self.player or character is self.player:
                        self.evManager.Post(CombatEvent(character, obj))
                    return False
                elif obj.gid in self.story.blocklist:
                    return False
        
        # accept movement
        character.x, character.y = (newx, newy)
        self.evManager.Post(PlayerMovedEvent(id(character), direction))
    
    def combatcharacters(self, event):
        """
        Begin a combat round.
        """
        
        if not self.playing:
            return False
        
        result = []
        a = event.attacker
        d = event.defender
        # we say 'you' where the player is involved
        a_name = (a is self.player) and ('you') or (a.name)
        d_name = (d is self.player) and ('you') or (d.name)
        # damage control
        a_atk = a.attack
        d_atk = d.attack
        # damage
        if a_atk:
            d.health -= a_atk
            result.append('%s hits %s for %s' % (a_name, d_name, a_atk) )
        if d_atk:
            a.health -= d_atk
            result.append('%s hits %s for %s' % (d_name, a_name, d_atk) )
        # report
        self.evManager.Post(MessageEvent(result))
        # death
        if a.health < 1:
            if a is self.player:
                self.evManager.Post(GameOverEvent())
            else:
                self.evManager.Post(KillCharacterEvent(a))
        if d.health < 1:
            if d is self.player:
                self.evManager.Post(GameOverEvent())
            else:
                self.evManager.Post(KillCharacterEvent(d))

    def killcharacter(self, character):
        """
        Remove a character from play.
        """

        self.objects.remove(character)

    def endgame(self):
        """
        Makes the game over.
        """
        
        self.playing = False
        while True:
            popped = self.state.pop()
            if not popped or popped == STATE_PLAY:
                break
        self.state.push(STATE_GAMEOVER)


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
        data (TMXParser): tmx file data.
        """
        self.number = number
        self.filename = filename
        self.tmx = TMXParser(filename)
        trace.write('loaded tmx data OK')


# State machine constants for the StateMachine class below
STATE_INTRO = 1
STATE_MENU = 2
STATE_HELP = 3
STATE_ABOUT = 4
STATE_PLAY = 5
STATE_DIALOG = 6
STATE_GAMEOVER = 7

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
    
    def process(self, state):
        """
        Process the given state.
        Returns False if the state stack is empty.
        """
        
        if state:
            self.push(state)
        else:
            self.pop()
        return len(self.statestack) > 0
    
    def contains(self, state):
        """
        Returns if a state is in the list.
        """
        
        return state in self.statestack
        
