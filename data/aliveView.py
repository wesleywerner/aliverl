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
import random
import textwrap
import pygame
from pygame import image
from pygame.locals import *
import ui
import trace
import color
from const import *
import rlhelper
import aliveModel
import aliveUpgrades as alu
from aliveViewClasses import *
from eventmanager import *
from tmxparser import TMXParser
from tmxparser import TilesetParser


class GraphicalView(object):
    """
    Draws the model state onto the screen.

    Attributes:

    isinitialized (bool):
        PyGame initialized OK and we are good to draw.

    screen (Surface):
        The surface representing the screen as returned by PyGame set_mode().

    clock (Clock):
        Keeps the fps constant when drawing.

    smallfont (Font):
        A small font.

    largefont (Font):
        A larger font.

    play_image (Surface):
        An image of the game play area, excluding game borders.
        All sprites and other game action is drawn here.

    image (Surface):
        This is the final destination for all rendering, before it gets
        blit to the screen. This separation allows us to scale the output
        if need be, or center it for arbitrary screen sizes.

    play_area (Rect):
        location on screen to draw gameplay.

    statsarea (Rect):
        The area on image to draw player stats.

    viewport (Rect):
        The portion of the game map we are looking at, like the viewport
        of a ship. The level map may be larger than our image, and the
        viewport defines which part of that map we are viewing.
        It moves around with the player character via the
        update_viewport() call.

    viewport_shift (Rect):
        On each game tick the viewport will shift to lean towards the same
        position ast his virtual viewport.
        This gives a gradual moving like motion.

    sprites (Dict):
        A sprite lookup by object id.

    messages (list):
        list of recent game messages.

    chosen_upgrade (string):
        the name of the currently selected upgrade in the info screen.

    last_info_state (const):
        the last state of the info screen. used to synchronize the last
        selected tab on that screen.

    """

    def __init__(self, evManager, model):
        """
        evManager controls Post()ing and notify()ing events.
        model gives us a strong reference to what we need to draw.

        """

        self.evManager = evManager
        evManager.RegisterListener(self)
        self.model = model
        self.isinitialized = False
        self.screen = None
        self.clock = None
        self.smallfont = None
        self.largefont = None
        self.image = None
        self.play_image = None
        self.graphs = {}
        self.play_area = None
        self.statsarea = None
        self.viewport = None
        self.viewport_shift = None
        self.windowsize = None
        self.sprites = {}
        self.message_sprites = []
        self.last_tip_pos = 0
        self.transition_queue = []
        self.ui = None
        self.chosen_upgrade = None
        self.chosen_upgrade_details = None
        self.last_info_state = STATE_INFO_HOME
        self.menu_buttons = None

    @property
    def tmx(self):
        """
        A virtual property to access the level data on the model.
        """

        return self.model.level.tmx

    #TODO rename to tile_width
    @property
    def tile_w(self):
        """
        A virtual property to access the tile width.
        """

        return self.tmx.tile_width

    #TODO rename to tile_height
    @property
    def tile_h(self):
        """
        A virtual property to access the tile height.
        """

        return self.tmx.tile_height

    @property
    def transition(self):
        """
        A virtual property to access the last transition in the queue.
        """

        if self.transition_queue:
            return self.transition_queue[-1]

    def post(self, event):
        """
        A helper to post game events.

        """

        self.evManager.Post(event)

    def notify(self, event):
        """
        Called by an event in the message queue.
        """

        try:
            if isinstance(event, TickEvent):
                self.render()
                self.clock.tick(FPS)

            elif isinstance(event, CharacterMovedEvent):
                self.move_sprite(event)

            elif isinstance(event, PlayerMovedEvent):
                self.update_viewport()
                self.update_button_borders()
                self.update_graphs()

            elif isinstance(event, MessageEvent):
                self.create_floating_tip(event.message,
                    event.color and event.color or color.message)

            elif isinstance(event, KillCharacterEvent):
                self.kill_sprite(event.character)

            elif isinstance(event, UpdateObjectGID):
                self.transmute_sprite(event)

            elif isinstance(event, TargetTileEvent):
                self.model.target_next()

            elif isinstance(event, DialogueEvent):
                self.queue_dialogue(event.dialogue)

            elif isinstance(event, NextLevelEvent):
                self.load_level()
                self.create_sprites()
                # pre-render the map and sprite images for any warp transitions
                self.render()
                self.queue_warp_transitions()

            elif isinstance(event, InitializeEvent):
                self.initialize()

            elif isinstance(event, QuitEvent):
                self.isinitialized = False
                pygame.quit()

            elif isinstance(event, DebugEvent):
                if event.request_type == 'animation cheatsheet':
                    self.draw_animations_cheatsheet()
                    self.draw_number_cheatsheet()

            elif isinstance(event, InputEvent):
                if self.ui:
                    if event.char:
                        self.ui.click(event.char)
                    else:
                        self.ui.unclick()

            elif (isinstance(event, StateChangeEvent) or
                    isinstance(event, StateSwapEvent)):
                model_state = self.model.state.peek()
                if self.ui:
                    self.reposition_upgrade_buttons(model_state)
                    trace.write('set ui context to game state %s' %
                        model_state)
                    self.ui.set_context(model_state)

                if event.state == STATE_HELP:
                    self.show_help_screens()
                elif event.state == STATE_LEVEL_FAIL:
                    # housekeeping: reset some things for level restart
                    self.message_sprites = []
                    self.queue_slide_transition('', None, color.ai_crash)

            elif isinstance(event, RefreshUpgradesEvent):
                model_state = self.model.state.peek()
                self.reposition_upgrade_buttons(model_state)

        except Exception, e:
            # we explicitly catch Exception, since sys.exit() will throw
            # a SystemExit, and we want that one to not catch here.
            # That means we drop to the terminal if sys.exit() is used.
            self.evManager.Post(CrashEvent())

    def render(self):
        """
        Draw the current game state on screen.
        blits the correct surfaces for the current Model state.
        Does nothing if isinitialized == False (pygame.init failed)
        """

        if not self.isinitialized:
            return

        try:
            state = self.model.state.peek()
            if state == STATE_CRASH:
                somewords = self.draw_text(CRASH_MESSAGE,
                                            self.smallfont,
                                            False,
                                            color.yellow)
                self.screen.blit(somewords, (0, 0))
                pygame.display.flip()
                return
        except Exception, e:
            # these lines pose an interesting problem:
            # if the crash message crashes, we go down hard.
            print('\n'.join(CRASH_MESSAGE))
            import traceback
            print('\n' + str(traceback.format_exc()))
            sys.exit(1)

        self.shift_viewport()

        # reset the main image by painting a background over it
        self.image.blit(self.defaultbackground, (0, 0))

        if state == STATE_INTRO:
            pass

        elif state in (STATE_INFO_HOME, STATE_INFO_UPGRADES, STATE_INFO_WINS):
            self.draw_info_screen(state)

        elif state == STATE_LEVEL_FAIL:
            self.draw_level_fail_screen()
            self.draw_graphs()

        elif state == STATE_PLAY:
            # draw all the game play images on to play_image and
            # merge that into our main image at the relevant position
            self.play_image.fill(color.magenta)
            self.draw_borders()
            self.draw_graphs()
            self.draw_sprites()
            self.draw_target()
            self.draw_fog()
            self.draw_scroller_text()
            self.image.blit(self.play_image, self.play_area)

        elif state in (STATE_MENU_MAIN,
                        STATE_MENU_SAVED,
                        STATE_MENU_STORIES,
                        STATE_MENU_OPTIONS):
            self.draw_menu()

        # NOTE: no need to handle drawing for HELP or DIALOGUE states
        #       since those use the TransitionBase, which draws itself below.

        # apply any transitions (including dialogues and help screens)
        if self.transition:
            self.transition.update(pygame.time.get_ticks())
            self.image.blit(self.transition.image, (0, 0))
        self.step_transitions()

        # finally draw our composed image onto the screen
        self.screen.blit(self.image, self.game_area)

        # update the ui and draw it to the main image
        self.ui.update()
        self.screen.blit(self.ui.image, (0, 0))

        pygame.display.flip()

    def draw_animations_cheatsheet(self):
        """
        Draw a cheatsheet for the animations defined in this story
        and save it to a file.
        """

        size = (1200, 600)
        surf = pygame.Surface(size)
        surf.fill(color.black)
        x, y = (10, 50)
        column_width = 0
        #level_file = os.path.basename(self.model.level.filename)
        image_filename = '/tmp/alive_animations.png'
        fnt = self.largefont.render('Alive animations', False, color.green)
        title_width = fnt.get_width()
        surf.blit(fnt, (10, 10))
        #fnt = self.smallfont.render(level_file, False, color.white)
        #surf.blit(fnt, (40 + title_width, 20))

        data = self.model.story.raw_animation_data()
        for key, value in data.items():
            gid = value.as_int('gid')
            tile = self.tsp[gid]
            surf.blit(tile, (x, y))
            fnt = self.smallfont.render(
                str(gid) + ': ' + key, False, color.white)
            surf.blit(fnt, (x + self.tile_w, y))
            this_width = x + self.tile_w + fnt.get_width()
            if this_width > column_width:
                column_width = this_width
            y += self.tile_h * 1.5

            if y > size[1] - self.tile_h:
                y = 50
                x = column_width
                column_width = 0

        pygame.image.save(surf, image_filename)
        self.create_floating_tip(
            'saved animation cheatsheet as ' + image_filename, color.white)

    def draw_number_cheatsheet(self):
        """
        Draw a copy of the tileset with index numbers and save it to a file.

        """

        pix = image.load('images/alive-tileset.png')
        w, h = pix.get_size()
        w, h = (w / self.tile_w, h / self.tile_h)
        for y in range(0, h):
            for x in range(0, w):
                gid = x + (y * w) + 1
                xpos = x * self.tile_w
                ypos = y * self.tile_h
                pygame.draw.rect(pix, color.white,
                    (xpos, ypos, self.tile_w, self.tile_h), 1)
                num_pix = self.smallfont.render(
                    str(gid), False, color.white)
                pix.blit(num_pix, (xpos, ypos))
        image_filename = '/tmp/alive_tileset_indexed.png'
        pygame.image.save(pix, image_filename)
        self.create_floating_tip(
            'saved animation cheatsheet as ' + image_filename, color.white)

    def draw_menu(self):
        """
        Draw the main menu.
        """

        self.image.blit(self.menubackground, (0, 0))

    def draw_action_shot(self, x, y):
        """
        Draw a small static action shot of the game play action.

        """

        # define a portion of the play area
        snap_rect = pygame.Rect(
                    self.tile_w * (self.model.player.x - 2),
                    self.tile_h * (self.model.player.y - 2),
                    self.tile_w * 5,
                    self.tile_h * 5,
                    )
        # adjust it to our viewport
        snap_rect = snap_rect.move(-self.viewport.left, -self.viewport.top)
        self.image.blit(self.play_image, (x, y), snap_rect)
        # surround with a nice rectangle
        pygame.draw.rect(self.image, color.darkest_green,
            (x, y, snap_rect[2], snap_rect[3]), 2)

    def draw_level_fail_screen(self):
        """
        Draw the level failed screen.

        """

        self.image.blit(self.failed_background, (0, 0))
        self.draw_action_shot(14, 14)
        fail_words = (
            'Your core became unstable :-( '
            'Press spacebar to try that level again. '
            'Good luck!'
            )
        pix = self.draw_text_block(
            text=fail_words,
            font=self.smallfont,
            antialias=False,
            fontcolor=color.gray,
            wrap_width=40,
            )
        self.image.blit(pix, (180, 122))
        self.draw_messages(28, 184, amount=20)

    def draw_info_screen(self, game_state):
        """
        Draw the player info screen.
        """

        self.image.blit(self.info_screen, (0, 0))

        if game_state == STATE_INFO_HOME:
            self.draw_action_shot(220, 94)
            # the level name
            pix = self.largefont.render(
                self.model.story.level_title(self.model.level_number),
                False, color.message)
            self.image.blit(pix, (28, 55))
            # column of stats titles
            titles = 'turn\nlevel\nhealth\npower\nattack\nspeed\nview'
            pix = self.draw_text_block(
                titles, self.largefont, False, color.desaturated_green)
            self.image.blit(pix, (28, 94))
            values = '%s\n%s\n%s\n%s\n%s\n%s\n%s' % (
                self.model.turn,
                self.model.level_number,
                self.model.player.health,
                self.model.player.power,
                self.model.player.attack,
                self.model.player.speed,
                self.model.player.view_range,
                )
            pix = self.draw_text_block(
                values, self.largefont, False, color.desaturated_yellow)
            self.image.blit(pix, (140, 94))
            self.draw_messages(28, 290, amount=15)

        elif game_state == STATE_INFO_UPGRADES:
            # display the amount of upgrades the player can install
            amt = self.model.upgrades_available
            if amt == 0:
                status = 'No upgrades points to spend.'
            elif amt == 1:
                status = 'You can install 1 upgrade.'
            else:
                status = 'You can install %s upgrades.' % amt
            pix = self.draw_text([status], self.smallfont, False,
                color.lighter_blue)
            self.image.blit(pix, (140, 70))
            # show chosen upgrade details
            if self.chosen_upgrade_details:
                self.image.blit(self.chosen_upgrade_details, (45, 120))

    def draw_target(self):
        """
        Draw a selection around the targeted object.

        """

        target = self.model.target_object
        if target:
            sprite = self.sprites.get(id(target), None)
            if sprite:
                new_rect = sprite.rect.move(
                    -self.viewport.left, -self.viewport.top)
                pygame.draw.rect(self.play_image,
                                color.target_selection, new_rect, 1)

    def draw_sprites(self):
        """
        Draw the play area: level tiles and objects.
        """

        # start by drawing the level map on our play image.
        ticks = pygame.time.get_ticks()
        # for each sprite in our viewport range
        for y in range(0, self.tmx.height):
            for x in range(0, self.tmx.width):

                # draw static map tiles
                if self.model.seen_tile(x, y):
                    for layer in self.tmx.tilelayers:
                        gid = layer.at((x, y))
                        tile = self.tsp[gid]
                        if tile:
                            new_rect = (
                                x * self.tile_w - self.viewport.left,
                                y * self.tile_h - self.viewport.top)
                            self.play_image.blit(tile, new_rect)

                # draw movable sprite objects at this location
                object_list = self.model.get_object_by_xy(x, y)
                for obj in object_list:
                    # grab the sprite that match this object id
                    sprite = self.sprites.get(id(obj), None)
                    # test if this is a character within view range
                    if obj.type in ('ai', 'friend', 'player'):
                        if obj.in_range:
                            visible = True
                        else:
                            visible = False
                    # or not a character, but has been seen before
                    elif obj.seen:
                        visible = True
                    else:
                        visible = False
                    # draw if both are happy
                    if sprite:
                        # update the sprite animation.
                        sprite.update(ticks)
                        if visible:
                            # our play_image is only the size of the screen
                            # we update sprite positions, which are relative to
                            # entire map, by subtracting the viewport location.
                            new_rect = sprite.rect.move(
                                -self.viewport.left, -self.viewport.top)
                            self.play_image.blit(sprite.image, new_rect)

    def draw_fog(self):
        """
        Overlay fog on the level for that which is out of player view.
        """

        unseen_sprite = self.tsp[UNSEEN_GID]
        fog_sprite = self.tsp[FOG_GID]

        for y in range(0, self.tmx.height):
            for x in range(0, self.tmx.width):
                # lookup list of which positions has been seen
                # and overlay those with FOG_GID, the rest with UNSEEN_GID
                seen = self.model.level.matrix['seen'][x][y]

                # because our play_image is only the size of the screen
                # we accommodate sprite positions, which are relative to
                # an entire map, by subtracting the viewport location.
                new_rect = (
                    x * self.tile_w - self.viewport.left,
                    y * self.tile_h - self.viewport.top)

                # not yet seen
                if seen == 0:
                    # self.play_image.blit(unseen_sprite, new_rect)
                    self.play_image.blit(fog_sprite, new_rect)
                # seen but out of range
                elif seen == 1:
                    self.play_image.blit(fog_sprite, new_rect)

    def draw_scroller_text(self):
        """
        Draw any scrolling text sprites.
        """

        ticks = pygame.time.get_ticks()
        for sprite in self.message_sprites:
            # utilize the sprite's fps attribute to determine update speed.
            if sprite.canupdate(ticks):
                sprite.update(ticks)
            if not sprite.is_moving:
                self.message_sprites.remove(sprite)
            else:
                new_rect = sprite.rect.move(
                    -self.viewport.left, -self.viewport.top)
                self.play_image.blit(sprite.image, new_rect)

    def step_transitions(self):
        """
        Move to teh next queued transition if the current one is done and
        not waiting for a user keypress.

        """

        # stop if the transition is still animating or waiting for a keypress.
        if self.transition:
            if not self.transition.done:
                return
            if self.transition.waitforkey:
                return

        # nothing left to wait for, so move along:
        # we use the next dialogue call as it does what we need
        # in addition to handling dialogue states
        self.next_dialogue()

    def queue_warp_transitions(self):
        """
        Queue some nice level warp transitions on warp.

        """

        open_transition = SlideinTransition(
                        size=self.game_area.size,
                        fps=FPS,
                        font=self.smallfont,
                        title='',
                        direction_reversed=True
                        )
        self.transition_queue.insert(0, open_transition)

    def queue_slide_transition(self, title,
        inner_bg=None, boxcolor=color.green, direction_reversed=False):
        """
        Queue a generic slide-in transition.
        It uses the current game image as the background, giving a overlay
        of the current view.

        """

        new_transition = SlideinTransition(
            size=self.game_area.size,
            fps=FPS,
            font=self.smallfont,
            title=title,
            inner_bg=inner_bg,
            outer_bg=self.image.copy(),
            boxcolor=boxcolor,
            direction_reversed=direction_reversed
            )
        self.transition_queue.insert(0, new_transition)

    def queue_dialogue(self, dialogue):
        """
        Queue a dialogue for display.

        """

        trace.write('showing dialogue "%s"' % dialogue.name)
        # we only need one slide-in transition for many screens.
        terminal_slidein_added = False
        # a dialogue may contain multiple screens. Keep this in mind.
        for dialogue_screen in dialogue.keys():
            datas = dialogue[dialogue_screen]
            # terminal type defaults
            set_background = self.terminal_bg
            set_wrap = 40
            set_x_offset = 55
            set_y_offset = 55
            # override story types
            if datas['type'] == 'story':
                set_background = self.dialogue_bg
                #set_wrap = 45
                #set_x_offset = 55
                #set_y_offset = 55
            # start with a Slide-in Transition
            if not terminal_slidein_added:
                terminal_slidein_added = True
                self.queue_slide_transition(
                    'connecting . . .', set_background)
            # follow up with a terminal printer
            text_color = getattr(color, datas['color'])
            words = self.wrap_text(datas['datas'], set_wrap)
            new_transition = TerminalPrinter(
                size=self.game_area.size,
                background_color=color.magenta,
                fps=FPS,
                font=self.largefont,
                words=words,
                word_color=text_color,
                words_x_offset=set_x_offset,
                words_y_offset=set_x_offset,
                background=set_background
                )
            self.transition_queue.insert(0, new_transition)
        # add a closing transition
        self.queue_slide_transition(
            '', self.dialogue_bg, direction_reversed=True)

    def next_dialogue(self):
        """
        Move to the next dialogue line
        """

        # move to the next transition in the queue
        if self.transition_queue:
            self.transition_queue.pop()

        # cater for certain STATES that rely on transitions
        # by popping the state queue if no more transitions are available.
        state = self.model.state.peek()
        if (state in (STATE_DIALOG, STATE_HELP) and
            not self.transition_queue):
                self.post(StateChangeEvent(None))

    def close_dialogue(self):
        """
        Close running dialogues and reset for next time.
        """

        self.transition_queue = []
        self.next_dialogue()

    def draw_borders(self):
        """
        Draw game borders.
        """

        self.image.blit(self.borders, (0, 0))

    def update_graphs(self):
        """
        Update graphs to reflect player stats.

        """

        self.graphs['health'].set_values(
            self.model.player.health_history,
            self.model.player.max_health)
        self.graphs['power'].set_values(
            self.model.player.power_history,
            self.model.player.max_power)

    def draw_graphs(self):
        """
        Draw the stats graphs.
        """

        ticks = pygame.time.get_ticks()
        for key, graph in self.graphs.items():
            graph.update(ticks)
            graph.draw(self.image)

    def draw_messages(self, x, y,
        message_color=color.message, amount=None):
        """
        Draw recent game messages.

        """

        if amount:
            amount *= -1
        pix = self.draw_text(
            self.model.recent_messages[amount:],
            self.smallfont,
            False,
            message_color
            )
        self.image.blit(pix, (x, y))

    def wrap_text(self, message, maxlength):
        """
        Wraps a long string into multiple lines.
        Preserves paragraphs as indicated by multiple newlines.

        """

        outlines = []
        for line in message.lstrip('\n').split('\n'):
            if line == '':
                outlines.append(' ')
            else:
                outlines.extend(textwrap.wrap(line, maxlength))
        return outlines

    def draw_text(
            self, lines, font, antialias, fontcolor,
            colorize=None, background=None):
        """ # Simple functions to easily render pre-wrapped text onto a single
        # surface with a uniform background.
        # Author: George Paci

        # Results with various background color alphas:
        # no background given:
        #   ultimate blit will just change figure part of text,
        #   not ground i.e. it will be interpreted as a transparent background
        # background alpha = 0:
        # background alpha = 128, entire bounding rectangle will
        # be equally blended
        # with background color, both within and outside text
        # background alpha = 255:
        #   entire bounding rectangle will be background color
        #
        # (At this point, we're not trying to respect foreground color alpha;
        # we could by compositing the lines first onto a transparent surface,
        # then blitting to the returned surface.)

        colorize sets by how much each rgb value is upped for each line.
        (0, 10, 0) will up green by 10 for each line printed.
         """

        fontHeight = font.get_height()
        surfaces = []
        c = fontcolor
        if colorize:
            for ln in lines:
                c = (c[0] + colorize[0],
                    c[1] + colorize[1], c[2] + colorize[2])
                surfaces.append(font.render(ln, antialias, c))
        else:
            surfaces = [font.render(ln, antialias, fontcolor) for ln in lines]
        maxwidth = max([s.get_width() for s in surfaces])
        result = pygame.Surface((maxwidth, len(lines) * fontHeight))
        result.set_colorkey(color.magenta)
        if background is None:
            result.fill(color.magenta)
        else:
            result.fill(background)

        for i in range(len(lines)):
            result.blit(surfaces[i], (0, i * fontHeight))
        return result

    def draw_text_block(
            self, text, font, antialias, fontcolor,
            colorize=None, background=None, wrap_width=None):
        """ renders block text with newlines. """

        if wrap_width:
            lines = self.wrap_text(text, wrap_width)
        else:
            lines = text.replace("\r\n", "\n").replace("\r", "\n")
            lines = lines.split("\n")
        return self.draw_text(
                        lines=lines,
                        font=font,
                        antialias=antialias,
                        fontcolor=fontcolor,
                        colorize=colorize,
                        background=background
                        )

    def load_level(self):
        """
        Load the map data and prepare some resources for drawing the game.
        Note: we only support the first tilset as defined in the self.tmx.
        """

        story = self.model.story
        #tilesetfile = os.path.join(story.path, self.tmx.tilesets[0].source)
        tilesetfile = 'images/alive-tileset.png'
        self.tsp = TilesetParser(
                                tilesetfile,
                                (self.tile_w, self.tile_h),
                                color.magenta
                                )

    def set_sprite_defaults(self, obj):
        """
        Apply sprite settings to an object from the story animations setting.
        """

        # set defaults
        defaults = {'frames': [], 'fps': 0, 'loop': 0}
        [setattr(obj, k, v) for k, v in defaults.items()]

        # grab animation defs
        anims = self.model.story.animations_by_gid(obj.gid)

        # grab our sprite
        sprite = self.sprites.get(id(obj), None)
        if not sprite:
            trace.write('%s has no matching sprite object.' % obj.name)
            return

        # apply animation defs
        if anims:
            obj.frames = map(int, anims['frames'])
            obj.fps = anims.as_float('fps') + round(random.random() - 0.5, 1)
            obj.loop = anims.as_int('loop')

        # ensure at least 1 frame
        if len(obj.frames) == 0:
            obj.frames.append(obj.gid)

        # add all frame images
        sprite.clear()
        for f in obj.frames:
            sprite.addimage(self.tsp[f], obj.fps, obj.loop)

    def create_sprites(self):
        """
        Create all the sprites that represent all level objects.
        """

        self.sprites = {}
        self.message_sprites = []

        for obj in [o for o in self.model.objects if o.gid > -1]:
            x = (obj.x * self.tile_w)
            y = (obj.y * self.tile_h)
            sprite_id = id(obj)
            s = Sprite(
                    sprite_id,
                    Rect(x, y,
                        self.tile_w,
                        self.tile_h)
                    )
            self.sprites[sprite_id] = s
            self.set_sprite_defaults(obj)

    def draw_outlined_text(self, font, text, fcolor, bcolor):
        """
        Draws a font with a border.
        Returns the resulting surface.
        """

        w, h = font.size(text)
        size = w + 2, h + 2

        s = pygame.Surface(size)
        s.set_colorkey(color.magenta)
        s.fill(color.magenta)

        bg = font.render(text, False, bcolor)
        fg = font.render(text, False, fcolor)

        si = 1
        dirs = [(-1, -1), (-1, 0),
            (-1, 1), (0, -1),
            (0, 1), (1, -1),
            (1, 0), (1, 1)]
        for dx, dy in dirs:
            s.blit(bg, (si + dx * si, si + dy * si))
        s.blit(fg, (si, si))

        return s

    def create_floating_tip_at_xy(self, message, fontcolor, pos, dest):
        """
        Create a game message as a scrolling tooltip.

        """

        bmp = self.draw_outlined_text(self.smallfont, message,
                                        fontcolor, color.black)
        # limit the message position within sane boundaries
        if pos[0] + bmp.get_width() > self.viewport.width:
            pos = (pos[0] - bmp.get_width(), pos[1])
            dest = (dest[0] - bmp.get_width(), dest[1])
        # do not draw off the left
        if pos[0] < 1:
            pos = (2, pos[1])
            dest = (2, dest[1])
        s = Sprite('scoller message', pygame.Rect(pos, bmp.get_size()))
        s.addimage(bmp, 8, 0)
        s.set_position(dest[0], dest[1], 1)
        self.message_sprites.append(s)

    def create_floating_tip(self, message, fontcolor):
        """
        Create a floating tip from the message.
        This calculates the positioning then calls create_floating_tip_at_xy.
        """

        # allow the same message to popup again and again
        if True:
            # avoid overlapping recent messages
            self.last_tip_pos += 14
            pos = self.model.player.getpixelxy()
            # if the tip is too far from the player position
            if abs(pos[1] - self.last_tip_pos) > 60:
                # reset it closer to the player
                self.last_tip_pos = self.model.player.py
            # adjust the position relative to the last position
            pos = (pos[0], self.last_tip_pos)
            dest = (pos[0], pos[1] - 20)
            self.create_floating_tip_at_xy(message, fontcolor, pos, dest)

    def move_sprite(self, event):
        """
        Move the sprite by the event details.
        """

        sprite = self.sprites.get(id(event.obj), None)
        if sprite:
            sprite.set_position(event.obj.x * self.tile_w,
                                event.obj.y * self.tile_h,
                                8)
            return

    def kill_sprite(self, obj):
        """
        Remove a sprite.
        """

        self.sprites.pop(id(obj), None)

    def transmute_sprite(self, event):
        """
        Change a sprite image by object gid.
        """

        event.obj.gid = event.gid
        self.set_sprite_defaults(event.obj)

    def update_viewport(self):
        """
        Auto center the viewport if the player gets too close to any edge.
        """

        px, py = self.model.player.getpixelxy()

        # distance from the edges before we shift (in tiles)
        tolerance = 6 * self.tile_w

        # shrink the viewport to create a buffer so we can detect a shift
        # a few tiles away from the edge
        # if the player is not inside the viewport, center her.
        # this may occur on level warps.
        intolerant_viewport = self.viewport_shift.inflate(
            -tolerance, -tolerance)
        if not intolerant_viewport.collidepoint(px, py):
            self.viewport_shift.center = (px, py)

        # snap to top and left edges
        if self.viewport_shift.left < 0:
            self.viewport_shift.left = 0
        if self.viewport_shift.top < 0:
            self.viewport_shift.top = 0

        # snap to the bottom and right edges
        map_width = self.tmx.width * self.tile_w
        map_height = self.tmx.height * self.tile_h
        if self.viewport_shift.right > map_width:
            self.viewport_shift.right = map_width
        if self.viewport_shift.bottom > map_height:
            self.viewport_shift.bottom = map_height

        # center viewport left if the map fits in snuggly
        if map_width <= self.viewport_shift.width:
            self.viewport_shift.left = (map_width -
                                        self.viewport_shift.width) / 2
        # center viewport top if the map fits in snuggly
        if map_height <= self.viewport_shift.height:
            self.viewport_shift.top = (map_height -
                                        self.viewport_shift.height) / 2

    def shift_viewport(self):
        """
        Shift the actual viewport over time to match our virtual one, giving
        a motion like effect.
        """

        # note that shifts need to happen in multiples of 2 since the viewport
        # shifts by tile size
        x_diff = self.viewport.left - self.viewport_shift.left
        y_diff = self.viewport.top - self.viewport_shift.top
        if x_diff < 0:
            self.viewport.left += 8
        if x_diff > 0:
            self.viewport.left -= 8
        if y_diff < 0:
            self.viewport.top += 8
        if y_diff > 0:
            self.viewport.top -= 8

    def play_music(self, level):
        playlist = [
            'audio/universalnetwork2_real.xm',
            'audio/kbmonkey-ditty.it'
            ]
        pygame.mixer.music.fadeout(1000)
        pygame.mixer.music.load(playlist[0])
        pygame.mixer.music.play()

    def initialize(self):
        """
        Set up the pygame graphical display and loads graphical resources.
        """

        try:

            # set the window size
            self.windowsize = pygame.Rect(0, 0, 600, 600)

            # set the game area, centered in the window
            self.game_area = pygame.Rect(0, 0, 600, 600)
            self.game_area.topleft = (
                self.windowsize.width / 2 - self.game_area.width / 2,
                self.windowsize.height / 2 - self.game_area.height / 2
            )

            # the viewport is a shifting area within the game map
            self.viewport = pygame.Rect(0, 0, 512, 512)
            self.viewport_shift = self.viewport.copy()

            # the on-screen area for drawing game play action
            self.play_area = pygame.Rect((75, 66), self.viewport.size)

            # where player stats are drawn
            self.statsarea = pygame.Rect(200, 22, 400, 40)

            # initialize pygame
            result = pygame.init()
            pygame.font.init()
            self.clock = pygame.time.Clock()
            pygame.display.set_caption('Alive')
            pygame.mouse.set_visible(False)
            self.screen = pygame.display.set_mode(self.windowsize.size)

            # flag that we are done and ready for drawing action
            self.isinitialized = True
            #self.play_music(1)

            # create drawing surfaces which are reused
            self.play_image = pygame.Surface(self.play_area.size)
            self.play_image.set_colorkey(color.magenta)
            self.image = pygame.Surface(self.game_area.size)
            self.image.set_colorkey(color.magenta)

            # holding a key will repeat it
            pygame.key.set_repeat(250, 200)

            # load resources
            self.smallfont = pygame.font.Font('DejaVuSansMono-Bold.ttf', 16)
            self.largefont = pygame.font.Font('DejaVuSansMono-Bold.ttf', 20)
            self.defaultbackground = image.load(
                'images/background.png').convert()
            self.info_screen = image.load(
                'images/info_screen.png').convert()
            self.menubackground = image.load(
                'images/menu.png').convert()
            self.borders = image.load(
                'images/game_borders.png').convert()
            self.borders.set_colorkey(color.magenta)
            self.dialogue_bg = image.load(
                'images/dialog.png').convert()
            self.terminal_bg = image.load(
                'images/terminal.png').convert()
            self.failed_background = image.load(
                'images/level_failed.png').convert()

            # set up all our ui buttons
            self.setup_ui_manager()

            # set up graph objects
            self.graphs['health'] = GraphDisplay(
                fps=30,
                base_color=color.lighter_green,
                title='health',
                font=self.smallfont,
                rect=(180, 23, 140, 40),
                background_image=None
                )

            # set up graph objects
            self.graphs['power'] = GraphDisplay(
                fps=30,
                base_color=color.lighter_blue,
                title='power',
                font=self.smallfont,
                rect=(322, 23, 140, 40),
                background_image=None
                )

        except Exception, e:
            # these lines pose an interesting problem:
            # if the crash message crashes, we go down hard.
            print('\n'.join(CRASH_MESSAGE))
            import traceback
            print('\n' + str(traceback.format_exc()))
            sys.exit(1)

    def show_help_screens(self):
        """
        Queues the help screens as dialogues with transitions.

        """

        help_screen = pygame.image.load('images/help-1.png').convert()

        # add the first help screen
        help_transition = SlideinTransition(
            size=self.game_area.size,
            fps=FPS,
            font=self.smallfont,
            title='',
            inner_bg=help_screen,
            outer_bg=self.image.copy(),
            boxcolor=color.blue,
            pensize=3
            )
        help_transition.waitforkey = True
        self.transition_queue.insert(0, help_transition)

        # add subsequent screens as static (no animation required)
        help_screen2 = pygame.image.load('images/help-2.png').convert()
        help_2 = StaticScreen(
            size=self.game_area.size,
            background_color=color.magenta,
            fps=FPS,
            font=self.largefont,
            words=None,
            word_color=color.green,
            words_x_offset=0,
            words_y_offset=0,
            background=help_screen2
            )
        self.transition_queue.insert(0, help_2)

        # add a closing transition
        close_transition = SlideinTransition(
            size=self.game_area.size,
            fps=FPS,
            font=self.smallfont,
            title='',
            boxcolor=color.blue,
            pensize=3,
            outer_bg=self.image.copy(),
            direction_reversed=True
            )
        self.transition_queue.insert(0, close_transition)

    def show_about_screens(self):
        """
        Shows about screens.

        """

        data = self.model.about_game_data()
        self.post(DialogueEvent(data))
        self.post(StateChangeEvent(STATE_DIALOG))

    def setup_ui_manager(self):
        """
        Setup the UxManager which handles clickable buttons.
        All controls are defined here, they are seperated into groups
        by context equals game states.

        """

        self.ui = ui.UxManager(self.game_area.size,
            image_filename='images/ui.png',
            font=self.largefont,
            click_callback=self.ui_click_event,
            colorkey=color.magenta
            )

        # add main menu buttons
        self.menu_buttons = {}
        # play button
        button = ui.UxMovingButton(
            rect=(-160, 200, 151, 64),
            image_rect=(650, 4, 151, 64),
            code='play',
            hotkey='p',
            enabled=True,
            border_color=None,
            context=STATE_MENU_MAIN
            )
        self.menu_buttons['play'] = button
        self.ui.add(button, hide_hotkey=False)
        button.store_destination(None, None, 'hide')
        button.store_destination(40, None, 'show')
        # options button
        button = ui.UxMovingButton(
            rect=(-200, 280, 151, 64),
            image_rect=(650, 69, 151, 64),
            code='options',
            hotkey='o',
            enabled=True,
            border_color=None,
            context=STATE_MENU_MAIN
            )
        self.menu_buttons['options'] = button
        self.ui.add(button, hide_hotkey=True)
        button.store_destination(None, None, 'hide')
        button.store_destination(40, None, 'show')
        # about button
        button = ui.UxMovingButton(
            rect=(-240, 360, 151, 64),
            image_rect=(650, 134, 151, 64),
            code='about',
            hotkey='a',
            enabled=True,
            border_color=None,
            context=STATE_MENU_MAIN
            )
        self.menu_buttons['about'] = button
        self.ui.add(button, hide_hotkey=True)
        button.store_destination(None, None, 'hide')
        button.store_destination(40, None, 'show')
        # quit button
        button = ui.UxMovingButton(
            rect=(-280, 440, 151, 64),
            image_rect=(650, 199, 151, 64),
            code='quit',
            hotkey='q',
            enabled=True,
            border_color=None,
            context=STATE_MENU_MAIN
            )
        self.menu_buttons['quit'] = button
        self.ui.add(button, hide_hotkey=True)
        button.store_destination(None, None, 'hide')
        button.store_destination(40, None, 'show')
        # saved game buttons
        y_pos = 200
        for n, slot in enumerate(self.model.saved_games_list()):
            button = ui.UxMovingButton(
                rect=(self.game_area.width + 20 + (40 * n), y_pos, 500, 64),
                image_rect=(300, 264, 500, 64),
                code=slot[0],
                hotkey=str(n + 1),
                enabled=True,
                border_color=None,
                context=STATE_MENU_SAVED
                )
            ovl = pygame.Surface((button.rect.size))
            ovl.set_colorkey(color.magenta)
            ovl.fill(color.magenta)
            ovl.blit(self.largefont.render(
                '%s: game slot' % (n + 1), False, color.white),
                (10, 5))
            ovl.blit(self.smallfont.render(slot[1], False,
                color.yellow, color.magenta),
                (10, 30))
            button.overlay = ovl
            self.menu_buttons[button.code] = button
            self.ui.add(button, hide_hotkey=False)
            button.store_destination(None, None, 'hide')
            button.store_destination(60, None, 'show')
            y_pos += 80
        # story buttons
        y_pos = 200
        for n, slot in enumerate(self.model.stories_list()):
            hotkey = chr(ord('a') + n)
            button = ui.UxMovingButton(
                rect=(-500 - (40 * n), y_pos, 500, 64),
                image_rect=(300, 264, 500, 64),
                code='story %s' % (n),
                hotkey=hotkey,
                enabled=True,
                border_color=None,
                context=STATE_MENU_STORIES
                )
            # store the story name in button data
            button.data = slot[0]
            ovl = pygame.Surface((button.rect.size))
            ovl.set_colorkey(color.magenta)
            ovl.fill(color.magenta)
            ovl.blit(self.largefont.render(
                '%s: %s' % (hotkey, slot[0]), False, color.white),
                (10, 5))
            ovl.blit(self.smallfont.render(slot[1], False,
                color.yellow, color.magenta),
                (10, 30))
            button.overlay = ovl
            self.menu_buttons[button.code] = button
            self.ui.add(button, hide_hotkey=False)
            button.store_destination(None, None, 'hide')
            button.store_destination(60, None, 'show')
            y_pos += 80

        # add the "goto home screen" button
        button = ui.UxButton(
            rect=BT_HOME_DST,
            image_rect=BT_HOME_SRC,
            code='goto home',
            hotkey='~',
            enabled=True,
            border_color=None,
            context=STATE_PLAY
            )
        self.ui.add(button, hide_hotkey=True
        )

        # set up info screen tabs (list required)
        tab_states = [STATE_INFO_HOME, STATE_INFO_UPGRADES, STATE_INFO_WINS]

        # add home tab
        tab = ui.UxTabButton(
            rect=TB_HOME_DST,
            image_rect=TB_HOME_SRC,
            code='home tab',
            hotkey='h',
            enabled=True,
            border_color=None,
            context=tab_states,
            group=None
            )
        tab.isclicked = True
        self.ui.add(tab)

        # add upgrades tab
        tab = ui.UxTabButton(
            rect=TB_UPGRADE_DST,
            image_rect=TB_UPGRADE_SRC,
            code='upgrades tab',
            hotkey='u',
            enabled=True,
            border_color=None,
            context=tab_states,
            group=None
            )
        self.ui.add(tab)

        # add wins tab
        tab = ui.UxTabButton(
            rect=TB_WINS_DST,
            image_rect=TB_WINS_SRC,
            code='wins tab',
            hotkey='w',
            enabled=True,
            border_color=None,
            context=tab_states,
            group=None
            )
        self.ui.add(tab)

        # upgrade Install button
        button = ui.UxButton(
            rect=BT_INSTALL_DST,
            image_rect=BT_INSTALL_SRC,
            code='install upgrade',
            hotkey='i',
            enabled=False,
            border_color=None,
            context=STATE_INFO_UPGRADES
            )
        self.ui.add(button, hide_hotkey=True)

        # prepare the default upgrade screen message
        the_message = 'Select an upgrade to view more about it.'
        self.chosen_upgrade_details = self.draw_text(
            lines=[the_message],
            font=self.smallfont,
            antialias=False,
            fontcolor=color.lighter_green,
            background=color.magenta,
            )

    def reposition_upgrade_buttons(self, game_state):
        """
        Reposition the ui buttons that display the player's upgrades.
        This is also done for the upgrades screen, depending on game_state.

        """

        if not self.isinitialized or not self.ui:
            return

        # define a lookup of each upgrade's:
        #   [source image position, in-game hotkey, upgrade screen hotkey]
        upgrade_lookup = {
            alu.REGEN:
                (UG_REGEN_SRC, None, '1'),
            alu.CODE_HARDENING:
                (UG_HARDENING_SRC, None, '2'),
            alu.ASSEMBLY_OPTIMIZE:
                (UG_OPTIMIZE_SRC, None, '3'),
            alu.ECHO_LOOP:
                (UG_ECHO_SRC, 'e', 'e'),
            alu.MAP_PEEK:
                (UG_PEEK_SRC, None, '4'),
            alu.ZAP:
                (UG_ZAP_SRC, 'z', 'z'),
            alu.CODE_FREEZE:
                (UG_FREEZE_SRC, 'f', 'f'),
            alu.PING_FLOOD:
                (UG_PING_SRC, 'p', 'p'),
            alu.FORK_BOMB:
                (UG_FORK_SRC, 'r', 'r'),
            alu.EXPLOIT:
                (UG_EXPLOIT_SRC, 'x', 'x'),
            alu.DESERIALIZE:
                (UG_DEREZ_SRC, 'd', 'd'),
            }

        # first clear any possible elements
        code_list = [u['name'] for u in alu.UPGRADES]
        self.ui.remove_by_code(code_list)

        if game_state == STATE_PLAY:

            butt_x = 14
            butt_y = 69
            butt_size = (57, 45)
            butt_padding = 6

            for upgrade in self.model.player.upgrades:
                # set the screen position
                rect = [butt_x, butt_y]
                rect.extend(butt_size)
                # grab the upgrade lookup data
                lookup = upgrade_lookup.get(upgrade.name, None)
                # sanity check
                if not lookup:
                    trace.error('no upgrade_lookup defined for "%s"' %
                        upgrade.name)
                    # jump to the next item
                    continue
                image_rect = lookup[0]
                # create the ui button
                button = ui.UxButton(
                    rect=rect,
                    image_rect=image_rect,
                    code=upgrade.name,
                    hotkey=lookup[1],
                    enabled=upgrade.enabled,
                    border_color=None,
                    context=STATE_PLAY
                    )
                self.ui.add(button)
                # move to the next available button position
                butt_y += butt_size[1] + butt_padding
            self.update_button_borders()

        elif game_state == STATE_INFO_UPGRADES:
            # position buttons for the upgrade screen

            butt_x = 30
            butt_y = 420
            butt_size = (57, 45)
            butt_padding = 12

            #TODO build a ui label that we can use here to tell
            #   our player if they can choose an upgrade.

            # grab the upgrades the player has
            player_list = [u.name for u in self.model.player.upgrades]
            # grab the available upgrades for this level
            available_list = [u['name']
                for u in alu.from_level(self.model.level_number)]
            # merge the lists
            upgrade_list = sorted(set(player_list + available_list))

            # draw the combined lists
            for name in upgrade_list:
                rect = [butt_x, butt_y]
                rect.extend(butt_size)
                # grab the upgrade lookup data
                lookup = upgrade_lookup.get(name, None)
                # sanity check
                if not lookup:
                    trace.error('no upgrade_lookup defined for "%s"' %
                        name)
                    # jump to the next item
                    continue
                image_rect = lookup[0]
                # installable or upgradable have bright borders.
                border_color = ((name in available_list) and
                                color.green or color.darkest_green)
                button = ui.UxButton(
                    rect=rect,
                    image_rect=image_rect,
                    code=name,
                    hotkey=lookup[2],
                    enabled=True,
                    border_color=border_color,
                    context=STATE_INFO_UPGRADES
                    )
                # set the button's data to indicate if the ugprade is available
                button.data = (name in available_list)
                self.ui.add(button)
                # move to the next available button position
                butt_x += butt_size[0] + butt_padding
                if (butt_x > self.play_area.width - butt_padding):
                    butt_y += butt_size[1] + butt_padding
                    butt_x = 30

    def update_button_borders(self):
        """
        Update ui button borders to match their state.

        """

        for upgrade in self.model.player.upgrades:
            button = self.ui.get_by_code(upgrade.name)
            if button:
                # outline the button depending if it is active or cooling
                new_color = None
                if upgrade.is_active:
                    new_color = color.green
                elif upgrade.is_cooling:
                    new_color = color.yellow
                #button.enabled = upgrade.ready
                button.border_color = new_color

    def ui_click_event(self, context, ux):
        """
        Called on a ui element click or hotkey press.
        check ux.code for the item involved.

        """

        trace.write('pressed button %s' % ux.code)
        tab_states = [STATE_INFO_HOME, STATE_INFO_UPGRADES, STATE_INFO_WINS]

        if context == STATE_PLAY:
            if ux.code == 'goto home':
                self.post(StateChangeEvent(self.last_info_state))
            else:
                self.model.use_upgrade(ux.code)
                self.update_button_borders()

        if context == STATE_MENU_MAIN:
            if ux.code == 'play':
                if self.model.game_in_progress:
                    self.post(StateChangeEvent(STATE_PLAY))
                else:
                    self.post(StateChangeEvent(STATE_MENU_SAVED))
            elif ux.code == 'about':
                self.show_about_screens()
            elif ux.code == 'options':
                pass
            elif ux.code == 'quit':
                self.post(QuitEvent())

        elif context == STATE_MENU_SAVED:
            if ux.code.startswith('load game'):
                self.model.game_slot = int(ux.code.split()[-1])
                trace.write('save game slot %s selected' %
                    self.model.game_slot)
                self.post(StateChangeEvent(None))
                self.model.begin_game()
            elif ux.code.startswith('new game'):
                self.model.game_slot = int(ux.code.split()[-1])
                trace.write('save game slot %s selected' %
                    self.model.game_slot)
                self.post(StateChangeEvent(STATE_MENU_STORIES))

        elif context == STATE_MENU_STORIES:
            if ux.code.startswith('story'):
                self.model.story_name = ux.data
                trace.write('selected story "%s"' % (self.model.story_name))
                self.post(StateChangeEvent(None))
                self.post(StateChangeEvent(None))
                self.model.begin_game()

        # handle info screen menus
        if context in tab_states:
            if ux.code == 'home tab':
                self.last_info_state = STATE_INFO_HOME
                self.post(StateSwapEvent(STATE_INFO_HOME))
            elif ux.code == 'upgrades tab':
                self.last_info_state = STATE_INFO_UPGRADES
                self.post(StateSwapEvent(STATE_INFO_UPGRADES))
            elif ux.code == 'wins tab':
                self.last_info_state = STATE_INFO_WINS
                self.post(StateSwapEvent(STATE_INFO_WINS))
            elif ux.code == 'install upgrade':
                if self.chosen_upgrade:
                    status = self.model.install_upgrade(self.chosen_upgrade)
                    if status:
                        self.chosen_upgrade = None
                        self.chosen_upgrade_details = None
                        self.ui.get_by_code('install upgrade').enabled = False
                        self.chosen_upgrade_details = self.draw_text_block(
                            status, self.smallfont, False, color.yellow)
            else:
                # grab the upgrade data and create a details screen for it
                data = alu.from_name(ux.code)
                # enable button if upgrade available on level
                if self.model.upgrades_available > 0:
                    butt = self.ui.get_by_code('install upgrade')
                    butt.enabled = True if data and ux.data else False
                # draw the upgrade info surface: name, description and version.
                if data:
                    # store the code of the chosen upgrade
                    self.chosen_upgrade = ux.code
                    # draw a name and version image
                    v_string = ' is not installed'
                    plr_upgrade = self.model.player_upgrade(ux.code)
                    if plr_upgrade:
                        v_string = ' version: %s' % (plr_upgrade.version)
                        data = plr_upgrade
                    data_lines = [
                        '%s%s' % (data.name.upper(), v_string),
                        'reach: %s' % (data.reach),
                        'targets: %s' % (data.max_targets),
                        'cost: %s' % (data.cost),
                        'damage multiplier: %s' % (data.damage_multiplier),
                        'duration: %s' % (data.duration),
                        'cooldown: %s' % (data.cooldown),
                        '',
                        ]
                    name_img = self.draw_text(
                        lines=data_lines,
                        font=self.smallfont,
                        antialias=False,
                        fontcolor=color.lighter_green,
                        background=color.magenta,
                        )
                    name_h = name_img.get_height()
                    desc_img = self.draw_text_block(
                        text=data.description,
                        font=self.smallfont,
                        antialias=False,
                        fontcolor=color.lighter_green,
                        colorize=None,
                        background=color.magenta,
                        wrap_width=50,
                        )
                    # compose the final image from all the smaller info bitmaps
                    w = desc_img.get_width()
                    h = desc_img.get_height() + name_img.get_height()
                    self.chosen_upgrade_details = pygame.Surface((w, h))
                    self.chosen_upgrade_details.set_colorkey(color.magenta)
                    self.chosen_upgrade_details.fill(color.magenta)
                    self.chosen_upgrade_details.blit(name_img, (0, 0))
                    self.chosen_upgrade_details.blit(desc_img, (0, name_h))

# locations of ui.png images
# goto home button
BT_HOME_SRC = (228, 170, 83, 34)
BT_HOME_DST = (500, 26, 0, 0)
# home tabs
BT_INSTALL_SRC = (228, 102, 83, 34)
BT_INSTALL_DST = (40, 70, 0, 0)
TB_HOME_SRC = (228, 0, 83, 34)
TB_HOME_DST = (12, 12, 0, 0)
TB_UPGRADE_SRC = (228, 34, 152, 34)
TB_UPGRADE_DST = (97, 12, 0, 0)
TB_WINS_SRC = (228, 68, 74, 34)
TB_WINS_DST = (251, 12, 0, 0)
# upgrades
UG_REGEN_SRC = (0, 0, 57, 45)
UG_HARDENING_SRC = (0, 45, 57, 45)
UG_OPTIMIZE_SRC = (0, 90, 57, 45)
UG_ECHO_SRC = (0, 135, 57, 45)
UG_PEEK_SRC = (0, 180, 57, 45)
UG_ZAP_SRC = (0, 225, 57, 45)
UG_FREEZE_SRC = (0, 270, 57, 45)
UG_PING_SRC = (0, 315, 57, 45)
UG_FORK_SRC = (0, 360, 57, 45)
UG_EXPLOIT_SRC = (0, 405, 57, 45)
UG_DEREZ_SRC = (0, 450,  57, 45)
