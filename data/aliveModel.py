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
import re
import sys
import math
import copy
import random
import pickle
import traceback
import datetime
from const import *
import color
import trace
import story
import rlhelper
import aliveUpgrades as alu
from tmxparser import TMXParser
from configobj4 import ConfigObj
from eventmanager import *

VERSION = 0.1

# version history tracker
# 0.1 - 2013-08-21

class GameEngine(object):
    """
    The game engine handles all character interactions and data.
    This includes movement, combat, object interactions, levels
    and snargle spam.

    The evManager handles posting events to other listeners, how
    we notify the other parts of the game when things happen.

    Attributes:

    engine_pumping (bool)
        True while the engine is pumping out TickEvents to all
        listeners. Gets changed if we see a notify() QuitEvent.

    state (StateMachine)
        Stores the current game state, like which menu we are in,
        if we are busy playing, or viewing word dialogues,
        or the info screens.

    event_queue (dict)
        A queue of delayed events to post at a later time.
        The value is the seconds to delay before posting.

    settings (Settings)
        An instance of Settings class.

    game_in_progress (bool)
        True if there is a game in progress. This mainly escapes
        game-only calls to ensure the user can't do much if there
        is no game in progress.

    level (GameLevel)
        Stores level related data.

    story (ConfigObj)
        An instance of story.py, which contains the current story data.

    player (MapObject)
        The current player object used for moving or or actions.
        This may get swapped out (like via the Exploit upgrade)
        allowing us to control other characters.

    upgrades_available (int)
        The number of upgrades the player can still install.

    objects ([MapObject])
        The list of level objects the player can interact with.
        This includes the player itself, other AI, terminals and doors.

    level_number (int)
        The current level the player is on

    turn (int)
        A counter of the current turn number.

    trigger_queue []
        Interacting with objects will place map-defined triggers in
        this queue. Some get processed out again on that same turn,
        while others have a @delay which keep them in this queue
        until a later time.

    store (dict)
        Temporary storage for transient player states.

    can_warp (bool)
        True if a level is done and the player can warp to the next level.

    recent_messages (list)
        A list of game messages.

    game_slot (int)
        The slot number for loading or saving the current game to.

    story_name (string)
        The name of the story currently played. This value determines the path
        to the story config files and map data.

    """

    def __init__(self, evManager):
        """
        Create a new instance of the game engine, giving the event manager
        object to use for posting and receive events.

        """

        self.evManager = evManager
        evManager.RegisterListener(self)
        self.engine_pumping = True
        self.state = StateMachine()
        self.event_queue = {}
        self.settings = Settings()
        self.game_in_progress = False
        self.level = None
        self.level_number = 0
        self.story = None
        self.player = None
        self.upgrades_available = 0
        self.objects = None
        self.turn = None
        self.trigger_queue = None
        self.target_object = None
        self.store = None
        self.can_warp = False
        self.recent_messages = []
        self.game_slot = 0
        self.story_name = 'ascension'

    def notify(self, event):
        """
        Called by an event in the message queue.
        """

        if isinstance(event, QuitEvent):
            self.engine_pumping = False
            self.save_game()

        elif isinstance(event, StateChangeEvent):
            self.change_state(event.state)

        elif isinstance(event, StateSwapEvent):
            self.state.swap(event.state)

        elif isinstance(event, PlayerMoveRequestEvent):
            self.last_direction = event.direction
            self.move_player(event.direction)

        elif isinstance(event, CombatEvent):
            self.combat_turn(event.attacker, event.defender)

        elif isinstance(event, KillCharacterEvent):
            if event.character in self.objects:
                self.objects.remove(event.character)
                self.update_block_matrix(
                    event.character.x, event.character.y, 0)

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

        self.post(InitializeEvent())
        self.post(StateChangeEvent(STATE_MENU_MAIN))
        #self.post(StateChangeEvent(STATE_INTRO))
        # tell all listeners to prepare themselves before we start
        while self.engine_pumping:
            newTick = TickEvent()
            self.evManager.Post(newTick)

            # process any delayed events
            for event, delay in self.event_queue.items():
                delay -= 1
                if delay < 1:
                    del self.event_queue[event]
                    self.post(event)
                else:
                    self.event_queue[event] = delay

    def begin_game(self):
        """
        Begins a new game.
        event.story contains the campaign to play.
        """

        self.turn = 0
        self.level = None
        self.level_number = 0
        self.recent_messages = []
        # load any saved game over these defaults
        self.load_game()
        if self.load_story(self.story_name):
            self.can_warp = True
            self.warp_level()
            self.game_in_progress = True

    def end_game(self):
        """
        Ends the current game by popping all states up to include STATE_PLAY
        and setting game in progress flags.

        """

        while True:
            popped = self.state.pop()
            if not popped or popped == STATE_PLAY:
                break
        self.game_in_progress = False

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

    def restart_level(self):
        """
        Restarts the current level. The player state will revert to when they
        first entered the level.

        """

        self.player = copy.deepcopy(self.store['player copy'])
        self.warp_level(restart=True)

    def warp_level(self, restart=False):
        """
        Proceed to the next level.
        """

        if not restart and not self.can_warp:
            return
        if not restart:
            self.level_number += 1

        trace.write('warping to level: %s ' % self.level_number)
        level_filename = self.story.level_file(self.level_number)
        if not level_filename or not os.path.exists(level_filename):
            trace.write('Warning! There is no map for level %s. '
                        'I guess I am stuck here.' % self.level_number)
            return False
        self.can_warp = False
        self.store = {}
        self.trigger_queue = []
        self.event_queue = {}
        self.level = GameLevel(level_filename)
        self.load_objects()
        self.load_matrix()
        self.look_around()

        # ensure the player health history has some data
        if len(self.player.health_history) < 10:
            self.player.health_history = [self.player.health] * 10
        if len(self.player.power_history) < 10:
            self.player.power_history = [self.player.power] * 10
        if self.state.peek() != STATE_PLAY:
            self.evManager.Post(StateChangeEvent(STATE_PLAY))
        self.post(NextLevelEvent(None))

        # trigger move events for any viewers to update their views
        self.post(PlayerMovedEvent())

        # refresh any listeners before we post entry messages
        self.post(TickEvent())

        # show the level title if there is one
        level_title = self.story.level_title(self.level_number)
        if level_title:
            self.post_msg('[%s]' % level_title)

        # show a level entry message
        entry_message = self.story.entry_message(self.level_number)
        if entry_message:
            self.post_msg(entry_message)

        # show a level entry dialogue
        entry_dialogue = self.story.entry_dialogue(self.level_number)
        if entry_dialogue:
            self.show_dialogue(entry_dialogue)

        # apply any special upgrades
        regen = alu.from_list(self.player.upgrades, alu.REGEN)
        if regen:
            regen.apply_upgrade(self.player)

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

        self.objects = []
        defaults = {'dead': False,
                     'seen': False,
                     'attack': 0,
                     'health': 0,
                     'max_health': 0,
                     'heal_rate': 0,
                     'speed': 0,
                     'stealth': 0,
                     'power': 0,
                     'max_power': 5,
                     'power_restore_rate': 6,
                     'modes': None,
                     'view_range': 3,
                     'in_range': False,
                     'trail': None,
                     'upgrades': None,
                     'freeze_duration': 0,
                     'confused_duration': 0,
                     'last_direction': None,
                     }

        # for each object group on this level (because maps can be layers)
        for objectgroup in self.level.tmx.objectgroups:

            # for each object in this group
            for obj in objectgroup:

                # apply defaults first
                [setattr(obj, k, v) for k, v in defaults.items()]

                # make values case incensitive
                obj.name = obj.name.lower()
                obj.type = obj.type.lower()
                #NOTE:  found that using setattr with lists uses shallow copy
                #       and thus lists share the same memory == panic
                obj.upgrades = []
                obj.trail = []
                obj.modes = []
                obj.health_history = []
                obj.power_history = []

                # apply character stats from the story config
                stats = self.story.char_stats(obj.name)
                if stats:
                    trace.write('applying conf stats for %s' % (obj.name,))
                    obj.attack = stats.as_float('attack')
                    obj.health = stats.as_float('health')
                    obj.max_health = stats.as_float('max_health')
                    obj.heal_rate = stats.as_float('heal_rate')
                    obj.speed = stats.as_float('speed')
                    obj.stealth = stats.as_float('stealth')
                    obj.power = stats.as_float('power')
                    obj.max_power = stats.as_float('max_power')
                    obj.power_restore_rate = (
                        stats.as_float('power_restore_rate'))
                    obj.modes = stats.as_list('modes')

                # carry the player object across levels
                if obj.type == 'player':
                    if self.player is None:
                        self.player = obj
                    else:
                        self.player.x, self.player.y = obj.getxy()
                        self.player.px, self.player.py = obj.getpixelxy()
                        obj = self.player
                    # keep a copy of player for redoing a level after death
                    self.store['player copy'] = copy.deepcopy(self.player)

                # the map object can override our "mode" behaviours.
                # these are stored in the object's "properties" attribute.
                # read any of them out and apply.
                for k, v in obj.properties.items():
                    # only override known values
                    if k in defaults.keys():
                        try:
                            setattr(obj, k, float(v))
                        except ValueError:
                            # that did not work, keep it a string
                            setattr(obj, k, v)
                        # we know that 'modes' is a list
                        if k == 'modes':
                            setattr(obj, k, v.replace(' ', '').split(','))

                # add this one to the collective
                self.objects.append(obj)

        # show a courtesy message
        if self.player is None:
            trace.error('Warning: No player character on this level. ' +
                        'Good luck!')

    def move_player(self, direction):
        """
        Move the player in a direction. This also makes everybody else (AI)
        have a turn.

        """

        trace.write('TURN %s' % self.turn)
        if self.player.dead:
            return
        self.move_character(self.player, direction)

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
        # re-look at our target object
        self.look_at_target()
        # step any upgrades we may have
        for u in self.player.upgrades:
            result = u.step()
            if result:
                self.post_msg(result, color.upgrade_tip)

        # process the exploit ability.
        # if there is a stored player with an exploit upgrade that
        # is not active anymore, swap us back.
        stored_player = self.store.get('stored player', None)
        if stored_player:
            exploiting = alu.from_list(self.player.upgrades, alu.EXPLOIT)
            if exploiting and not exploiting.is_active:
                # swap the player back to her own form
                self.player.upgrades.remove(exploiting)
                self.player = stored_player
                del self.store['stored player']
                self.post_msg('you return...', color.combat_message)
                self.look_around()
                self.look_at_target()
                self.post(RefreshUpgradesEvent())

        # track player health history
        self.player.health_history.append(self.player.health)
        if len(self.player.health_history) > 10:
            self.player.health_history = self.player.health_history[-10:]
        self.player.power_history.append(self.player.power)
        if len(self.player.power_history) > 10:
            self.player.power_history = self.player.power_history[-10:]

        # notify the view to update it's visible sprites
        self.post(PlayerMovedEvent())

    def move_character(self, character, direction):
        """
        Moves the given character by offset direction (x, y).

        """

        # store this direction, carefully not overriding with empty values.
        if direction != (0, 0):
            character.last_direction = direction

        self.move_character_to(
            character,
            character.x + direction[0],
            character.y + direction[1]
            )

    def move_character_to(self, character, x, y):
        """
        Moves a character to (x, y).
        Notifies all listeners of this if the move is successfull
        via the CharacterMovedEvent.

        """

        if not self.game_in_progress:
            return False

        # unfreeze a little.
        if character.freeze_duration > 0:
            character.freeze_duration -= 1
            trace.write('%s is frozen for %s turns' %
                (character.name, character.freeze_duration))
            # a small chance that a code freeze is deadly
            if random.randint(1, 100) < 10:
                self.kill_character(character)
            return False

        # reduce any confusion. note its effect is handled in ai_movement_turn.
        if character.confused_duration > 0:
            character.confused_duration -= 1
            trace.write('%s is confused for %s turns' %
                (character.name, character.confused_duration))

        # boundary check
        if not self.location_inside_map(x, y):
            return False

        # no point in colliding with oneself
        if character.getxy() == (x, y):
            colliders = []
        else:
            colliders = self.get_object_by_xy(x, y)

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
                    self.post(CombatEvent(character, collider))
                return False
            # collider is blocked
            if self.story.tile_blocks(collider.gid):
                return False

        # tile collisions
        if self.tile_is_solid(x, y):
            return False

        # clear the block matrix of this position
        self.update_block_matrix(character.x, character.y, 0)

        # accept movement
        character.x, character.y = (x, y)
        character.px, character.py = (x * self.level.tmx.tile_width,
                                      y * self.level.tmx.tile_height)

        # set the block matrix with the new position
        tile_blocks = self.story.tile_blocks(character.gid)
        self.update_block_matrix(x, y, tile_blocks)

        # update scent trail
        character.trail.insert(0, (character.x, character.y))
        character.trail = character.trail[:PLAYER_SCENT_LEN]

        # notify the view to update it's sprite positions
        self.post(CharacterMovedEvent(character))
        return True

    def update_block_matrix(self, x, y, value):
        """
        Update the level block matrix at the given position.

        """

        if value:
            self.level.matrix['block'][x][y] = int(value)
        else:
            self.level.matrix['block'][x][y] = 0

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
                            (int(self.turn % e.speed) == 0) and
                            e is not self.player]:
            # NOTE: x,y is misleading - its the direction, not absolute points.
            x, y = (0, 0)
            for mode in obj.modes:
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
                    dist = rlhelper.distance(
                        self.player.x, self.player.y, obj.x, obj.y)
                    if dist <= 4:
                        x, y = rlhelper.direction(
                            obj.x, obj.y, self.player.x, self.player.y)
                if mode == 'sniffer':
                    trail = self.player.trail
                    objxy = obj.getxy()
                    if objxy in trail:
                        idx = trail.index(objxy) - 1
                        if idx >= 0:
                            x, y = rlhelper.direction(
                                obj.x, obj.y, *trail[idx])
                if mode == 'random' or obj.confused_duration > 0:
                    if random.randint(0, 1):
                        x = random.randint(-1, 1)
                        y = random.randint(-1, 1)
            # normalize positions then move
            x = (x < -1) and -1 or x
            x = (x > 1) and 1 or x
            y = (y < -1) and -1 or y
            y = (y > 1) and 1 or y
            self.move_character(obj, (x, y))

    def look_at_target(self):
        """
        Look if the current target is still in view and alive.

        """

        if self.target_object:
            if not self.target_object.in_range or self.target_object.dead:
                self.target_object = None

    def look_around(self):
        """
        Marks any other objects within the player characters range as seen.
        """

        RANGE = int(round(self.player.view_range))
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
                # FIXME optimize by just iterating over the whole list once?
                #       consider this call does that now for each x, y :p
                objects = self.get_object_by_xy(x, y)
                for obj in objects:
                    obj.in_range = False

        ## DEBUG printout the blocked matrix
        #for v in range(0, h):
            #for u in range(0, w):
                #print(blocked_mx[u][v]),
            #print()

        for x, y in rlhelper.cover_area(px, py,
                                        self.player.view_range, w - 1, h - 1):

            # test if we also have line of sight to this position
            # FIXME the get line segments gives an inconsistent effect:
            #       positions to our left use points asymetrical to the right
            #       resulting in the block matrix checking cells with twisted
            #       positions. bottom-right corners appear out of sight
            #       when the top-left counterparts are in view.
            #       This can be seen by uncommenting the DEBUG print loop
            #       above and comparing the top and bottom line segments
            #       that are checked against the blocked matrix.
            #       -- see print in line_of_sight() too.
            if (rlhelper.line_of_sight(blocked_mx, px, py, x, y)):

                # mark this matrix tile as in view
                seen_mx[x][y] = 2

                # and any objects too
                objects = self.get_object_by_xy(x, y)
                for obj in objects:
                    # mark object is in_range
                    obj.in_range = True
                    obj.seen = True

    def seen_tile(self, x, y):
        """
        Returns if the tile at x, y has been seen by the player.

        """

        seen_mx = self.level.matrix['seen']
        if x < len(seen_mx) and y < len(seen_mx[0]):
            return seen_mx[x][y]

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

        return [o for o in self.objects
            if x >= o.x and
            y >= o.y and
            x < o.x + o.width and
            y < o.y + o.height
            ]

    def get_object_by_name(self, name):
        """
        Get a list of characters by name.
        """

        return [e for e in self.objects if e.name == name]

    def get_objects_in_reach(self, x, y, reach, type_filter=['ai']):
        """
        Gets a list of objects in reach of position x, y.

        """

        # fix: account for reaching to diagonals:
        reach += 0.5
        the_list = []
        w, h = self.level.tmx.width, self.level.tmx.height
        [the_list.extend(self.get_object_by_xy(u, v))
            for u, v in rlhelper.cover_area(x, y, reach, w, h)
            ]
        return [o for o in the_list if o.type in type_filter]

    def heal_turn(self):
        """
        Each turn characters gets a chance to heal.
        """

        for npc in [e for e in self.objects
                            if e.type in ('player', 'ai', 'friend')
                            and not e.dead]:
            # health
            if npc.health < npc.max_health:
                if (npc.heal_rate > 0):
                    self.adjust_character_health(npc, npc.heal_rate)
                    trace.write('%s heals to %s hp' %
                        (npc.name, npc.health))
            # mana
            if npc.power < npc.max_power:
                if npc.power_restore_rate > 0:
                    npc.power = rlhelper.clamp(
                        npc.power + npc.power_restore_rate, 0, npc.max_power)
                    trace.write('%s heals power to %s hp' %
                        (npc.name, npc.power))

    def split_value_pairs(self, string_value):
        """
        Split a @key=@value pair and return as a list.
        If the value is wrapped in quotes those will be stripped.

        """

        values = string_value.split('=')
        return [e.strip('"') for e in values]

    def split_command(self, command_list, find_command, default=None):
        """
        Find and split the given command from a list.
        The command is expected in the format @name=value.
        Returns a tuple of the command values, or default if the command
        is not found in the list.

        """

        matches = [cmd for cmd in command_list if cmd.startswith(find_command)]
        if matches:
            # remember: the first value is our command itself
            values = self.split_value_pairs(matches[0])
            if len(values) == 2:
                # return the only value not as a list
                return values[1]
            else:
                # return values minus the command
                return values[1:]
        else:
            return default

    def trigger_object(self, obj, direct):
        """
        Push any triggers from an object into the trigger_queue.

        """

        trace.write(('interact with "%s"%s' %
                    (obj.name, (direct) and (' directly') or (' indirctly'))))
        for key in obj.properties.keys():
            prop = obj.properties[key]
            if type(prop) is str:
                # split the property at word boundaries.
                # all commands start with "@".
                # we only queue interactions if the player interacts with the
                # object directly, unless the @ontrigger command is present.
                # then objects only trigger via another object's @trigger.
                # we also extract the value of @delay=n if present.
                values = prop.split(' ')
                commands = [v for v in values if v.startswith('@')]
                user_data = ' '.join([v for v in values
                    if not v.startswith('@')])
                on_trigger = '@ontrigger' in commands
                has_counter = '@addcounter' in commands
                #delay = [cmd for cmd in commands if cmd.startswith('@delay=')]
                if (direct and not on_trigger) or (not direct and on_trigger):
                    delay = self.split_command(commands, '@delay', 0)
                    command_data = {
                        'name': key,
                        'obj': obj,
                        'direct': direct,
                        'commands': commands,
                        'delay': delay and int(delay) or 0,
                        'user_data': user_data,
                        }
                    # we order commands with @addcounter first to let
                    # other @ifcounter tests get fresh counter values.
                    # the list processes from bottom out.
                    if has_counter:
                        self.trigger_queue.append(command_data)
                    else:
                        self.trigger_queue.insert(0, command_data)
                    trace.write('\t"%s" added to trigger queue' % key)

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

        requeue = []
        while self.trigger_queue:
            trig = self.trigger_queue.pop()
            name = trig['name']
            trace.write('processing the "%s" trigger' % name)
            direct = trig['direct']
            obj = trig['obj']
            commands = trig['commands']
            user_data = trig['user_data']
            delay = trig['delay']
            if delay > 0:
                trace.write('\t"%s" trigger delayed %s turn(s)' %
                    (name, delay))
                trig['delay'] = delay - 1
                requeue.append(trig)
            else:
                # conditional: if the object counter matches this test allow
                #       the other commands to process. Otherwise delay them.
                ifcounter = self.split_command(commands, '@ifcounter', None)
                counter_value = obj.properties.get('counter', 0)
                if ifcounter and int(ifcounter) != int(counter_value):
                    trace.write('\tcounter "%s" on "%s" != expected "%s"' %
                        (counter_value, obj.name, ifcounter))
                    continue
                    # NOTE: side effects from continue?
                if '@trigger' in commands and direct:
                    _object_list = self.get_object_by_name(user_data)
                    for _trig_object in _object_list:
                        trace.write('\t"%s" triggers "%s"' %
                            (obj.name, _trig_object.name))
                        self.trigger_object(_trig_object, False)
                if '@exit' in commands:
                    #self.warp_level()
                    trace.write('\tplayer can now warp to the next level')
                    self.can_warp = True
                    self.post_msg('press > to warp to the next level',
                        color.message)
                if '@message' in commands:
                    self.post_msg(user_data)
                if '@upgrade' in commands:
                    trace.write('giving player an upgrade token')
                    self.allow_upgrade()
                if '@dialogue' in commands:
                    self.show_dialogue(user_data)
                if '@give' in commands:
                    rnd_name = self.random_identifier(obj.name)
                    give_data = user_data.replace('%', '@')
                    trace.write('\tgiving "%s" interaction "%s" -> "%s"' %
                        (obj.name, rnd_name, give_data))
                    obj.properties[rnd_name] = (give_data)
                if '@transmute' in commands:
                    gid_list = [int(i)
                        for i in user_data.replace(' ', '').split(',')]
                    self.transmute_object(obj, gid_list)
                if '@addcounter' in commands:
                    counter_value = obj.properties.get('counter', 0)
                    counter_value += 1
                    trace.write('\tadd counter on "%s" to %s' %
                        (obj.name, counter_value))
                    obj.properties['counter'] = counter_value
                if '@clearcounter' in commands:
                    trace.write('\tclearing counter on "%s"' % obj.name)
                    obj.properties['counter'] = 0
                if '@setattr' in commands:
                    trace.write('altering objects within "%s"' % (obj.name))
                    self.alter_object_attributes(
                        obj.x, obj.y, obj.width, obj.height, user_data)
                # do we repeat this interaction next time
                if not '@repeat' in commands:
                    trace.write('\tkill interaction "%s" on "%s"' %
                        (name, obj.name))
                    if name in obj.properties.keys():
                        del obj.properties[name]
                    else:
                        trace.write(
                            '\tProperty "%s" on "%s" already deleted.' %
                            (name, obj.name))
        self.trigger_queue = requeue

    def alter_object_attributes(self, x, y, width, height, option_data):
        """
        Alter game object attributes as defined by the options given.
        Options is a string as define on a map object property.
        The region (x, y, width, height) is measured in map tiles.

        example options: type_filter=friend name_filter="the doctor" type=ai
        """

        # split options by space, preserving quoted values
        options = re.split(r''' (?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', option_data)

        # separate filters from attribute alters
        filters = []
        alters = []
        # these are stored as [key, value] lists
        for option in options:
            if '_filter' in option:
                filters.append(self.split_value_pairs(option))
            else:
                alters.append(self.split_value_pairs(option))

        # get objects within the region
        objects = []
        for x, y in rlhelper.iterate_square(x, y, width, height):
            map_objects = self.get_object_by_xy(x, y)
            for mo in map_objects:
                # ignore non gid objects (like rect regions) and the player.
                if mo.gid != -1 and mo is not self.player:
                    # no filters grabs any object
                    if not filters:
                        objects.append(mo)
                    for f in filters:
                        # fuzzy match by name
                        if f[0] == 'name_filter' and f[1] in mo.name:
                            objects.append(mo)
                        # strict match by type
                        elif f[0] == 'type_filter' and f[1] == mo.type:
                            objects.append(mo)

        # apply attributes to objects found
        for map_object in objects:
            for alter_data in alters:
                trace.write('\talter "%s": %s' % (map_object.name, alter_data))
                # we know the 'modes' attribute is a list
                if alter_data[0] == 'modes':
                    alter_data[1] = alter_data[1].split(',')
                try:
                    setattr(map_object, alter_data[0], float(str(alter_data[1])))
                except ValueError:
                    # that did not work, keep it a string
                    setattr(map_object, alter_data[0], alter_data[1])


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
                if (ff is not obj and
                    ff.type in ('ai', 'friend', 'player') and
                    self.story.tile_blocks(transmute_id)):
                    trace.write('hey, you cant transmorgify a tile ' +
                                'to a solid if someone is standing on it :p')
                    return False
            # transmorgify!
            obj.gid = transmute_id
            # update the level block matrix with our new aquired status
            self.update_block_matrix(
                obj.x, obj.y, self.story.tile_blocks(obj.gid))
            self.post(UpdateObjectGID(obj, obj.gid))
        except ValueError:
            trace.error('Error converting "%s" to a int while transmuting'
                        ' "%s"' % (str(gid_list), obj.name))

    def combat_turn(self,
                    attacker,
                    defender,
                    a_verb='hit',
                    d_verb='hit',
                    a_multiplier=0
                    ):
        """
        Begin a combat round.
        'a' and 'd' refer to attacker and defendor.

        """

        if not self.game_in_progress:
            return False
        if defender.dead:
            return
        a, d = (attacker, defender)
        # we say 'you' where the player is involved
        a_name = (a is self.player) and ('you') or (a.name)
        d_name = (d is self.player) and ('you') or (d.name)
        a_verb = (a is self.player) and (a_verb) or ('%ss' % a_verb)
        d_verb = (a is self.player) and ('%ss' % d_verb) or (d_verb)
        # damage control
        a_atk = a.attack + (a_multiplier * a.attack)
        d_atk = 0  # defender does not retaliate by default
        # apply upgrade abilities
        echo = alu.from_list(defender.upgrades, alu.ECHO_LOOP)
        if echo and echo.is_active:
            trace.write('%s has "echo" activated' % defender.name)
            # mitigate damage received and throw it back at the attacker.
            # each version will echo one eigth (12.5%) of the damage back.
            delta = a_atk * (float(echo.version) / 8)
            a_atk -= delta
            d_atk += delta
            d_verb = 'echo back'
        # damage
        if a_atk:
            self.adjust_character_health(d, -a_atk)
            self.post_msg('%s %s %s for %s' %
                (a_name, a_verb, d_name, a_atk), color.combat_message)
        if d_atk:
            self.adjust_character_health(a, -d_atk)
            self.post_msg('%s %s %s for %s' %
                (d_name, d_verb, a_name, d_atk), color.combat_message)
        # traces
        trace.write('%s on %s health' % (attacker.name, attacker.health))
        trace.write('%s on %s health' % (defender.name, defender.health))
        # death
        if a.health <= 0:
            if a is self.player:
                self.crash_player()
            else:
                self.kill_character(a)
        if d.health <= 0:
            if d is self.player:
                self.crash_player()
            else:
                self.kill_character(d)
        self.look_at_target()

    def adjust_character_health(self, character, amount):
        """
        Adjust a character health.

        """

        character.health = rlhelper.clamp(
            character.health + amount, 0, character.max_health)

    def kill_character(self, character):
        """
        Remove a character from play.
        """

        if character in self.objects:
            character.dead = True
            self.post_msg('The %s crashes' % (character.name), color.ai_crash)
            # find and activate the characer crash animation
            crash_anim = self.story.animations_by_name(
                '%s crash' % (character.name))
            if crash_anim:
                self.transmute_object(character, [crash_anim.as_int('gid')])
            # delay the kill event which will remove the sprite
            self.queue_event(KillCharacterEvent(character), 2)

    def crash_player(self):
        """
        Mark the player as dead and queue some events to fire level failed.

        """

        self.player.dead = True
        self.post_msg('** You Segfault **', color.ai_crash)
        self.queue_event(StateChangeEvent(STATE_LEVEL_FAIL), 2)
        # find the player crash animation data
        crash_anim = self.story.animations_by_name('player crash')
        if crash_anim:
            self.transmute_object(self.player, [crash_anim.as_int('gid')])

    def change_state(self, state):
        """
        Process game state change events.
        """

        # push or pop the given state
        if not self.state.process(state):
            self.post(QuitEvent())

    def show_dialogue(self, key):
        """
        Update the model state to show a dialogue screen.
        keys is a list of dialogue key names.
        """

        dialogue = self.story.dialogue(key)

        if dialogue:
            # tell everyone about the words about to display
            self.post(DialogueEvent(dialogue))
            # change our state to dialogue mode
            self.post(StateChangeEvent(STATE_DIALOG))
        else:
            trace.write('dialogue "%s" not found in story definition' % (key))

    def install_upgrade(self, upgrade_name):
        """
        Install an upgrade by it's code.

        """

        # if player has this upgrade, version_up() it.
        status = None
        upgrade = alu.from_list(self.player.upgrades, upgrade_name)
        if upgrade:
            upgrade.version_up()
            trace.write('upgrading "%s"' % upgrade_name)
            status = 'upgraded %s (v%s)' % (upgrade_name, upgrade.version)
        else:
            # else get an instance of it and add it to the player.
            trace.write('installing "%s"' % upgrade_name)
            upgrade = alu.from_name(upgrade_name)
            if upgrade:
                self.player.upgrades.append(upgrade)
                status = 'installed %s' % upgrade_name
        # apply upgrade abilities
        result = upgrade.apply_upgrade(self.player)
        if status or result:
            self.upgrades_available -= 1
            # look around again if any abilities upgraded our perception
            self.look_around()
            # notify listeners we have new things
            self.post_msg(status, color=color.tip)
            if result:
                self.post_msg(result, color=color.tip)
        return '%s\n%s' % (status, result is None and ' ' or result)

    def allow_upgrade(self):
        """
        Gives the player one more allowed upgrade.

        """

        self.upgrades_available += 1
        self.post_msg('You have upgrades available!', color=color.tip)

    def target_next(self, type_list=['ai', 'friend']):
        """
        Targets the next available object in range.

        """

        last_selected = self.target_object
        origin_x, origin_y = (self.player.x, self.player.y)
        reach = self.player.view_range
        level = self.level.tmx
        w, h = level.width, level.height
        first_match = None
        choose_next = False
        breaked = False

        for x, y in rlhelper.cover_area(origin_x, origin_y, reach, w, h):
            objs = self.get_object_by_xy(x, y)
            for obj in [o for o in objs if o.in_range and o.type in type_list]:
                if not first_match:
                    first_match = obj
                if choose_next:
                    first_match = obj
                    breaked = True
                    break
                if obj is last_selected:
                    choose_next = True
            if breaked:
                break
        self.target_object = first_match
        if first_match:
            trace.write('targeted %s' % first_match.name)

    def use_upgrade(self, upgrade_name):
        """
        Use the given upgrade if the player has it.

        """

        # test if the player has this upgrade, if it is enabled and if
        # it requires a target.
        upgrade = alu.from_list(self.player.upgrades, upgrade_name)
        if not upgrade:
            trace.write('"%s" is not an upgrade the player has' % upgrade_name)
            return
        if not upgrade.enabled:
            trace.write('"%s" is not enabled' % upgrade_name)
            return
        if upgrade.use_targeting and self.target_object is None:
            self.post_msg('Select a target first', color.tip)
            return

        # grab the AI in reach of the upgrade, or the selected target
        if upgrade.max_targets > 1:
            targets = self.get_objects_in_reach(
                self.player.x, self.player.y, upgrade.reach)
            # grab a sample of max_targets.
            if upgrade.max_targets < len(targets):
                targets = random.sample(targets, upgrade.max_targets)
        else:
            targets = [self.target_object] if self.target_object else None

        if targets:
            trace.write('targets in reach: %s' %
                ', '.join([t.name for t in targets]))

        # test for enough power to pay the upgrade ability cost
        if upgrade.cost > self.player.power:
            self.post_msg('not enough power', color.message)
            return
        else:
            self.player.power -= upgrade.cost

        # action this upgrade - it is now active
        upgrade.activate()

        # perform upgrade-specific voodoo
        if upgrade_name == alu.ECHO_LOOP:
            # this upgrade is handled in combat_turn()
            self.post_msg('%s activated' % upgrade_name, color.upgrade_tip)

        if upgrade_name == alu.ZAP:
            # zap the targets from a distance
            for ai in targets:
                self.combat_turn(self.player, ai, a_verb='zap',
                                a_multiplier=upgrade.damage_multiplier)

        if upgrade_name == alu.CODE_FREEZE:
            # freeze targets
            for ai in targets:
                ai.freeze_duration = upgrade.duration
                self.post_msg('the %s froze!' %
                    (ai.name), color.combat_message)

        if upgrade_name == alu.PING_FLOOD:
            # ping flood (confuse) targets
            for ai in targets:
                ai.confused_duration = upgrade.duration
                self.post_msg('the %s is confused!' %
                    (ai.name), color.combat_message)

        if upgrade_name == alu.FORK_BOMB:
            # bomb the area around the target
            for count in range(0, upgrade.version):
                for ai in [t for t in targets if not t.dead]:
                    self.combat_turn(self.player, ai,
                        a_verb='bomb', a_multiplier=upgrade.damage_multiplier)

        if upgrade_name == alu.EXPLOIT:
            # take control of another for a short while.
            # we do this by storing the current player owning the target.
            # when the ability resolves in the player move event we
            # switch back.
            self.store['stored player'] = self.player
            self.player = self.target_object
            self.player.upgrades.append(upgrade)
            self.post_msg('you exploit the %s!' %
                (self.target_object.name), color.combat_message)
            self.look_around()
            self.post(RefreshUpgradesEvent())

        if upgrade_name == alu.DESERIALIZE:
            # blink into the last direction moved.
            # we do this by getting the line segments in direction and
            # testing each for blockability.
            if self.player.last_direction:
                dir_x = self.player.last_direction[0]
                dir_y = self.player.last_direction[1]
                from_x = self.player.x + dir_x
                from_y = self.player.y + dir_y
                to_x = from_x + (dir_x * upgrade.reach)
                to_y = from_y + (dir_y * upgrade.reach)
                jmp_x = None
                jmp_y = None
                # version n+ crosses solids. we do this by counting segments
                # from the destination and grab the first open tile.
                # For lower versions we count segments as normal until we
                # reach max or we hit a solid.
                ghost = upgrade.version > 3
                if ghost:
                    segs = rlhelper.get_line_segments(
                        to_x, to_y, from_x, from_y)
                else:
                    segs = rlhelper.get_line_segments(
                        from_x, from_y, to_x, to_y)
                for x, y in segs:
                    if self.tile_is_solid(x, y):
                        # non ghosts stop at the first solid
                        if not ghost:
                            break
                    else:
                        jmp_x = x
                        jmp_y = y
                        if ghost:
                            # ghosties grab the first open spot
                            break
                if jmp_x:
                    self.move_character_to(self.player, jmp_x, jmp_y)

        # take this as a turn
        self.move_player((0, 0))

    def player_upgrade(self, upgrade_name):
        """
        Gets the upgrade by name that the player has.
        Returns None if the player does not have this upgrade.

        """

        return alu.from_list(self.player.upgrades, upgrade_name)

    def post_msg(self, message, color=color.message):
        """
        A helper to post game messages.

        """

        self.recent_messages.append(message)
        self.evManager.Post(MessageEvent(message, color))

    def queue_event(self, event, seconds_delay):
        """
        Queue an event for posting at the end of the player's turn.

        """

        self.event_queue[event] = seconds_delay * FPS

    def post(self, event):
        """
        A helper to post game events.

        """

        self.evManager.Post(event)

    def debug_action(self, event):
        """
        Perform some debugesque action.
        These are considered cheating if you are not debugging ;)

        """

        if event.request_type == 'warp to next level':
            self.can_warp = True
            self.warp_level()
        elif event.request_type == 'restart level':
            self.restart_level()
        elif event.request_type == 'reveal map':
            self.level.matrix['seen'] = rlhelper.make_matrix(
                self.level_width, self.level_height, 1)
            for obj in self.objects:
                obj.seen = True
            self.look_around()
            self.post(PlayerMovedEvent())
        elif event.request_type == 'heal all':
            self.upgrades_available = 10
            self.player.health = self.player.max_health
            self.player.power = self.player.max_power
        elif event.request_type == 'demo map':
            # get the level number with the demo map name
            level_index = self.story.level_number('demo-map.tmx')
            if level_index:
                self.level_number = level_index
                self.warp_level(restart=True)


    def stories_list(self):
        """
        Gets the list of playable stories.

        """

        return [('ascension', 'You awaken to the smell of waffles.')]

    def saved_games_list(self):
        """
        Gets the list of saved games available.
        Returns a (key, title) list.

        """

        games_list = []
        for n in range(1, 4):
            title = self.load_savegame_title(n)
            if title is None:
                games_list.append(('new game slot %s' % (n), 'new game'))
            else:
                games_list.append(('load game slot %s' % (n), title))
        return games_list

    def load_savegame_title(self, slot_number):
        """
        Build a savegame slot title from it's stored info.
        Returns None if there is no save game for that slot.

        """

        fn = 'savedgame%s' % (slot_number)
        if os.path.exists(fn):
            values = {}
            jar = pickle.Unpickler(open(fn, 'r'))
            saved_version = jar.load()
            saved_time = jar.load()
            values['time'] = self.human_friendly_timespan(saved_time)
            values['story'] = jar.load()
            values['level'] = jar.load() + 1
            jar = None
            return '%(story)s level %(level)s, %(time)s' % (values)

    def human_friendly_timespan(self, past_date):
        """
        Give a human readable time difference from now.
        """

        human = 'infinity'
        delta_time = datetime.datetime.now() - past_date
        if delta_time.days > 60:
            human = '%s months ago' % (delta_time.days / 90)
        elif delta_time.days > 2:
            human = '%s days ago' % (delta_time.days)
        else:
            mins = int(delta_time.total_seconds() / 60)
            hrs = int(mins / 60)
            if hrs > 1:
                human = '%s hours ago' % (hrs)
            elif mins > 2:
                human = '%s minutes ago' % (mins)
            else:
                human = 'just now'
        return human

    def save_game(self):
        """
        Saves the current game to a disk file.
        """

        if self.game_slot > 0:
            fn = 'savedgame%s' % (self.game_slot)
            trace.write('writing %s' % fn)
            if self.game_in_progress:
                jar = pickle.Pickler(open(fn, 'w'))
                jar.dump(VERSION)
                jar.dump(datetime.datetime.now())
                jar.dump(self.story_name)
                jar.dump(self.level_number - 1)
                jar.dump(self.turn)
                jar.dump(self.upgrades_available)
                jar.dump(self.recent_messages)
                jar.dump(self.store['player copy'])
                jar = None

    def load_game(self):
        """
        Loads a saved game from a disk file.
        """

        if self.game_slot > 0:
            fn = 'savedgame%s' % (self.game_slot)
            if os.path.exists(fn):
                trace.write('loading %s' % (fn))
                jar = pickle.Unpickler(open(fn, 'r'))
                saved_version = jar.load()
                saved_time = jar.load()
                self.story_name = jar.load()
                self.level_number = jar.load()
                self.turn = jar.load()
                self.upgrades_available = jar.load()
                self.recent_messages = jar.load()
                self.player = jar.load()
                jar = None

    def about_game_data(self):
        """
        Get the about game config data.

        """

        conf = ConfigObj('./alive.conf', file_error=True)
        data = conf['about']
        for screen_key in data.keys():
            stripped = '\n'.join([s.lstrip() for s
                            in data[screen_key]['datas'].split('\n')])
            data[screen_key]['datas'] = stripped
        return conf['about']

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

    def __init__(self, filename):
        """
        Attributes:

        filename (str): relative path to the level file.
        data (TMXParser): tmx file data.
        """

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

    def swap(self, state):
        """
        Swaps the current state out for the one given.
        Note this bypasses unwinding of the natural stack order.

        Useful for menus where you want to switch states yet easily
        unwind only one state.
        """

        if state and self.statestack:
            self.pop()
            self.push(state)

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

        pass
