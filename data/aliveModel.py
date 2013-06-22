import os
import sys
import math
import random
import traceback
import const
import color
import trace
import story
import rlhelper
from tmxparser import TMXParser
from eventmanager import *


class GameEngine(object):
    """
    Tracks the game state.
    """

    def __init__(self, evManager):
        """
        evManager controls Post()ing and notify()ing events.

        Attributes:

        running (bool):
            True while the engine is online. Changed via QuitEvent().
        state (StateMachine):
            controls the game mode stack.
        level (GameLevel):
            stores level related data.
        story (ConfigObj):
            stores the story.conf data.
        player (MapObject):
            the player controlled map object.
        objects ([MapObject]):
            list of level objects.
        dialogue ([str]):
            List of dialogue strings in queue to display.
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
            self.change_state(event.state)
        elif isinstance(event, PlayerMoveRequestEvent):
            self.move_player(event.direction)
        elif isinstance(event, CombatEvent):
            self.combat_turn(event)
        elif isinstance(event, KillCharacterEvent):
            self.kill_object(event.character)
        elif isinstance(event, CrashEvent):
            self.change_state(STATE_CRASH)
            error_message = str(traceback.format_exc())
            print(error_message)
            trace.log_crash(error_message)

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

    def begin_game(self):
        """
        Begins a new game.
        event.story contains the campaign to play.
        """

        #TODO allow selecting the storyline, pass it in here
        self.settings.storyname = '1-in-the-beginning'
        if self.load_story(self.settings.storyname):
            self.turn = 0
            self.level = None
            self.warp_level()
            self.gamerunning = True
            if self.state.peek() != STATE_PLAY:
                self.change_state(STATE_PLAY)

    def end_game(self):
        """
        Makes the game over.
        """

        while True:
            popped = self.state.pop()
            if not popped or popped == STATE_PLAY:
                break
        self.change_state(STATE_GAMEOVER)
        self.gamerunning = False

    def load_story(self, storyname):
        """
        Loads the story data for the given story as:

            'stories/<storyname>/story.conf'
        """

        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, 'stories', storyname, 'story.conf')
        self.story = story.StoryData(full_path)
        trace.write('loaded story OK')
        return True

    def warp_level(self):
        """
        Proceed to the next level.
        """

        if self.level:
            nextlevel = self.level.number + 1
        else:
            nextlevel = 1

        trace.write('warping to level: %s ' % (nextlevel,))
        self.level = GameLevel(nextlevel, self.story.level_file(nextlevel))
        self.load_matrix()
        self.load_objects()
        self.evManager.Post(NextLevelEvent(None))
        # trigger move events for any viewers to update their views
        self.look_around()
        self.evManager.Post(PlayerMovedEvent())

        # show any level entry messages defined in the story
        entry_message = self.story.entry_message(nextlevel)
        if entry_message:
            self.evManager.Post(MessageEvent(entry_message))

    def load_matrix(self):
        """
        Load the blocking tiles matrix from map data.
        """

        matrix = self.level.matrix['block']
        # for each level cell
        for y in range(0, self.level.tmx.height):
            for x in range(0, self.level.tmx.width):
                # and for every map tile layer
                for layer in self.level.tmx.tilelayers:
                    # this tile blocks movement
                    gid = layer.at((x, y))
                    if self.story.tile_blocks(gid):
                        matrix[x][y] = 1
        # also include all blocking objects
        for objectgroup in self.level.tmx.objectgroups:
            for obj in objectgroup:
                if obj.type != 'player' and self.story.tile_blocks(obj.gid):
                    matrix[obj.x][obj.y] = 1

    def load_objects(self):
        """
        Load map objects and apply any stats defined in the story.conf

        """

        self.player = None
        self.objects = []
        defaults = {'dead': False,
                     'seen': False,
                     'attack': 0,
                     'health': 0,
                     'maxhealth': 0,
                     'healrate': 0,
                     'speed': 0,
                     'stealth': 0,
                     'mana': 0,
                     'maxmana': 5,
                     'manarate': 6,
                     'modes': [],
                     'in_range': False,
                     }

        # for each object group on this level (because maps can be layers)
        for objectgroup in self.level.tmx.objectgroups:

            # for each object in this group
            for obj in objectgroup:

                # apply defaults first
                [setattr(obj, k, v) for k, v in defaults.items()]

                # grab it's name
                oname = obj.name.lower()

                # remember the player object
                if obj.type == 'player':
                    self.player = obj
                    self.player.properties['trail'] = []

                # apply character stats from the story config
                stats = self.story.char_stats(oname)
                if stats:
                    obj.attack = stats.as_int('attack')
                    obj.health = stats.as_int('health')
                    obj.maxhealth = stats.as_int('maxhealth')
                    obj.healrate = stats.as_int('healrate')
                    obj.speed = stats.as_int('speed')
                    obj.stealth = stats.as_int('stealth')
                    obj.mana = stats.as_int('mana')
                    obj.maxmana = stats.as_int('maxmana')
                    obj.manarate = stats.as_int('manarate')
                    obj.modes = stats.as_list('modes')

                # the map object can override our "mode" behaviours.
                # these are stored in the object's "properties" attribute.
                # read any of them out and apply.
                for k, v in obj.properties.items():
                    # only override known values
                    if k in defaults.keys():
                        try:
                            setattr(obj, k, int(v))
                        except ValueError:
                            # that did not work, keep it a string
                            setattr(obj, k, v)
                        # we know that 'modes' is a list
                        if k == 'modes':
                            setattr(obj, k, v.split(','))

                # add this one to the collective
                self.objects.append(obj)

        # show a courtesy message
        if self.player is None:
            trace.error('Warning: No player character on this level. ' +
                        'Good luck!')

    def move_player(self, direction):
        """
        Move the player in direction.
        If the move succeeds, we also take care of updating turn details:
            * look_around() for objects in sight
            * heal_turn() for everyone
            * ai_movement_turn()
        """

        if not self.move_object(self.player, direction):
            return False
        # at this point the player made a successful move.
        # her x-y is up to date with the new position.

        # so let us take care of some turn stuff:
        self.turn += 1
        # update what we can see
        self.look_around()
        # heal turn for player and AI
        self.heal_turn()
        # move turn for AI
        self.ai_movement_turn()
        # update scent trail
        p = self.player.properties
        p['trail'].insert(0, (self.player.x, self.player.y))
        self.player.properties['trail'] = p['trail'][:const.PLAYER_SCENT_LEN]

        # notify the view to update it's visible sprites
        self.evManager.Post(PlayerMovedEvent())

        # notify the view to update it's sprites visibilies
        self.evManager.Post(CharacterMovedEvent(self.player, direction))

    def move_object(self, character, direction):
        """
        Moves the given character by offset direction (x, y).
        Notifies all listeners of this if the move
        is successfull via the CharacterMovedEvent.

        Returns False if the move failed (blocked by tile or combat),
        and True if the move succeeded.

        """

        if not self.gamerunning:
            return False

        newx, newy = (character.x + direction[0],
                      character.y + direction[1])
        colliders = self.get_object_by_xy((newx, newy))

        # only player can activate object triggers
        if character is self.player:
            for collider in colliders:
                self.trigger_object(collider)

        # initiate combat for player and AI
        for collider in colliders:
            if (collider.type in ('ai', 'player') and
                    character.type != 'friend'):
                # but only if one or the other is the player
                if (collider is self.player) or (character is self.player):
                    self.evManager.Post(CombatEvent(character, collider))
                return False
            # collider is blocked
            if self.story.tile_blocks(collider.gid):
                return False

        # tile collisions
        if self.tile_is_solid((newx, newy)):
            return False

        # accept movement
        character.x, character.y = (newx, newy)
        character.px, character.py = (newx * self.level.tmx.tile_width,
                                      newy * self.level.tmx.tile_height)

        # notify the view to update it's sprite positions
        self.evManager.Post(CharacterMovedEvent(character, direction))
        return True

    def tile_is_solid(self, xy):
        """
        Returns if the tile at (x, y) blocks:
        """

        for layer in self.level.tmx.tilelayers:
            gid = layer.at((xy[0], xy[1]))
            if self.story.tile_blocks(gid):
                trace.write('Tile gid %s is solid and blocks us' % gid)
                return True
        # test objects too
        objects = self.get_object_by_xy(xy)
        for obj in objects:
            if self.story.tile_blocks(obj.gid):
                return True

    def ai_movement_turn(self):
        """
        Moves all the ai characters.
        """

        for obj in [e for e in self.objects
                            if e.type in ('ai', 'friend') and
                            not e.dead and
                            (e.speed > 0) and
                            (int(self.turn % e.speed) == 0)]:
            x, y = (0, 0)
            for mode in obj.modes:
                if mode == 'random':
                    if random.randint(0, 1):
                        x = random.randint(-1, 1)
                        y = random.randint(-1, 1)
                if mode == 'updown':
                    if 'movingup' in obj.properties:
                        if self.tile_is_solid((obj.x, obj.y - 1)):
                            del obj.properties['movingup']
                            obj.properties['movingdown'] = True
                        y += -1
                    elif 'movingdown' in obj.properties:
                        if self.tile_is_solid((obj.x, obj.y + 1)):
                            del obj.properties['movingdown']
                            obj.properties['movingup'] = True
                        y += +1
                    else:
                        # start the sequence
                        obj.properties['movingdown'] = True
                if mode == 'leftright':
                    if 'movingleft' in obj.properties:
                        if self.tile_is_solid((obj.x - 1, obj.y)):
                            del obj.properties['movingleft']
                            obj.properties['movingright'] = True
                        x += -1
                    elif 'movingright' in obj.properties:
                        if self.tile_is_solid((obj.x + 1, obj.y)):
                            del obj.properties['movingright']
                            obj.properties['movingleft'] = True
                        x += +1
                    else:
                        # start the sequence
                        obj.properties['movingleft'] = True
                if mode == 'magnet':
                    playerxy = self.player.getxy()
                    objxy = obj.getxy()
                    if self.get_distance(playerxy, objxy) <= 4:
                        x, y = self.get_direction(objxy, playerxy)
                if mode == 'sniffer':
                    #TODO sniffer dog
                    objxy = obj.getxy()
                    trail = self.player.properties['trail']
                    if objxy in trail:
                        idx = trail.index(objxy) - 1
                        if idx >= 0:
                            x, y = self.get_direction(objxy, trail[idx])
            # normalize positions then move
            x = (x < -1) and -1 or x
            x = (x > 1) and 1 or x
            y = (y < -1) and -1 or y
            y = (y > 1) and 1 or y
            self.move_object(obj, (x, y))

    def look_around(self):
        """
        Marks any other objects within the player characters range as seen.
        """

        RANGE = 3
        px, py = (self.player.x, self.player.y)
        # store the level seen matrix
        matrix = self.level.matrix['seen']
        # store the level blocked matrix
        blocked_matrix = self.level.matrix['block']
        # store the map width and height
        w, h = (len(matrix), len(matrix[0]))

        # reset any in-view tiles as "seen"
        for y in range(0, h):
            for x in range(0, w):
                # set to 1 (seen) if it is 2 (in view)
                matrix[x][y] = matrix[x][y] == 2 and 1 or matrix[x][y]
                # same for objects who were in range
                objects = self.get_object_by_xy((x, y))
                for obj in objects:
                    obj.in_range = False

        # we only need to scan for seen tiles and objects in our RANGE vicinity
        # look around the map at what is in view range
        for y in range(py - RANGE, py + RANGE):
            for x in range(px - RANGE, px + RANGE):

                # constrain our view to the level boundaries
                if x < 0 or y < 0 or x > w - 1 or y > h - 1:
                    continue

                # the distance will round our view to a nice ellipse
                dist = self.get_distance((px, py), (x, y))
                if dist <= RANGE:

                    # test if we also have line of sight to this position
                    if (dist <= 1.5 or
                        rlhelper.line_of_sight(blocked_matrix, px, py, x, y)):

                        # mark this matrix tile as in view
                        matrix[x][y] = 2

                        # and any objects too
                        objects = self.get_object_by_xy((x, y))
                        for obj in objects:
                            # mark object is in_range
                            obj.in_range = True
                            obj.seen = True

    def get_distance(self, pointa, pointb):
        """
        Returns the distance between two cartesian points.
        """

        return math.sqrt((pointa[0] - pointb[0]) ** 2 +
                        (pointa[1] - pointb[1]) ** 2)

    def get_direction(self, pointa, pointb):
        """
        Returns the (x, y) offsets required to move pointa towards pointb.
        """

        deltax = pointb[0] - pointa[0]
        deltay = pointb[1] - pointa[1]

        # theta is the angle (in radians) of the direction in which to move
        theta = math.atan2(deltay, deltax)

        # r is the distance to move
        r = 1.0

        deltax = r * math.cos(theta)
        deltay = r * math.sin(theta)

        return (int(round(deltax)), int(round(deltay)))

    def get_object_by_id(self, objectid):
        """
        Get characters object by it's id().
        """

        match = [e for e in self.objects if id(e) == objectid]
        if match:
            return match[0]
        else:
            return None

    def get_object_by_xy(self, xy):
        """
        Get a list of characters at xy.
        """

        return [e for e in self.objects if e.getxy() == xy]

    def heal_turn(self):
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

    def trigger_object(self, obj, isfingered=False):
        """
        Process any triggers on an object.
        Returns True on OK, False if level is changing, abort caller loop.
        """

        trace.write(('trigger %s%s' %
                    (obj.name, (isfingered) and
                    (' via finger') or (''))))

        for action in obj.properties.keys():
            action_value = obj.properties[action]

            # finger somebody else
            if not isfingered and action.startswith('fingers'):
                for fn in [e for e in self.objects if e.name == action_value]:
                    self.trigger_object(fn, isfingered=True)

            # these actions are only triggered by direct interaction
            if not isfingered:
                # next level
                if action == 'exit':
                    self.warp_level()
                    return False
                # show a message
                if action.startswith('message'):
                    self.evManager.Post(MessageEvent(action_value))
                # show a dialog
                if action.startswith('dialogue'):
                    self.show_dialogue(action_value)

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
                            transmute_id = int(list(options[idx:] +
                                options[:idx])[0])
                            trace.write('Rotate tile index %s to %s' %
                                (obj.gid, transmute_id))
                        else:
                            # use first index
                            transmute_id = int(options[0])
                    # do not transmute to a blocking tile if anyone is
                    # standing on the finger target (cant close doors)
                    fingerfriends = self.get_object_by_xy(obj.getxy())
                    for ff in fingerfriends:
                        if (ff is not obj and
                                self.story.tile_blocks(transmute_id)):
                            trace.write('hey, you cant transmorgify a tile ' +
                                'to a solid if someone is standing on it :p')
                            return False
                    # transmorgify!
                    obj.gid = transmute_id
                    # update the level block matrix with our new aquired status
                    matrix = self.level.matrix['block']
                    matrix[obj.x][obj.y] = self.story.tile_blocks(obj.gid)
                    self.evManager.Post(UpdateObjectGID(obj, obj.gid))

            # once shots actions (append once to any action)
            if action.endswith('once'):
                #FIXME fingering an object itself removes this property
                # during the fingered call, causing a keyerror whence
                # returning to here.
                del obj.properties[action]
        # signal caller all is OK
        return True

    def combat_turn(self, event):
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
                    MessageEvent('%s %s for %s' % (a_name, a_verb, a_atk),
                                color.yellow))
        if d_atk:
            a.health -= d_atk
            self.evManager.Post(
                    MessageEvent('%s %s for %s' % (d_name, d_verb, d_atk),
                                color.yellow))
        # death
        if a.health < 1:
            if a is self.player:
                self.end_game()
            else:
                self.evManager.Post(KillCharacterEvent(a))
        if d.health < 1:
            if d is self.player:
                self.end_game()
            else:
                self.evManager.Post(KillCharacterEvent(d))

    def kill_object(self, character):
        """
        Remove a character from play.
        """

        if character in self.objects:
            self.objects.remove(character)

    def change_state(self, state):
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
            self.begin_game()

    def show_dialogue(self, key):
        """
        Update the model state to show a dialogue screen.
        keys is a list of dialogue key names.
        """

        dialogue = self.story.dialogue(key)

        if dialogue:
            # tell everyone about the words about to display
            self.evManager.Post(DialogueEvent(dialogue))
            # change our state to dialogue mode
            self.evManager.Post(StateChangeEvent(STATE_DIALOG))
        else:
            trace.write('dialogue "%s" not found in story definition' % (key))

    @property
    def tile_width(self):
        """
        Quick acccess for the level tmx tile width

        """

        if self.level:
            return self.level.tmx.tile_width

    @property
    def tile_height(self):
        """
        Quick acccess for the level tmx tile height

        """

        if self.level:
            return self.level.tmx.tile_height


class GameLevel(object):
    """
    Contains level specific data.
    Nothing here should persist across levels.
    """

    def __init__(self, number, filename):
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

        # store the level map data in our map matrix.
        self.matrix = {}
        w = self.tmx.width
        h = self.tmx.height
        # store a matrix of tiles that block (for line of sight checks)
        self.matrix['block'] = rlhelper.make_matrix(w, h, 0)
        # and a matrix of tiles seen (it update as the player moves around)
        self.matrix['seen'] = rlhelper.make_matrix(w, h, 0)


# State machine constants for the StateMachine class below
STATE_INTRO = 1
STATE_MENU = 2
STATE_HELP = 3
STATE_ABOUT = 4
STATE_PLAY = 5
STATE_DIALOG = 6
STATE_GAMEOVER = 7
STATE_CRASH = 8


class StateMachine(object):
    """
    Manages a stack based state machine.
    peek(), pop() and push() perform as traditionally expected.
    peeking and popping an empty stack returns None.
    """

    def __init__(self):
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

    def __init__(self):
        """

        """

        self.storyname = None
