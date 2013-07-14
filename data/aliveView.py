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

    map_image (Surface):
        A prerendered image of the level map static tiles that do not need
        to animate. It may be larger than our play area, and we only draw
        the map area under our viewport.

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
        self.map_image = None
        self.play_image = None
        #TODO remove statscanvas ?
        self.statscanvas = None
        self.play_area = None
        self.statsarea = None
        self.viewport = None
        self.windowsize = None
        self.sprites = {}
        self.scrollertexts = None
        self.messages = []
        self.gamefps = 30
        self.last_tip_pos = 0
        self.transition_queue = []
        self.ui = None
        self.chosen_upgrade = None
        self.chosen_upgrade_details = None
        self.last_info_state = STATE_INFO_HOME

    @property
    def tmx(self):
        """
        A virtual property to access the level data on the model.
        """

        return self.model.level.tmx

    @property
    def tile_w(self):
        """
        A virtual property to access the tile width.
        """

        return self.tmx.tile_width

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

    def notify(self, event):
        """
        Called by an event in the message queue.
        """

        try:
            if isinstance(event, TickEvent):
                self.render()
                self.clock.tick(self.gamefps)

            elif isinstance(event, CharacterMovedEvent):
                self.move_sprite(event)

            elif isinstance(event, PlayerMovedEvent):
                self.update_viewport()
                self.update_button_borders()

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

            elif isinstance(event, InputEvent):
                if self.ui:
                    if event.char:
                        self.ui.click(event.char)
                    else:
                        self.ui.unclick()

            elif (isinstance(event, StateChangeEvent) or
                    isinstance(event, StateSwapEvent)):
                if self.ui:
                    model_state = self.model.state.peek()
                    self.reposition_upgrade_buttons(model_state)
                    trace.write('set ui context to game state %s' %
                        model_state)
                    self.ui.set_context(model_state)

                if event.state == STATE_HELP:
                    self.show_help_screens()

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

        # reset the main image by painting a background over it
        self.image.blit(self.defaultbackground, (0, 0))

        if state == STATE_INTRO:
            pass

        elif state == STATE_MENU:
            self.draw_menu()

        elif state in (STATE_INFO_HOME, STATE_INFO_UPGRADES, STATE_INFO_WINS):
            self.draw_info_screen(state)

        elif state in (STATE_PLAY, STATE_GAMEOVER):

            self.play_image.fill(color.magenta)
            self.draw_borders()
            self.draw_player_stats()
            self.draw_sprites()
            self.draw_target()
            self.draw_fog()
            self.draw_scroller_text()

            if state == STATE_GAMEOVER:
                #TODO Overlay a game over message.
                pass

            # merge play_image into our main image at the relevant position
            self.image.blit(self.play_image, self.play_area)

        # NOTE: no need to handle drawing for HELP or DIALOGUE states
        #       since those use the TransitionBase, which draws itself below.

        # update the ui and draw it to the main image
        self.ui.update()
        self.image.blit(self.ui.image, (0, 0))

        # apply any transitions (including dialogues and help screens)
        if self.transition:
            self.transition.update(pygame.time.get_ticks())
            self.image.blit(self.transition.image, (0, 0))
        self.step_transitions()

        # finally draw our composed image onto the screen
        self.screen.blit(self.image, self.game_area)
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
        level_file = os.path.basename(self.model.level.filename)
        image_filename = '/tmp/anims-%s.png' % level_file
        fnt = self.largefont.render('Alive animations', False, color.green)
        title_width = fnt.get_width()
        surf.blit(fnt, (10, 10))
        fnt = self.smallfont.render(level_file, False, color.white)
        surf.blit(fnt, (40 + title_width, 20))

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

        ## apply animation defs
        #if anims and sprite:
            #obj.frames = map(int, anims['frames'])
            #obj.fps = anims.as_float('fps')
            #obj.loop = anims.as_int('loop')

    def draw_menu(self):
        """
        Draw the main menu.
        """

        self.image.blit(self.menubackground, (0, 0))

    def draw_info_screen(self, game_state):
        """
        Draw the player info screen.
        """

        self.image.blit(self.info_screen, (0, 0))

        if game_state == STATE_INFO_HOME:
            # draw a portion of the playscreen
            snap_rect = (
                        self.tile_w * (self.model.player.x - 2),
                        self.tile_h * (self.model.player.y - 2),
                        self.tile_w * 5,
                        self.tile_h * 5,
                        )
            snap_dest = (28, 122)
            self.image.blit(self.play_image, snap_dest, snap_rect)
            pygame.draw.rect(self.image, color.blue,
                (snap_dest[0], snap_dest[1], snap_rect[2], snap_rect[3]), 2)
            # a helpful message
            pix = self.largefont.render(
                'you are alive!', False, color.message)
            self.image.blit(pix, (28, 75))
            # column of stats titles
            titles = 'turn\nlevel\nhealth\npower\nattack\nspeed\nview'
            pix = self.draw_text_block(
                titles, self.largefont, False, color.desaturated_cyan)
            self.image.blit(pix, (370, 70))
            values = '%s\n%s\n%s\n%s\n%s\n%s\n%s' % (
                self.model.turn,
                self.model.level.number,
                self.model.player.health,
                self.model.player.power,
                self.model.player.attack,
                self.model.player.speed,
                self.model.player.view_range,
                )
            pix = self.draw_text_block(
                values, self.largefont, False, color.desaturated_yellow)
            self.image.blit(pix, (490, 70))
            # recent messages
            if self.messages:
                pix = self.draw_text(
                    self.messages, self.smallfont, False, color.message)
                self.image.blit(pix, (28, 290))

        elif game_state == STATE_INFO_UPGRADES:
            # display the amount of upgrades the player can install
            amt = self.model.upgrades_available
            if amt == 0:
                status = 'You cannot install any upgrades at this time.'
            elif amt == 1:
                status = 'You can install 1 upgrade.'
            else:
                status = 'You can install %s upgrades.' % amt
            pix = self.draw_text([status], self.smallfont, False, color.white)
            self.image.blit(pix, (140, 65))
            # show chosen upgrade details
            if self.chosen_upgrade_details:
                self.image.blit(self.chosen_upgrade_details, (140, 85))

    def draw_target(self):
        """
        Draw a selection around the targeted object.

        """

        target = self.model.target_object
        if target:
            sprite = self.sprites.get(id(target), None)
            if sprite:
                pygame.draw.rect(self.play_image,
                                color.target_selection, sprite.rect, 1)

    def draw_sprites(self):
        """
        Draw the play area: level tiles and objects.
        """

        # start by drawing the level map on our play image.
        self.play_image.blit(self.map_image, (0, 0), self.viewport)
        ticks = pygame.time.get_ticks()
        # for each sprite in our viewport range
        for x, y in rlhelper.remap_coords(
                self.viewport, self.tile_w, self.tile_h):
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
                        # because our play_image is only the size of the screen
                        # we accommodate sprite positions, which are relative
                        # to entire map, by subtracting the viewport location.
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
                    self.play_image.blit(unseen_sprite, new_rect)
                # seen but out of range
                elif seen == 1:
                    self.play_image.blit(fog_sprite, new_rect)

    def draw_scroller_text(self):
        """
        Draw any scrolling text sprites.
        """

        if not self.scrollertexts:
            return
        ticks = pygame.time.get_ticks()
        for sprite in self.scrollertexts:
            if sprite.done:
                self.scrollertexts.remove(sprite)
            else:
                sprite.update(ticks)
                self.play_image.blit(sprite.image, sprite.rect)

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
                        fps=self.gamefps,
                        font=self.smallfont,
                        title='',
                        direction_reversed=True
                        )
        self.transition_queue.insert(0, open_transition)

    def queue_dialogue(self, dialogue):
        """
        Queue a dialogue for display.

        """

        # we only need one slide-in transition for many screens.
        terminal_slidein_added = False

        # a dialogue may contain multiple screens. Keep this in mind.
        for dialogue_screen in dialogue.keys():

            datas = dialogue[dialogue_screen]

            # we may add other transitions depending on the screen "type".
            # for now we only have terminals.
            if datas['type'] in ('story', 'terminal'):

                # Start with a Slide-in Transition
                if not terminal_slidein_added:
                    terminal_slidein_added = True
                    new_transition = SlideinTransition(
                        size=self.game_area.size,
                        fps=self.gamefps,
                        font=self.smallfont,
                        title='connecting . . .',
                        inner_bg=self.dialoguebackground,
                        outer_bg=self.image.copy(),
                        )
                    self.transition_queue.insert(0, new_transition)

                # Follow up with a Terminal Printer Transition
                text_color = getattr(color, datas['color'])
                words = datas['datas']
                words = self.wrap_text(words, 25)
                new_transition = TerminalPrinter(
                    size=self.game_area.size,
                    background_color=color.magenta,
                    fps=self.gamefps,
                    font=self.largefont,
                    words=words,
                    word_color=text_color,
                    words_x_offset=80,
                    words_y_offset=80,
                    background=self.dialoguebackground
                    )
                self.transition_queue.insert(0, new_transition)

        # add a closing transition
        close_transition = SlideinTransition(
                        size=self.game_area.size,
                        fps=self.gamefps,
                        font=self.smallfont,
                        title='',
                        inner_bg=self.dialoguebackground,
                        outer_bg=self.image.copy(),
                        direction_reversed=True
                        )
        self.transition_queue.insert(0, close_transition)

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
                self.evManager.Post(StateChangeEvent(None))

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

    def draw_player_stats(self):
        """
        Draw the player stats onto statscanvas.
        """

        def _colorband(ratio):
            # gradient green for healthy and red for hurt
            if ratio > 0.8:
                return color.green
            elif ratio > 0.5:
                return color.yellow
            else:
                return color.red

        self.statscanvas.fill(color.magenta)

        player = self.model.player

        # health
        xposition = 0
        yposition = 0
        health = 0
        if player.max_health > 0:
            health = player.health / player.max_health
        mana = 0
        if player.max_power > 0:
            mana = player.power / player.max_power

        phealth = self.smallfont.render(
                                str(player.health) + ' health',
                                False,
                                _colorband(health))
        self.statscanvas.blit(phealth, (xposition, yposition))
        # mana
        pmana = self.smallfont.render(
                                str(player.power) + ' mana',
                                False,
                                _colorband(mana))
        self.statscanvas.blit(
            pmana, (xposition + (phealth.get_width() * 1.5), yposition))
        self.image.blit(self.statscanvas, self.statsarea)

    def draw_game_messages(self):
        """
        Draw recent game messages.
        """

        messagebmp = self.draw_text(
                    self.messages[-8:],
                    self.smallfont,
                    False,
                    (0, 20, 0),
                    (0, 20, 0))
        self.screen.blit(messagebmp, (0, 0))
        # cull
        self.messages = self.messages[-20:]

    def wrap_text(self, message, maxlength):
        """
        Takes a long string and returns a list of lines.
        maxlength is the characters per line.
        """

        # first split any newlines
        inlines = message.split('\n')
        outlines = []
        # chop up any lines longer than maxlength
        for line in inlines:
            while True:
                maxpos = line.find(' ', maxlength)
                if maxpos > 0:
                    # split this line into smaller chunks
                    outlines.append(line[:maxpos].strip())
                    line = line[maxpos:].strip()
                else:
                    if len(line) == 0:
                        line = ' '
                    outlines.append(line)
                    break
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
            brokenText = text.replace("\r\n", " ")
            brokenText = brokenText.replace("\r", " ").replace("\n", " ")
            brokenText = textwrap.wrap(brokenText, wrap_width)
        else:
            brokenText = text.replace("\r\n", "\n").replace("\r", "\n")
            brokenText = brokenText.split("\n")
        return self.draw_text(
                        brokenText,
                        font,
                        antialias,
                        fontcolor,
                        colorize,
                        background
                        )

    def draw_map_image(self):
        """
        Prerender the level onto an image for easier use.
        This only draws non-animation map tiles.

        """

        self.map_image = pygame.Surface(
            (self.tmx.px_width, self.tmx.px_height))
        self.map_image.set_colorkey(color.magenta)
        self.map_image.fill(color.magenta)
        for y in range(self.tmx.height):
            for x in range(self.tmx.width):
                for layer in self.tmx.tilelayers:
                    gid = layer.at((x, y))
                    tile = self.tsp[gid]
                    if tile:
                        self.map_image.blit(tile,
                            (x * self.tile_w,
                            y * self.tile_h))

    def load_level(self):
        """
        Load the map data and prepare some resources for drawing the game.
        Note: we only support the first tilset as defined in the self.tmx.
        """

        story = self.model.story
        tilesetfile = os.path.join(story.path, self.tmx.tilesets[0].source)
        self.tsp = TilesetParser(
                                tilesetfile,
                                (self.tile_w, self.tile_h),
                                color.magenta
                                )
        self.draw_map_image()

    def set_sprite_defaults(self, obj):
        """
        Apply sprite settings to an object from the story animations setting.
        """

        # set defaults
        defaults = {'frames': [], 'fps': 0, 'loop': 0}
        [setattr(obj, k, v) for k, v in defaults.items()]

        # grab animation defs
        anims = self.model.story.animations(obj.gid)

        # grab our sprite
        sprite = self.sprites.get(id(obj), None)

        # apply animation defs
        if anims and sprite:
            obj.frames = map(int, anims['frames'])
            obj.fps = anims.as_float('fps')
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

        for obj in self.model.objects:
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

        if not self.scrollertexts:
            self.scrollertexts = pygame.sprite.Group()
            self.scrollertexts.empty()

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
        s = MovingSprite('',
                        pygame.Rect(pos, bmp.get_size()),
                        dest,
                        1,
                        self.scrollertexts)
        s.addimage(bmp, 10, 0)

    def create_floating_tip(self, message, fontcolor):
        """
        Create a floating tip from the message.
        This calculates the positioning then calls create_floating_tip_at_xy.
        """

        # allow the same message to popup again and again
        if True:
            self.messages.append(message)
            self.messages = self.messages[-12:]
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
            sprite.rect.topleft = ((event.obj.x * self.tile_w),
                                    (event.obj.y * self.tile_h))
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

        # make some values easier to read
        px, py = self.model.player.getpixelxy()
        vp = self.viewport

        # how close to edges we need to be to shfit the view (in tiles)
        A = 4 * self.tile_w
        B = 4 * self.tile_h

        x_min, y_min = (vp.left + A, vp.top + B)
        x_max, y_max = (vp.left + vp.width - A, vp.top + vp.height - B)

        if px < x_min:
            self.viewport = self.viewport.move(-A, 0)
        if px > x_max:
            self.viewport = self.viewport.move(A, 0)
        if py < y_min:
            self.viewport = self.viewport.move(0, -A)
        if py > y_max:
            self.viewport = self.viewport.move(0, A)

        # if the player is not inside the viewport, center her.
        # this may occur on level warps.
        if not self.viewport.collidepoint(px, py):
            self.viewport.center = (px, py)

        # snap to top-left edges
        if self.viewport.left < 0:
            self.viewport.left = 0
        if self.viewport.top < 0:
            self.viewport.top = 0
        # and the bottom-right edges
        if self.viewport.right > self.tmx.width * self.tile_w:
            self.viewport.right = self.tmx.width * self.tile_w
        if self.viewport.bottom > self.tmx.height * self.tile_h:
            self.viewport.bottom = self.tmx.height * self.tile_h

    def adjust_viewport(self, event):
        """

        """

        pass

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
            self.statscanvas = pygame.Surface(self.statsarea.size)
            self.statscanvas.set_colorkey(color.magenta)
            self.image = pygame.Surface(self.game_area.size)
            self.image.set_colorkey(color.magenta)

            # holding a key will repeat it
            pygame.key.set_repeat(200, 150)

            # load resources
            self.smallfont = pygame.font.Font('UbuntuMono-B.ttf', 16)
            self.largefont = pygame.font.Font('bitwise.ttf', 30)
            self.button_font = pygame.font.Font('UbuntuMono-B.ttf', 24)
            self.defaultbackground = image.load(
                'images/background.png').convert()
            self.info_screen = image.load(
                'images/info_screen.png').convert()
            self.menubackground = image.load('images/menu.png').convert()
            self.borders = image.load('images/game_borders.png').convert()
            self.borders.set_colorkey(color.magenta)
            self.dialoguebackground = image.load('images/dialog.png').convert()

            # set up all our ui buttons
            self.setup_ui_manager()

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
            fps=self.gamefps,
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
        help_2 = StaticScreen(
            size=self.game_area.size,
            background_color=color.magenta,
            fps=self.gamefps,
            font=self.largefont,
            words=None,
            word_color=color.green,
            words_x_offset=0,
            words_y_offset=0,
            background=help_screen
            )
        self.transition_queue.insert(0, help_2)

        # add a closing transition
        close_transition = SlideinTransition(
            size=self.game_area.size,
            fps=self.gamefps,
            font=self.smallfont,
            title='',
            boxcolor=color.blue,
            pensize=3,
            outer_bg=self.image.copy(),
            direction_reversed=True
            )
        self.transition_queue.insert(0, close_transition)

    def setup_ui_manager(self):
        """
        Setup the UxManager which handles clickable buttons.
        All controls are defined here, they are seperated into groups
        by context equals game states.

        """

        self.ui = ui.UxManager(self.game_area.size,
            image_filename='images/ui.png',
            font=self.button_font,
            click_callback=self.ui_click_event,
            colorkey=color.magenta
            )

        # add the "goto home screen" button
        button = ui.UxButton(
            rect=BT_HOME_DST,
            image_rect=BT_HOME_SRC,
            code='goto home',
            hotkey='@',
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
        the_message = "Select an upgrade to view more about it. "
        self.chosen_upgrade_details = self.draw_text_block(
            the_message,
            self.smallfont,
            False,
            color.cyan,
            colorize=None,
            background=None,
            wrap_width=60
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
            butt_y = 240
            butt_size = (57, 45)
            butt_padding = 24

            #TODO build a ui label that we can use here to tell
            #   our player if they can choose an upgrade.

            # grab the upgrades the player has
            player_list = [u.name for u in self.model.player.upgrades]
            # grab the available upgrades for this level
            available_list = [u['name']
                for u in alu.from_level(self.model.level.number)]
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
                button.enabled = upgrade.ready
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
                self.evManager.Post(StateChangeEvent(self.last_info_state))
            else:
                self.model.use_upgrade(ux.code)
                self.update_button_borders()

        # handle info screen menus
        if context in tab_states:
            if ux.code == 'home tab':
                self.last_info_state = STATE_INFO_HOME
                self.evManager.Post(StateSwapEvent(STATE_INFO_HOME))
            elif ux.code == 'upgrades tab':
                self.last_info_state = STATE_INFO_UPGRADES
                self.evManager.Post(StateSwapEvent(STATE_INFO_UPGRADES))
            elif ux.code == 'wins tab':
                self.last_info_state = STATE_INFO_WINS
                self.evManager.Post(StateSwapEvent(STATE_INFO_WINS))
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
                if data:
                    self.chosen_upgrade = ux.code
                    self.chosen_upgrade_details = self.draw_text_block(
                            '%s: %s' % (
                            ux.code.upper(),
                            data.description),
                        self.smallfont,
                        False,
                        color.cyan,
                        colorize=None,
                        background=None,
                        wrap_width=50
                        )

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
