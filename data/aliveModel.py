import os
import sys
import math
import random
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
        player (MapObject): the player controlled map object.
        objects ([MapObject]): list of level objects.
        dialogue ([str]): List of dialogue strings in queue to display.
        """
        
        self.evManager = evManager
        evManager.RegisterListener(self)
        self.running = True
        self.state = StateMachine()
        self.settings = Settings()
        self.gamerunning = False
        self.level = None
        self.story = None
        self.player = None
        self.objects = None
        self.dialogue = []
        self.turn = None

    def notify(self, event):
        """
        Called by an event in the message queue. 
        """

        if isinstance(event, QuitEvent):
            self.running = False
        elif isinstance(event, StateChangeEvent):
            self.changestate(event.state)
        elif isinstance(event, PlayerMoveRequestEvent):
            self.movecharacter(self.player, event.direction)
        elif isinstance(event, CombatEvent):
            self.combatcharacters(event)
        elif isinstance(event, KillCharacterEvent):
            self.killcharacter(event.character)

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
        
    def begingame(self):
        """
        Begins a new game.
        event.story contains the campaign to play.
        """
        
        #TODO allow selecting the storyline, pass it in here
        self.settings.storyname = '1-in-the-beginning'
        if self.loadstory(self.settings.storyname):
            self.turn = 0
            self.level = None
            self.levelup()
            self.gamerunning = True
            if self.state.peek() != STATE_PLAY:
                self.changestate(STATE_PLAY)

    def endgame(self):
        """
        Makes the game over.
        """
        
        while True:
            popped = self.state.pop()
            if not popped or popped == STATE_PLAY:
                break
        self.changestate(STATE_GAMEOVER)
        self.gamerunning = False
    
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
        if len(self.story.entrymessages) <= nextlevel:
            self.evManager.Post(MessageEvent(self.story.entrymessages[nextlevel-1]))

    def loadcharacters(self):
        """
        Apply any character stats to the level object list.
        Stats are stored in the current story.
        """
        
        self.player = None
        self.objects = []
        defaultproperties = {'dead':False, 'seen':False, 'attack':0, 'health':0,
                             'maxhealth':0,'healrate':0, 'speed':0,
                             'stealth':0, 'mana':0, 'maxmana':5, 'manarate': 6,
                             'mode': ''
                             }
        for objectgroup in self.level.tmx.objectgroups:
            for obj in objectgroup:
                # set default properties
                [ setattr(obj, k, v) for k, v in defaultproperties.items() ]
                self.objects.append(obj)
                objname = obj.name.lower()
                # remember the player object
                if obj.type == 'player':
                    self.player = obj
                if objname in self.story.characterstats.keys():
                    # apply all properties from story to this object
                    [setattr(obj, k, v) 
                        for k, v in self.story.characterstats[objname].items()
                        ]
        if self.player is None:
            trace.error('there is no player character set on this map. Good luck!')

    def movecharacter(self, character, direction):
        """
        Moves the given character by offset direction (x, y)
        """
        
        if not self.gamerunning:
            return False

        newx, newy = (character.x + direction[0],
                      character.y + direction[1])
        colliders = self.getcharactersat((newx, newy))

        # turn management
        if character is self.player:
            # increase turn 
            self.turn += 1
            # update what we can see
            self.lookaround()
            # heal turn
            self.healcharacters()
            # ai move turn
            self.movecomputer()
            # player can trigger objects
            for collider in colliders:
                self.processtriggers(collider)

        for collider in colliders:
            # initiate combat
            if collider.type in ('ai', 'player') and character.type != 'friend':
                # but only if one or the other is the player
                if (collider is self.player) or (character is self.player):
                    self.evManager.Post(CombatEvent(character, collider))
                return False
            # collider is in the blocklist
            if collider.gid in self.story.blocklist:
                return False

        # tile collisions
        for layer in self.level.tmx.tilelayers:
            gid = layer.at((newx, newy - FIX_YOFFSET))
            if gid in self.story.blocklist:
                return False

        # accept movement
        character.x, character.y = (newx, newy)
        character.px, character.py = (newx*self.level.tmx.tile_width, 
                                      newy*self.level.tmx.tile_height)

        # notify listeners this character has moved
        self.evManager.Post(CharacterMovedEvent(character, direction))

    def movecomputer(self):
        """
        Moves all the ai characters.
        """
        
        for obj in [e for e in self.objects if e.type in ('ai', 'friend') and not e.dead]:
            #TODO implement intelligent ai movement
            if obj.mode == 'idle':
                return
            if random.randint(0, 1):
                x = random.randint(-1, 1)
                y = random.randint(-1, 1)
                self.movecharacter(obj, (x, y))
    
    def lookaround(self):
        """
        Marks any other objects within the player characters range as seen.
        """
        
        pxy = (self.player.x, self.player.y)
        for obj in self.objects:
            obj.seen = self.distance(pxy, (obj.x, obj.y)) <= 3
    
    def distance(self, pointa, pointb):
        """
        Returns the distance between two cartesian points.
        """
        
        return math.sqrt((pointa[0] - pointb[0])**2 + (pointa[1] - pointb[1])**2)
    
    def getcharacter(self, objectid):
        """
        Get characters object by it's id().
        """
        
        match = [e for e in self.objects if id(e) == objectid]
        if match:
            return match[0]
        else:
            return None
    
    def getcharactersat(self, xy):
        """
        Get a list of characters at xy.
        """
        
        return [e for e in self.objects if e.getxy() == xy]
        
    def healcharacters(self):
        """
        Each turn characters gets a chance to heal.
        """

        for npc in [e for e in self.objects
                            if e.type in ('player', 'ai')
                            and not e.dead]:
            # health
            if npc.health < npc.maxhealth:
                if self.turn % npc.healrate == 0:
                    npc.health += 1
                    trace.write('%s heals to %s hp' % (npc.name, npc.health))
            # mana
            if npc.mana < npc.maxmana:
                if self.turn % npc.manarate == 0:
                    npc.mana += 1
    
    def processtriggers(self, obj, isfingered=False):
        """
        Process any triggers on an object.
        Returns True on OK, False if level is changing, abort caller loop.
        """
        
        trace.write('trigger %s%s' % (obj.name, (isfingered) and (' via finger') or ('')))
        
        for action in obj.properties.keys():
            action_value = obj.properties[action]

            # finger somebody else
            if not isfingered and action.startswith('fingers'):
                for fn in [e for e in self.objects if e.name == action_value]:
                    self.processtriggers(fn, isfingered=True)
            
            # next level
            if action == 'exit':
                self.levelup()
                return False
            # show a message
            if action.startswith('message'):
                self.evManager.Post(MessageEvent(action_value))
            
            # show a dialog
            if action.startswith('dialogue'):
                self.showdialogue(action_value)

            # fingered characters only
            if action.startswith('on finger') and isfingered and \
                              obj is not self.player:
                # grab the finger actions
                f_action = action_value.split('=')
                # give us a new property equal to the rest of f_action
                if f_action[0] == 'give':
                    obj.properties[f_action[1]] = ' '.join(f_action[2:])
                elif f_action[0] == 'transmute':
                    # we can have a one-way or rotate transmutes
                    options = f_action[1].split(',')
                    if len(options) == 1:
                        transmute_id = int(options[0])
                    else:
                        if str(obj.gid) in options:
                            # rotate the list with the current
                            # index as offset. 
                            idx = options.index(str(obj.gid)) - 1
                            transmute_id = int(list(options[idx:] + options[:idx])[0])
                            trace.write('Rotate tile index %s to %s' % (obj.gid, transmute_id))
                        else:
                            # use first index
                            transmute_id = int(options[0])
                    # do not transmute to blocklist gid's if anyone is 
                    # standing on the finger target (cant close doors)
                    fingerfriends = self.getcharactersat(obj.getxy())
                    for ff in fingerfriends:
                        if ff is not obj and transmute_id in self.story.blocklist:
                            trace.write('hey, you cant transmorgify a tile to a solid if someone is standing on it :p')
                            return False
                    # transmorgify!
                    obj.gid = transmute_id
                    self.evManager.Post(UpdateObjectGID(obj, obj.gid))

            # once shots actions (append once to any action)
            if action.endswith('once'):
                del obj.properties[action]
        # signal caller all is OK
        return True
        
    
    def combatcharacters(self, event):
        """
        Begin a combat round.
        """
        
        if not self.gamerunning:
            return False
        a = event.attacker
        d = event.defender
        # we say 'you' where the player is involved
        a_name = (a is self.player) and ('you') or (a.name)
        d_name = (d is self.player) and ('you') or (d.name)
        a_verb = (a is self.player) and ('hit') or ('hits')
        d_verb = (a is self.player) and ('hits') or ('hit')
        # damage control
        a_atk = a.attack
        d_atk = d.attack
        # damage
        if a_atk:
            d.health -= a_atk
            self.evManager.Post(
                    MessageEvent('%s %s for %s' % (a_name, a_verb, a_atk)))
        if d_atk:
            a.health -= d_atk
            self.evManager.Post(
                    MessageEvent('%s %s for %s' % (d_name, d_verb, d_atk)))
        # death
        if a.health < 1:
            if a is self.player:
                self.endgame()
            else:
                self.evManager.Post(KillCharacterEvent(a))
        if d.health < 1:
            if d is self.player:
                self.endgame()
            else:
                self.evManager.Post(KillCharacterEvent(d))

    def killcharacter(self, character):
        """
        Remove a character from play.
        """

        self.objects.remove(character)

    def changestate(self, state):
        """
        Process game state change events.
        """
        
        # popping dialogue removes one line of dialog text
        if not state and \
                        len(self.dialogue) > 0 and \
                        self.state.peek() == STATE_DIALOG:
            self.dialogue.pop()
        # push or pop the given state
        if not self.state.process(state):
            self.evManager.Post(QuitEvent())
        if state == STATE_PLAY and not self.gamerunning:
            # start a new game
            self.begingame()

    def showdialogue(self, key):
        """
        Update the model state to show a dialogue screen.
        keys is a list of dialogue key names.
        """
        
        if key in self.story.dialogue:
            words = self.story.dialogue[key]['words']
            # tell anybody the words that should display
            self.evManager.Post(DialogueEvent(words))
            # match the model state
            self.evManager.Post(StateChangeEvent(STATE_DIALOG))
        else:
            trace.write('dialogue "%s" not found in story definition' % (key))


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
        

class Settings(object):
    """
    Stores persistant settings.
    """

    def __init__ (self):
        """
        
        """

        self.storyname = None
