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
import pygame
from pygame import image
from pygame.locals import *
import trace
import color
import const
import aliveModel
from eventmanager import *
from tmxparser import TMXParser
from tmxparser import TilesetParser

# tile id of seen fog overlay
FOG_GID = 16

# tile id of unseen tiles
UNSEEN_GID = 24


class GraphicalView(object):
    """
    Draws the model state onto the screen.
    """

    def __init__(self, evManager, model):
        """
        evManager controls Post()ing and notify()ing events.
        model gives us a strong reference to what we need to draw.

        Attributes:
        isinitialized (bool): pygame is ready to draw.
        screen (Surface): the screen surface.
        clock (Clock): keeps the fps constant.
        smallfont (Font): a small font.
        largefont (Font): a larger font.
        levelcanvas (Surface): a rendering of the level tiles.
        objectcanvas (Surface): a rendering of the level objects.
        statscanvas (Surface): a rendering of player and level stats.
        playarea (Rect): location on screen to draw gameplay.
        statsarea (Rect): area to draw player stats.
        viewport (Rect): which portion of the game map we are looking at.
        allsprites (Group): contains all animated, movable objects in play.
        visible_sprites (Group): only contains sprites visible to the player.
        sprite_lookup (Dict): a sprite name-value lookup.
        helpimages (Surface): stores the F1 help screens.
        transition (TransitionBase): current animated screen transition.
        messages (list): list of recent game messages.

        Note: The viewport defines which area of the level we see as the
        play area. a smaller viewport will render correctly, as long as
        we move it with the player character via the ShiftViewportEvent.
        It takes a tuple of (x,y) offset to move, by index, not pixels,
        where index equals the number of tiles to shift.
        """

        self.evManager = evManager
        evManager.RegisterListener(self)
        self.model = model
        self.isinitialized = False
        self.screen = None
        self.clock = None
        self.smallfont = None
        self.largefont = None
        self.levelcanvas = None
        self.objectcanvas = None
        self.statscanvas = None
        self.playarea = None
        self.statsarea = None
        self.viewport = None
        self.windowsize = None
        self.allsprites = None
        self.visible_sprites = None
        self.sprite_lookup = {}
        self.scrollertexts = None
        self.helpimages = None
        self.transition = None
        self.messages = [''] * 20
        self.gamefps = 30
        self.last_tip_pos = 0
        self.transition_queue = []

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
                self.update_visible_sprites()
                self.update_viewport()
            elif isinstance(event, MessageEvent):
                self.create_floating_tip(event.message,
                    event.fontcolor and event.fontcolor or color.text)
            elif isinstance(event, KillCharacterEvent):
                self.kill_sprite(event.character)
                self.messages.append('The %s dies' % (event.character.name))
            elif isinstance(event, UpdateObjectGID):
                self.transmute_sprite(event)
            elif isinstance(event, DialogueEvent):
                self.queue_dialogue(event.dialogue)
            elif isinstance(event, NextLevelEvent):
                self.load_level()
                self.create_sprites()
            #elif isinstance(event, ShiftViewportEvent):
                #self.adjust_viewport(event)
            elif isinstance(event, InitializeEvent):
                self.initialize()
            elif isinstance(event, QuitEvent):
                self.isinitialized = False
                pygame.quit()
            elif isinstance(event, DebugEvent):
                if event.request_type == 'animation cheatsheet':
                    self.draw_animations_cheatsheet()
        except Exception, e:
            # we explicitly catch Exception, since sys.exit() will throw
            # a SystemExit, and we want that one to not catch here.
            # That means we drop to the terminal if sys.exit() is used.
            self.evManager.Post(CrashEvent())

    def widgetclick(self, context, code):
        """
        A handler that gets called by UI widgets.
        #TODO ui widget implementation
        """

        pass

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
            if state == aliveModel.STATE_CRASH:
                somewords = self.draw_text(const.CRASH_MESSAGE,
                                            self.smallfont,
                                            False,
                                            color.yellow)
                self.screen.blit(somewords, (0, 0))
                pygame.display.flip()
                return
        except Exception, e:
            # these lines pose an interesting problem:
            # if the crash message crashes, we go down hard.
            print('\n'.join(const.CRASH_MESSAGE))
            import traceback
            print('\n' + str(traceback.format_exc()))
            sys.exit(1)

        self.screen.blit(self.defaultbackground, (0, 0))

        if state == aliveModel.STATE_INTRO:
            pass

        elif state == aliveModel.STATE_MENU:
            self.draw_menu()

        elif state == aliveModel.STATE_DIALOG:
            self.draw_borders()
            self.draw_player_stats()
            self.draw_sprites()
            self.draw_dialogue()

        elif state in (aliveModel.STATE_PLAY, aliveModel.STATE_GAMEOVER):
            self.draw_borders()
            self.draw_player_stats()
            self.draw_sprites()
            self.draw_scroller_text()

            if state == aliveModel.STATE_GAMEOVER:
                #TODO Overlay a game over message.
                pass

        elif state == aliveModel.STATE_HELP:
            if not self.helpimages:
                self.helpimages = pygame.image.load(
                    'images/help-1.png').convert()
            self.screen.blit(self.helpimages, (0, 0))

        if self.transition:
            self.transition.update(pygame.time.get_ticks())
            self.screen.blit(self.transition.image, (0, 0))

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
        tmx = self.model.level.tmx
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
            fnt = self.smallfont.render(str(gid) + ': ' + key, False, color.white)
            surf.blit(fnt, (x + tmx.tile_width, y))
            this_width = x + tmx.tile_width + fnt.get_width()
            if this_width > column_width:
                column_width = this_width
            y += tmx.tile_height * 1.5

            if y > size[1] - tmx.tile_height:
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

        self.screen.blit(self.menubackground, (0, 0))

    def draw_sprites(self):
        """
        Draw the play area: level tiles and objects.
        """

        self.screen.blit(self.levelcanvas, self.playarea, self.viewport)
        self.objectcanvas.fill(color.magenta)
        self.allsprites.update(pygame.time.get_ticks())
        self.visible_sprites.draw(self.objectcanvas)
        self.draw_fog()
        self.screen.blit(self.objectcanvas, self.playarea, self.viewport)

    def draw_fog(self):
        """
        Overlay fog on the level for that which is out of player view.
        """

        unseen_sprite = self.tsp[UNSEEN_GID]
        fog_sprite = self.tsp[FOG_GID]

        tmx = self.model.level.tmx
        for y in range(0, tmx.height):
            for x in range(0, tmx.width):
                # lookup list of which positions has been seen
                # and overlay those with FOG_GID, the rest with UNSEEN_GID
                seen = self.model.level.matrix['seen'][x][y]

                # not yet seen
                if seen == 0:
                    self.objectcanvas.blit(unseen_sprite,
                                    (x * tmx.tile_width, y * tmx.tile_height))
                # seen but out of range
                elif seen == 1:
                    self.objectcanvas.blit(fog_sprite,
                                    (x * tmx.tile_width, y * tmx.tile_height))

    def draw_scroller_text(self):
        """
        Draw any scrolling text sprites.
        """

        if self.scrollertexts:
            self.scrollertexts.update(pygame.time.get_ticks())
            self.scrollertexts.draw(self.objectcanvas)
            self.screen.blit(self.objectcanvas, self.playarea, self.viewport)
            for sprite in self.scrollertexts:
                if sprite.done:
                    self.scrollertexts.remove(sprite)

    def draw_dialogue(self):
        """
        Step any queued transitions:

         1. if there is no transition:
               create one from a queue
         2. if there is a transition:
               if it is not done:
                   return
               if it is waiting for a key:
                   return
               else:
                   create one from a queue

        """

        if self.transition:
            if not self.transition.done:
                return
            if self.transition.waitforkey:
                return

        # create one from a queue
        if self.transition_queue:
            self.transition = self.transition_queue.pop()
        else:
            self.evManager.Post(StateChangeEvent(None))

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
                    self.transition_queue.insert(0,
                                            SlideinTransition(
                                            self.windowsize,
                                            color.magenta,
                                            self.gamefps,
                                            self.smallfont,
                                            'connecting . . .',
                                            self.dialoguebackground))

                # Follow up with a Terminal Printer Transition
                text_color = getattr(color, datas['color'])
                words = datas['datas']
                words = self.wrap_text(words, 25)
                self.transition_queue.insert(0,
                                        TerminalPrinter(
                                        self.windowsize,
                                        color.magenta,
                                        self.gamefps,
                                        self.largefont,
                                        words,
                                        text_color,
                                        80, 80,
                                        self.dialoguebackground))

    def next_dialogue(self):
        """
        Move to the next dialogue line
        """

        self.transition = None

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

        self.screen.blit(self.borders, (0, 0))

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
        phealth = self.smallfont.render(
                                str(player.health) + ' health',
                                False,
                                _colorband(player.health / player.maxhealth))
        self.statscanvas.blit(phealth, (xposition, yposition))
        # mana
        pmana = self.smallfont.render(
                                str(player.mana) + ' mana',
                                False,
                                _colorband(player.mana / player.maxmana))
        self.statscanvas.blit(
            pmana, (xposition + (phealth.get_width() * 1.5), yposition))
        self.screen.blit(self.statscanvas, self.statsarea)

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
            colorize=None, background=None):
        """ renders block text with newlines. """
        brokenText = text.replace("\r\n", "\n").replace("\r", "\n")
        return self.draw_text(
                        brokenText.split("\n"),
                        font,
                        antialias,
                        fontcolor,
                        colorize,
                        background
                        )

    def load_level(self):
        """
        Prepare the View's canvases from the current model map data.
        Note: we only support the first tilset as defined in the tmx.
        """

        tmx = self.model.level.tmx
        story = self.model.story
        tilesetfile = os.path.join(story.path, tmx.tilesets[0].source)
        self.tsp = TilesetParser(
                                tilesetfile,
                                (tmx.tile_width, tmx.tile_height),
                                color.magenta
                                )

        self.levelcanvas = pygame.Surface((tmx.px_width, tmx.px_height))
        self.levelcanvas.set_colorkey(color.magenta)
        self.levelcanvas.fill(color.magenta)
        self.objectcanvas = pygame.Surface(self.levelcanvas.get_size())
        self.objectcanvas.set_colorkey(color.magenta)
        self.statscanvas = pygame.Surface(self.statsarea.size)
        self.statscanvas.set_colorkey(color.magenta)
        for y in range(tmx.height):
            for x in range(tmx.width):
                for layer in tmx.tilelayers:
                    gid = layer.at((x, y))
                    tile = self.tsp[gid]
                    if tile:
                        self.levelcanvas.blit(tile,
                                    (x * tmx.tile_width, y * tmx.tile_height))

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
        sprite = self.sprite_lookup[id(obj)]

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

        if not self.allsprites:
            self.allsprites = pygame.sprite.Group()
        if not self.visible_sprites:
            self.visible_sprites = pygame.sprite.Group()
        self.allsprites.empty()
        self.visible_sprites.empty()
        self.sprite_lookup = {}

        tmx = self.model.level.tmx
        for obj in self.model.objects:
            x = (obj.x * tmx.tile_width)
            y = (obj.y * tmx.tile_height)
            sprite_id = id(obj)
            s = Sprite(
                    sprite_id,
                    Rect(x, y,
                        tmx.tile_width,
                        tmx.tile_height),
                    self.allsprites
                    )
            self.sprite_lookup[sprite_id] = s
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
        if True: #or self.messages[-1] != message:
            self.messages.extend(self.wrap_text(message, 30))
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

        tmx = self.model.level.tmx
        oid = id(event.obj)
        for sprite in self.allsprites:
            if sprite.name == oid:
                sprite.rect.topleft = ((event.obj.x * tmx.tile_width),
                                        (event.obj.y * tmx.tile_height))
                return

    def kill_sprite(self, mapobject):
        """
        Remove a character from play and from the sprite list.
        """
        match = [e for e in self.allsprites if e.name == id(mapobject)]
        if match:
            self.allsprites.remove(match[0])
            self.visible_sprites.remove(match[0])

    def transmute_sprite(self, event):
        """
        Change a sprite image by object gid.
        """

        event.obj.gid = event.gid
        self.set_sprite_defaults(event.obj)

    def update_visible_sprites(self):
        """
        Update the visible_sprites group to only include those within
        the player's view, or on certain other conditions.
        """

        for obj in self.model.objects:
            # get the sprite name and reference
            sprite_name = id(obj)
            sprite = self.sprite_lookup[sprite_name]

            # add and remove sprites from the visible group
            # if they have been seen
            if obj.type in ('ai', 'friend'):
                if obj.in_range:
                    self.visible_sprites.add(sprite)
                else:
                    self.visible_sprites.remove(sprite)
            elif obj.seen:
                self.visible_sprites.add(sprite)
            else:
                self.visible_sprites.remove(sprite)

    def update_viewport(self):
        """
        Auto center the viewport if the player gets too close to any edge.
        """

        # make some values easier to read
        px, py = self.model.player.getpixelxy()
        vp = self.viewport
        tw = self.model.tile_width
        th = self.model.tile_height

        # no point to shift if the level size is within our viewport limits
        tmx = self.model.level.tmx
        if (tmx.width * tw <= vp.width and
            tmx.height * th <= vp.height):
            return

        # how close to edges we need to be to shfit the view (in tiles)
        A = 4 * tw
        B = 4 * th

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
        if self.viewport.right > tmx.width * tw:
            self.viewport.right = tmx.width * tw
        if self.viewport.bottom > tmx.height * th:
            self.viewport.bottom = tmx.height * th

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

        # setup pygame
        try:
            result = pygame.init()
            pygame.font.init()
            pygame.display.set_caption('Alive')
            self.windowsize = pygame.Rect(0, 0, 800, 600)
            self.viewport = pygame.Rect(0, 0, 512, 512)
            self.playarea = pygame.Rect((75, 66), self.viewport.size)
            self.screen = pygame.display.set_mode(self.windowsize.size)
            self.statsarea = pygame.Rect(200, 22, 400, 40)
            self.clock = pygame.time.Clock()
            self.allsprites = pygame.sprite.Group()
            pygame.key.set_repeat(200, 150)
            # load resources
            self.smallfont = pygame.font.Font('UbuntuMono-B.ttf', 16)
            self.largefont = pygame.font.Font('bitwise.ttf', 30)
            self.defaultbackground = image.load(
                'images/background.png').convert()
            self.menubackground = image.load('images/menu.png').convert()
            self.borders = image.load('images/playscreen.png').convert()
            self.borders.set_colorkey(color.magenta)
            self.dialoguebackground = image.load('images/dialog.png').convert()
            self.isinitialized = True
        except Exception, e:
            # these lines pose an interesting problem:
            # if the crash message crashes, we go down hard.
            print('\n'.join(const.CRASH_MESSAGE))
            import traceback
            print('\n' + str(traceback.format_exc()))
            sys.exit(1)


class Sprite(pygame.sprite.Sprite):
    """
    Represents an animated sprite.
    """

    def __init__(self, name, rect, *groups):
        """
        rect(Rect) of the sprite on screen.
        *groups(sprite.Group) add sprite to these groups.
        """

        super(Sprite, self).__init__(*groups)
        self.name = name
        self.rect = rect
        self.image = None
        self._images = []
        self._start = pygame.time.get_ticks()
        self._delay = 0
        self._last_update = 0
        self._frame = 0
        self._hasframes = False
        self.fps = 1
        self.loop = -1

    def addimage(self, image, fps, loop):
        """
        Allows adding of a animated sprite image.
        The fps applies to all frames. It overwrites the previous fps value.
        """

        self._images.append(image)
        self._hasframes = len(self._images) > 1
        if len(self._images) > 0:
            self.image = self._images[0]
        if fps <= 0:
            fps = 1
        self._delay = 1000 / fps
        self.loop = loop
        self._frame = 0

    def clear(self):
        """
        Clear sprite images
        """

        while len(self._images) > 0:
            del self._images[-1]
        self._hasframes = False

    def canupdate(self, t):
        """
        Tests if it is time to update again
        time is the current game ticks. It is used to calculate when to update
            so that animations appear constant across varying fps.
        """

        if t - self._last_update > self._delay:
            return True

    def update(self, t):
        """
        Update the sprite animation if enough time has passed.
        Called by the sprite group draw().
        """

        if not self._hasframes:
            return
        if self.canupdate(t):
            self._last_update = t
            self._frame += 1
            if self._frame >= len(self._images):
                self._frame = 0
                if self.loop > 0:
                    self.loop -= 1
                if self.loop == 0:
                    self._hasframes = False
                    self._frame = -1
            self.image = self._images[self._frame]


class MovingSprite(Sprite):
    """
    A sprite with a vector that slides it to a destination.
    """

    def __init__(self, name, rect, destination, speed, *groups):
        super(MovingSprite, self).__init__(name, rect, *groups)
        self.destination = destination
        self.speed = speed
        self.done = False

    def update(self, t):
        # update location
        super(MovingSprite, self).update(t)
        if self.canupdate(t):
            self._last_update = t
            if self.rect.left < self.destination[0]:
                self.rect.left += self.speed
            if self.rect.left > self.destination[0]:
                self.rect.left -= self.speed
            if self.rect.top < self.destination[1]:
                self.rect.top += self.speed
            if self.rect.top > self.destination[1]:
                self.rect.top -= self.speed
            self.done = self.rect.topleft == self.destination


class TransitionBase(object):
    """
    Base for animated screen transitions.

    Attributes:
        surface (Surface): where to draw onto.
        size ((w, h)): the size of the surface.
    Methods:
        update(): step the transition, returns True while busy
    """

    def __init__(self, rect, background_color, fps):
        """
        Defines a base for animations transition effects.
        Simply: a canvas that draws itself each update() -- permitting fps.

        rect (Rect) tells us how large our canvas should be.
                The topleft component serves to let us know where on
                the screen our canvas will be draw to.

        background_color (r, g, b) fills our canvas with the given color on
                creation.

        fps (int) is used to calculate constant redraw speed for any fps.

        Attributes:
            done (bool):
                True when our animation is complete.
            waitforkey (bool): A flag to let our callers know to wait for
                user keypress.
        """

        self.image = pygame.Surface(rect.size)
        self.image.set_colorkey(color.magenta)
        self.image.fill(background_color)
        self.rect = rect
        #TODO: up fps divisor to 1000?
        self.delay = 500 / fps
        self.lasttime = 0
        self.done = False
        self.waitforkey = False

    def can_update(self, time):
        """
        Tests if it is time to update again. time is the current game ticks.
        """

        if time - self.lasttime > self.delay:
            self.lasttime = time
            return True

    def update(self, time):
        """
        Step the transition.
        use can_update(time) to test if it is time to redraw.
        This call is left empty for you to override.
        """

        if self.can_update(time):
            pass


class SlideinTransition(TransitionBase):
    """
    A rectangle that stays centered on the canvas, grows in width
    until it touches the screen edges.
    Then the rectangle grows in height, while staying centered, until
    touching the top-bottom.
    """

    def __init__(self,
                rect,
                background_color,
                fps,
                font,
                title,
                background=None):
        """
        rect:
            (Rect) tells us how large our canvas should be.
            The topleft component is informative only:
            to let us know where on the screen our image will be draw to.

        background_color:
            (r, g, b) fills our canvas with the given color on creation.

        fps:
            (int) used to calculate constant redraw speed for any fps.

        font:
            is use for drawing any title text.
        """

        super(SlideinTransition, self).__init__(rect, background_color, fps)

        # box is our sliding rectangle that will expand to the screen.
        self.box = pygame.Rect(0, 0, 100, 20)
        # center the box according to full size
        self.box.center = rect.center
        # prerender the words and center them
        self.fontpix = font.render(title, False, color.green)
        self.fontloc = pygame.Rect((0, 0), self.fontpix.get_size())
        self.fontloc.center = rect.center
        self.size = (self.rect.width, self.rect.height)
        # center the background image
        self.background = None
        if background:
            #TODO may not be neccessary if we just store background_image :p
            # make a background surface
            bgpos = ((self.size[0] - background.get_width()) / 2,
                   (self.size[1] - background.get_height()) / 2)
            self.background = pygame.Surface(self.size)
            # fill it with black
            self.background.fill(color.black)
            # paint over the given image
            self.background.blit(background, bgpos)
        # toggle delta direction
        self.xdelta = 30
        self.ydelta = 30
        self.resizingwidth = True
        self.resizingheight = False

    def update(self, time):
        """
        Step the transition.
        """

        if self.can_update(time):
            if self.resizingheight:
                self.box = self.box.inflate(0, self.ydelta)
                self.resizingheight = self.box.h < self.size[1]
            elif self.resizingwidth:
                self.box = self.box.inflate(self.xdelta, 0)
                self.resizingwidth = self.box.w < self.size[0]
                self.resizingheight = not self.resizingwidth
            if self.background:
                # draw the background image cut from the same area of our box
                self.image.blit(self.background, self.box.topleft, self.box)
            pygame.draw.rect(self.image, color.green, self.box, 1)
            self.image.blit(self.fontpix, self.fontloc)
            self.done = not self.resizingwidth and not self.resizingheight
        return not self.done


class TerminalPrinter(TransitionBase):
    """
    Simulates typing text onto a screen.
    """

    def __init__(self,
                rect,
                background_color,
                fps,
                font,
                words,
                wordcolor,
                words_x_offset,
                words_y_offset,
                background=None):
        """
        rect:
            (Rect) tells us how large our canvas should be.
            The topleft component is informative only:
            to let us know where on the screen our image will be draw to.

        background_color:
            (r, g, b) fills our canvas with the given color on creation.

        fps:
            (int) used to calculate constant redraw speed for any fps.

        font:
            is use for drawing any title text.

        title:
            is the words to display during.

        words_x_offset, words_y_offset:
            how much to offset the word position.
            If background given this is relative to
            the rect - background sizes.

        """

        super(TerminalPrinter, self).__init__(rect, background_color, fps)
        self.words = words
        self.text = ""
        self.wordcolor = wordcolor
        self.font = font
        self.xpadding = words_x_offset
        self.ypadding = words_y_offset
        self.lineindex = 0
        self.charindex = 0
        self.rect = rect
        self.xposition, self.yposition = self.rect.topleft
        self.done = False
        self.lastfontheight = 0
        self.waitforkey = True
        self.size = (self.rect.width, self.rect.height)
        # center the background image
        self.background = None
        if background:
            # make a background surface
            bgpos = ((self.size[0] - background.get_width()) / 2,
                   (self.size[1] - background.get_height()) / 2)
            self.xpadding = words_x_offset + bgpos[0]
            self.ypadding = words_y_offset + bgpos[1]
            # create a new background the same size as our canvas
            self.background = pygame.Surface(self.size)
            # fill it with black
            self.background.fill(color.black)
            # paint over the given image
            self.background.blit(background, bgpos)

    def update(self, time):
        """
        Step the transition.
        """

        if self.can_update(time) and not self.done:
            if self.background:
                # draw the background image cut from the same area of our box
                self.image.blit(self.background, self.rect.topleft)
            if self.charindex == len(self.words[self.lineindex]):
                self.lineindex += 1
                self.xposition = self.rect.left
                self.charindex = 0
                self.yposition += self.lastfontheight
                self.done = self.lineindex == len(self.words)
            if not self.done:
                c = self.words[self.lineindex][self.charindex]
                glyph = self.font.render(c, False, self.wordcolor)
                self.background.blit(glyph,
                                    (self.xposition + self.xpadding,
                                    self.yposition + self.ypadding))
                glyphx, self.lastfontheight = glyph.get_size()
                self.xposition += glyphx
            self.charindex += 1
        return self.done
