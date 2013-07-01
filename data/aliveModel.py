#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see http://www.gnu.org/licenses/.

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
        self.trigger_queue = None

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
        elif isinstance(event, DebugEvent):
            self.debug_action(event)
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
        self.settings.storyname = 'ascension'
        if self.load_story(self.settings.storyname):
            self.turn = 0
            self.level = None
            self.warp_level()
            self.gamerunning = True

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
        self.trigger_queue = []
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

        trace.write('# TURN %s' % self.turn)
        if not self.move_object(self.player, direction):
            pass
            #return False
        # at this point the player made a successful move.
        # her x-y is up to date with the new position.

        # process any triggers in the queue
        self.process_interaction_queue()

        # so let us take care of some turn stuff:
        self.turn += 1
        # heal turn for player and AI
        self.heal_turn()
        # move turn for AI
        self.ai_movement_turn()
        # update what we can see
        self.look_around()
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

        old_x, old_y = (character.x, character.y)
        new_x, new_y = (character.x + direction[0],
                      character.y + direction[1])
        if not self.location_inside_map(new_x, new_y):
            return False
        colliders = self.get_object_by_xy(new_x, new_y)

        # only player can activate object triggers
        if character is self.player:
            for collider in colliders:
                self.trigger_object(collider, True)

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
        if self.tile_is_solid(new_x, new_y):
            return False

        # accept movement
        character.x, character.y = (new_x, new_y)
        character.px, character.py = (new_x * self.level.tmx.tile_width,
                                      new_y * self.level.tmx.tile_height)

        # update the level block matrix with this tile's old and new positions
        if character is not self.player:
            matrix = self.level.matrix['block']
            matrix[old_x][old_y] = 0
            matrix[new_x][new_y] = self.story.tile_blocks(character.gid)

        # notify the view to update it's sprite positions
        self.evManager.Post(CharacterMovedEvent(character, direction))
        return True

    def location_inside_map(self, x, y):
        """
        Tests if the tile position at x, y is inside map coordinates.

        """

        return (x >= 0 and
            y >= 0 and
            x < self.level.tmx.width and
            y < self.level.tmx.height)

    def tile_is_solid(self, x, y):
        """
        Returns if the tile at (x, y) blocks:
        """

        return self.level.matrix['block'][x][y]

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
                        if self.tile_is_solid(obj.x, obj.y - 1):
                            del obj.properties['movingup']
                            obj.properties['movingdown'] = True
                        y += -1
                    elif 'movingdown' in obj.properties:
                        if self.tile_is_solid(obj.x, obj.y + 1):
                            del obj.properties['movingdown']
                            obj.properties['movingup'] = True
                        y += +1
                    else:
                        # start the sequence
                        obj.properties['movingdown'] = True
                if mode == 'leftright':
                    if 'movingleft' in obj.properties:
                        if self.tile_is_solid(obj.x - 1, obj.y):
                            del obj.properties['movingleft']
                            obj.properties['movingright'] = True
                        x += -1
                    elif 'movingright' in obj.properties:
                        if self.tile_is_solid(obj.x + 1, obj.y):
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

        RANGE = 6
        px, py = (self.player.x, self.player.y)
        # store the level seen matrix
        seen_mx = self.level.matrix['seen']
        # store the level blocked matrix
        blocked_mx = self.level.matrix['block']
        # store the map width and height
        w, h = (len(seen_mx), len(seen_mx[0]))

        # reset any in-view tiles as "seen"
        for y in range(0, h):
            for x in range(0, w):
                # set to 1 (seen) if it is 2 (in view)
                seen_mx[x][y] = seen_mx[x][y] == 2 and 1 or seen_mx[x][y]
                # same for objects who were in range
                objects = self.get_object_by_xy(x, y)
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
                        rlhelper.line_of_sight(blocked_mx, px, py, x, y)):

                        # mark this matrix tile as in view
                        seen_mx[x][y] = 2

                        # and any objects too
                        objects = self.get_object_by_xy(x, y)
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

    def get_object_by_xy(self, x, y):
        """
        Get a list of characters at x, y.
        """

        return [e for e in self.objects if e.getxy() == (x, y)]

    def get_object_by_name(self, name):
        """
        Get a list of characters by name.
        """

        return [e for e in self.objects if e.name == name]

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

    def trigger_object(self, obj, direct):
        """
        Push any triggers on an object into the trigger_queue.
        """

        #trace.write(('trigger %s%s' %
                    #(trig['name'], (direct) and (' directly') or (''))))
        trace.write(('trigger "%s"%s' %
                    (obj.name, (direct) and (' directly') or (' indirctly'))))
        for key in obj.properties.keys():
            prop = obj.properties[key]
            #FIX AI use properties to store their movement mode.
            # move this to the object level?
            if type(prop) is str:
                # split the property at word boundaries.
                # all commands start with "@".
                # we only queue interactions if the player interacts with the
                # object directly, unless the @ontrigger command is present.
                # then objects only trigger via another object's @trigger.
                # we also extract the value of @delay=n if present.
                values = prop.split(' ')
                commands = [v for v in values if v.startswith('@')]
                user_data = ' '.join([v for v in values if not v.startswith('@')])
                on_trigger = '@ontrigger' in commands
                delay = [cmd for cmd in commands if cmd.startswith('@delay=')]
                if (direct and not on_trigger) or (not direct and on_trigger):
                    self.trigger_queue.append({
                        'name': key,
                        'obj': obj,
                        'direct': direct,
                        'commands': commands,
                        'delay': delay and int(delay[0].split('=')[1]) or 0,
                        'user_data': user_data,
                        })

    def random_identifier(self, prefix=''):
        """
        Returns a random identifier as a string.
        Used for dynamically adding object properties.
        These do not have to be descriptive for their purpose, just unique.

        """

        return '%s_%x' % (prefix, random.randint(0, 1000))

    def process_interaction_queue(self):
        """
        Process any interaction commands in the queue.
        Each item in the queue is a dictionary of:

            name:   the interaction name on the object (id)
            id:     the id of the object involved
            direct: True if it is a direct interaction like walk-ins,
                    or indirect like a switch.
            params: a list of values specific to each action.

        """

        #trace.write('PROCESSING ' + ','.join([d['name'] for d in self.trigger_queue]))
        requeue = []
        while self.trigger_queue:
            trig = self.trigger_queue.pop()
            name = trig['name']
            direct = trig['direct']
            obj = trig['obj']
            commands = trig['commands']
            user_data = trig['user_data']
            delay = trig['delay']
            if delay > 0:
                trace.write('interaction "%s" delayed %s turn(s)' %
                    (name, delay))
                trig['delay'] = delay - 1
                requeue.append(trig)
            else:
                if '@trigger' in commands and direct:
                    _object_list = self.get_object_by_name(user_data)
                    for _trig_object in _object_list:
                        trace.write('"%s" triggers another object:' %
                            (obj.name))
                        self.trigger_object(_trig_object, False)
                if '@exit' in commands:
                    self.warp_level()
                    return
                if '@message' in commands:
                    self.evManager.Post(MessageEvent(user_data))
                if '@dialogue' in commands:
                    self.show_dialogue(user_data)
                if '@give' in commands:
                    trace.write('giving "%s" interaction "%s"' %
                        (obj.name, name))
                    obj.properties[self.random_identifier(obj.name)] = (
                        user_data.replace('%', '@'))
                if '@transmute' in commands:
                    gid_list = [int(i) for i in user_data.replace(' ','').split(',')]
                    self.transmute_object(obj, gid_list)
                # do we repeat this interaction next time
                if not '@repeat' in commands:
                    trace.write('kill interaction "%s" on "%s"' % (name, obj.name))
                    if obj.properties.has_key(name):
                        del obj.properties[name]
                    else:
                        trace.write(
                            'Property %s on Object %s already deleted.' %
                            (name, obj.name))
        self.trigger_queue = requeue

    def transmute_object(self, obj, gid_list):
        """
        Change the given map Object GID to a new one.
        It will inherit the new animation properties.

        """

        try:
            transmute_id = None
            trace.write('Transmuting %s to gid %s' % (obj.name, gid_list))
            if len(gid_list) == 1:
                # one-way transmutes
                transmute_id = int(gid_list[0])
            else:
                # rotate transmutes
                if obj.gid in gid_list:
                    # rotate the list with the current index as offset.
                    idx = gid_list.index(obj.gid) - 1
                    transmute_id = int(list(
                                        gid_list[idx:] + gid_list[:idx])[0])
                    trace.write('Transmuting %s gid %s -> %s' %
                        (obj.name, obj.gid, transmute_id))
                else:
                    # use first index
                    transmute_id = int(gid_list[0])
            # do not transmute to a blocking tile if anyone is
            # standing on the finger target (cant close doors)
            fingerfriends = self.get_object_by_xy(*obj.getxy())
            for ff in fingerfriends:
                if (ff is not obj and self.story.tile_blocks(transmute_id)):
                    trace.write('hey, you cant transmorgify a tile ' +
                                'to a solid if someone is standing on it :p')
                    return False
            # transmorgify!
            obj.gid = transmute_id
            # update the level block matrix with our new aquired status
            matrix = self.level.matrix['block']
            matrix[obj.x][obj.y] = self.story.tile_blocks(obj.gid)
            self.evManager.Post(UpdateObjectGID(obj, obj.gid))
        except ValueError:
            trace.error('Error converting "%s" to a int while transmuting'
                        ' "%s"' % (str(gid_list), obj.name))

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

    def debug_action(self, event):
        """
        Perform some debugesque action.
        These are considered cheating if you are not debugging ;)

        """

        if event.request_type == 'warp to next level':
            self.warp_level()
        elif event.request_type == 'resurrect player':
            pass
        elif event.request_type == 'clear fog':
            self.level.matrix['seen'] = rlhelper.make_matrix(
                self.level_width, self.level_height, 1)
            for obj in self.objects:
                obj.seen = True
            self.look_around()
            self.evManager.Post(PlayerMovedEvent())

    @property
    def tile_width(self):
        """
        Quick access for the level tmx tile width

        """

        if self.level:
            return self.level.tmx.tile_width

    @property
    def tile_height(self):
        """
        Quick access for the level tmx tile height

        """

        if self.level:
            return self.level.tmx.tile_height

    @property
    def level_width(self):
        """
        Quick access for the level width in tiles.

        """

        return self.level.tmx.width

    @property
    def level_height(self):
        """
        Quick access for the level height in tiles.

        """

        return self.level.tmx.height


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
        # store a matrix of tiles that block (for los and collision tests)
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
