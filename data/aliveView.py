import os
import pygame
from pygame import image
from pygame.locals import *
import trace
import color
import aliveModel
from eventmanager import *
from tmxparser import TMXParser
from tmxparser import TilesetParser

# fixes a bug in tiled map editor.
# it saves objects y-position with one tile's worth more.
# its value is set later on. remove when bug is fixed :P
# https://github.com/bjorn/tiled/issues/91
FIX_YOFFSET=0

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
        fogcanvas (Surface): overlay for visibility fog.
        playarea (Rect): location on screen to draw gameplay.
        statsarea (Rect): area to draw player stats.
        messagearea (Rect): area to draw the recent messages.
        viewport (Rect): which portion of the game map we are looking at.
        spritegroup (Group): contains all animated, movable objects in play.
        helpimages (Surface): stores the F1 help screens.
        transition (TransitionBase): current animated screen transition.
        transitionstep (int): transition counter.
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
        self.fogcanvas = None
        self.playarea = None
        self.statsarea = None
        self.messagearea = None
        self.viewport = None
        self.spritegroup = None
        self.helpimages = None
        self.transition = None
        self.transitionstep = 0
        self.messages = [''] * 20
        self.gamefps = 30
    
    def notify(self, event):
        """
        Called by an event in the message queue.
        """

        if isinstance(event, TickEvent):
            self.render()
            self.clock.tick(self.gamefps)
        elif isinstance(event, CharacterMovedEvent):
            self.movesprite(event)
            self.erasefog()
        elif isinstance(event, MessageEvent):
            self.messages.extend(self.wrapLines(event.message, 30))
        elif isinstance(event, KillCharacterEvent):
            self.removesprite(event.character)
            self.messages.append('The %s dies' % (event.character.name))
        elif isinstance(event, UpdateObjectGID):
            self.transmutesprite(event)
        elif isinstance(event, DialogueEvent):
            self.dialoguewords = event.words[::-1]
        elif isinstance(event, NextLevelEvent):
            self.preparelevel()
            self.erasefog()
            self.createsprites()
        elif isinstance(event, ShiftViewportEvent):
            self.adjustviewport(event)
        elif isinstance(event, InitializeEvent):
            self.initialize()
        elif isinstance(event, QuitEvent):
            self.isinitialized = False
            pygame.quit()
    
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

        self.screen.blit(self.defaultbackground, (0, 0))
        state = self.model.state.peek()
        sometext = ''
        
        if state == aliveModel.STATE_INTRO:
            sometext = 'Intro screen is now drawing. Space to skip.'
            
        elif state == aliveModel.STATE_MENU:
            sometext = 'The game menu is now showing. Space to play, escape to quit.'
            
        elif state == aliveModel.STATE_DIALOG:
            self.drawborders()
            self.drawstats()
            self.drawmessages()
            self.drawplayground()
            self.drawdialogue()
            
        elif state in (aliveModel.STATE_PLAY, aliveModel.STATE_GAMEOVER):
            self.drawborders()
            self.drawstats()
            self.drawmessages()
            self.drawplayground()
            
            if state == aliveModel.STATE_GAMEOVER:
                #TODO Overlay a game over message.
                sometext = 'You have died :('
        
        elif state == aliveModel.STATE_HELP:
            if not self.helpimages:
                self.helpimages = pygame.image.load('images/help-1.png').convert()
            self.screen.blit(self.helpimages, (0, 0))
        
        if self.transition:
            self.transition.update(pygame.time.get_ticks())
            self.screen.blit(self.transition.surface, (0, 0))

        somewords = self.largefont.render(sometext, True, color.green)
        self.screen.blit(somewords, (0, 0))
        pygame.display.flip()
    
    def drawplayground(self):
        """
        Draw the play area: level tiles and objects.
        """

        self.screen.blit(self.levelcanvas, self.playarea, self.viewport)
        self.objectcanvas.fill(color.magenta)
        self.spritegroup.update(pygame.time.get_ticks())
        self.spritegroup.draw(self.objectcanvas)
        self.screen.blit(self.objectcanvas, self.playarea, self.viewport)
        #self.screen.blit(self.fogcanvas, self.playarea, self.viewport)
        
        
    def drawdialogue(self):
        """
        Draw current dialogue words.
        transitionstep is an indicator for this call for chaining transitions.
        
        transitionstep is used to control chaining transitions together.
        values (0, 2) signal to create a new transition.
        when in (1, 3) it means switch to the next one.
        
        """

        if (self.transition and (not self.transition.done or self.transition.waitforkey)):
            return False
        
        if self.transitionstep in (0, 2):
            canvas = pygame.Surface(self.screen.get_size())
            canvas.set_colorkey(color.magenta)
            canvas.fill(color.magenta)
            if self.transitionstep == 0:
                self.transition = SlideinTransition(
                                    canvas, self.playarea, self.gamefps, 
                                    self.largefont, 'connecting...')
            elif self.transitionstep == 2:
                if self.dialoguewords:
                    wordcolor = color.green
                    words = self.dialoguewords[-1]
                    # words may be (color, words)
                    if type(words) is tuple:
                        wordcolor, words = words
                    words = self.wrapLines(words, 25)
                    canvas.blit(self.dialoguebackground, self.playarea)
                    self.transition = TerminalPrinter(
                                        canvas, self.playarea, self.gamefps, 
                                        self.largefont, words, wordcolor)
            if not self.transition.waitforkey:
                self.transitionstep += 1
        else:
            # automatic chain from open animation to text printer
            if self.transitionstep == 1:
                self.transitionstep += 1

    def nextdialogue(self):
        """
        Move to the next dialogue line
        """

        if self.dialoguewords:
            # show each dialogue page as the transition finishes
            if self.transition.done:
                self.dialoguewords.pop()
                self.transition.waitforkey = False
                self.evManager.Post(DialogueEvent(self.dialoguewords[::-1]))
        if not self.dialoguewords:
            # no dialogue left, pop the model stack back to whence it came.
            self.transition = None
            self.transitionstep = 0
            self.evManager.Post(StateChangeEvent(None))
    
    def closedialogue(self):
        """
        Close running dialogues and reset for next time.
        """
        
        self.dialoguewords = []
        self.nextdialogue()
        
    def drawborders(self):
        """
        Draw game borders.
        """
        
        self.screen.blit(self.borders, (0, 0))
        
    def drawstats(self):
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
        self.statscanvas.blit(pmana, (xposition + (phealth.get_width() * 1.5), yposition))
        self.screen.blit(self.statscanvas, self.statsarea)
    
    def drawmessages(self):
        """
        Draw recent game messages.
        """
        
        self.screen.blit(
                        self.renderLines(
                            self.messages[-8:],
                            self.smallfont,
                            False,
                            (0, 20, 0),
                            (0, 20, 0)),
                        self.messagearea.topleft)
        # cull
        self.messages = self.messages[-20:]
        
    def wrapLines(self, message, maxlength):
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


    def renderLines(self, lines, font, antialias, fontcolor, colorize=None, background=None):
        """ # Simple functions to easily render pre-wrapped text onto a single
        # surface with a uniform background.
        # Author: George Paci

        # Results with various background color alphas:
        #  no background given: ultimate blit will just change figure part of text,
        #      not ground i.e. it will be interpreted as a transparent background
        #  background alpha = 0: "
        #  background alpha = 128, entire bounding rectangle will be equally blended
        #      with background color, both within and outside text
        #  background alpha = 255: entire bounding rectangle will be background color
        #
        # (At this point, we're not trying to respect foreground color alpha;
        # we could by compositing the lines first onto a transparent surface, then
        # blitting to the returned surface.)
        
        colorize sets by how much each rgb value is upped for each line.
        (0, 10, 0) will up green by 10 for each line printed.
         """
        
        fontHeight = font.get_height()
        surfaces = []
        c = fontcolor
        if colorize:
            for ln in lines:
                c = ( c[0] + colorize[0], c[1] + colorize[1], c[2] + colorize[2])
                surfaces.append(font.render(ln, antialias, c))
        else:
            surfaces = [font.render(ln, antialias, fontcolor) for ln in lines]
        maxwidth = max([s.get_width() for s in surfaces])
        result = pygame.Surface((maxwidth, len(lines)*fontHeight))
        result.set_colorkey(color.magenta)
        if background == None:
            result.fill(color.magenta)
        else:
            result.fill(background)

        for i in range(len(lines)):
            result.blit(surfaces[i], (0,i*fontHeight))
        return result

    def renderTextBlock(self, text, font, antialias, fontcolor, colorize=None, background=None):
        """ renders block text with newlines. """
        brokenText = text.replace("\r\n","\n").replace("\r","\n")
        return self.renderLines(
                        brokenText.split("\n"), 
                        font, 
                        antialias, 
                        fontcolor, 
                        colorize, 
                        background
                        )

    def preparelevel(self):
        """
        Prepare the View's resource to display the level given in event param.
        """
        
        tmx = self.model.level.tmx
        global FIX_YOFFSET
        FIX_YOFFSET = tmx.tile_height
        # load the tileset parser
        tilesetfile = os.path.join(self.model.story.path, tmx.tilesets[0].source)
        self.tsp = TilesetParser(
                                tilesetfile,
                                (tmx.tile_width, tmx.tile_height), 
                                color.magenta
                                )

        # draw tiles
        if not self.levelcanvas:
            self.levelcanvas = pygame.Surface((tmx.px_width, tmx.px_height))
            self.levelcanvas.set_colorkey(color.magenta)
        if not self.objectcanvas:
            self.objectcanvas = pygame.Surface(self.levelcanvas.get_size())
            self.objectcanvas.set_colorkey(color.magenta)
        if not self.statscanvas:
            self.statscanvas = pygame.Surface(self.statsarea.size)
            self.statscanvas.set_colorkey(color.magenta)
        self.fogcanvas = image.load('images/fog.png').convert()
        self.fogcanvas.set_colorkey(color.magenta)
        self.levelcanvas.fill(color.magenta)
        for y in range(tmx.height):
            for x in range(tmx.width):
                for layer in tmx.tilelayers:
                    gid = layer.at((x, y)) 
                    tile = self.tsp[gid]
                    if tile:
                        self.levelcanvas.blit(tile, 
                                    (x * tmx.tile_width, y * tmx.tile_height))
    
    def erasefog(self):
        """
        Partially clear some fog around the player.
        We do this by clearing (filling) the fogcanvas with magenta.
        """
        
        clearing = pygame.Rect((0, 0), self.model.level.tmx.tilesize(3))
        clearing.center = self.model.player.getpixelxy()
        balancingoffset = self.model.level.tmx.tile_width / 2
        clearing = clearing.move(balancingoffset, -balancingoffset)
        self.fogcanvas.fill(color.magenta, clearing)
        
    
    def setspriteframes(self, obj):
        """
        Apply sprite settings to an object from the story animations setting.
        """
        
        defaultvalues = {'frames':[], 'fps':0, 'loop': 0}
        anims = self.model.story.animations
        sprite = [e for e in self.spritegroup if e.name == id(obj)][0]
        if sprite:
            if obj.gid in anims.keys():
                [setattr(obj, k, v) for k, v in anims[obj.gid].items()]
            else:
                [setattr(obj, k, v) for k, v in defaultvalues.items()]
            if len(obj.frames) == 0:
                obj.frames.append(obj.gid)
            sprite.clear()
            for f in obj.frames:
                sprite.addimage(self.tsp[f], obj.fps, obj.loop)

    def createsprites(self):
        """
        Create all the sprites that represent all level objects.
        """
        
        if not self.spritegroup:
            self.spritegroup = pygame.sprite.Group()
        self.spritegroup.empty()
        
        tmx = self.model.level.tmx
        for obj in self.model.objects:
            x = (obj.x * tmx.tile_width)
            y = (obj.y * tmx.tile_height) - FIX_YOFFSET
            s = Sprite(
                    id(obj),
                    Rect(x, y, 
                        tmx.tile_width, 
                        tmx.tile_height),
                    self.spritegroup
                    )
            self.setspriteframes(obj)

    def movesprite(self, event):
        """
        Move the sprite by the event details.
        """
        
        tmx = self.model.level.tmx
        oid = id(event.obj)
        for sprite in self.spritegroup:
            if sprite.name == oid:
                sprite.rect.topleft = ((event.obj.x * tmx.tile_width),
                                        (event.obj.y * tmx.tile_height) - FIX_YOFFSET)
                return

    def removesprite(self, mapobject):
        """
        Remove a character from play and from the sprite list.
        """
        match = [e for e in self.spritegroup if e.name == id(mapobject)]
        if match:
            self.spritegroup.remove(match[0])
    
    def transmutesprite(self, event):
        """
        Change a sprite image by object gid.
        """
        
        event.obj.gid = event.gid
        self.setspriteframes(event.obj)
    
    def adjustviewport(self, event):
        """
        Auto center the viewport if the player gets too close to any edge.
        """
        
        pass

    def playmusic(self, level):
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
        result = pygame.init()
        pygame.font.init()
        pygame.display.set_caption('Alive')
        windowsize = pygame.Rect(0, 0, 800, 512)
        self.viewport = pygame.Rect(0, 0, 512, 512)
        self.playarea = pygame.Rect((windowsize.w - self.viewport.w, 0), self.viewport.size)
        self.screen = pygame.display.set_mode(windowsize.size)
        self.statsarea = pygame.Rect(16, 300, self.playarea.left, 100)
        self.messagearea = pygame.Rect(15, 360, 260, 140)
        self.clock = pygame.time.Clock()
        self.spritegroup = pygame.sprite.Group()
        # load resources
        self.smallfont = pygame.font.Font('UbuntuMono-B.ttf', 16)
        self.largefont = pygame.font.Font('bitwise.ttf', 30)
        self.defaultbackground = image.load('images/background.png').convert()
        self.menubackground = image.load('images/menu.png').convert()
        self.borders = image.load('images/playscreen.png').convert()
        self.dialoguebackground = image.load('images/dialog.png').convert()
        self.isinitialized = True


class Sprite(pygame.sprite.Sprite):
    """
    Represents an animated sprite.
    """
    
    def __init__(self, name, rect, *groups):
        """
        rect(Rect) of the sprite on screen.
        fps(int) frames per seconds to rotate through.
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
        self.image = None
        self.fps = 1
        self.loop = -1
    
    def addimage(self, image, fps, loop):
        """
        Allows adding of a animated sprite image.
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

    def update(self, t):
        """
        Update the sprite animation if enough time has passed.
        Called by the sprite group draw().
        """
        
        if not self._hasframes:
            return
        if t - self._last_update > self._delay:
            self._frame += 1
            if self._frame >= len(self._images): 
                self._frame = 0
                if self.loop > 0:
                    self.loop -= 1
                if self.loop == 0:
                    self._hasframes = False
                    self._frame = -1
            self.image = self._images[self._frame]
            self._last_update = t
    
    
class TransitionBase(object):
    """
    Base for animated screen transitions.
    
    Attributes:
        surface (Surface): where to draw onto.
        size ((w, h)): the size of the surface.
    Methods:
        update(): step the transition, returns True while busy
    """
    
    def __init__(self, surface, viewport, fps):
        """
        Defines an animated transition base.
        
        surface is where to draw on.
        viewport tells us the area to draw within surface.
        fps isused to calculate constant redraw speed for any fps.
        
        Attributes:
            done (bit): set to True when the animation is complete.
            waitforkey (bit): flags to wait for user keypress.
        """
        
        self.surface = surface
        self.viewport = viewport
        self.delay = 500 / fps
        self.lasttime = 0
        self.done = False
        self.waitforkey = False
    
    def canupdate(self, time):
        """
        Tests if it is time to update again
        time is the current game ticks. It is used to calculate when to update
            so that animations appear constant across varying fps.
        """
        
        if time - self.lasttime > self.delay:
            self.lasttime = time
            return True
        
    def update(self, time):
        """
        Step the transition.
        use canupdate(time) to test if it is time to redraw.
        Returns True while transitioning.
        """
        
        if self.canupdate(time):
            return True


class SlideinTransition(TransitionBase):
    """
    Starts with the words "connecting..." centered.
    A small centered square below the words elongates horizontally 
        into a long rectangle.
    Elongate the rectangle vertically to fill up the space.
    The words disappear.
    """
    
    def __init__(self, surface, viewport, fps, font, title):
        """
        surface is where to draw on.
        font is for drawing the title text.
        title is the words to display during.
        """
        
        super(SlideinTransition, self).__init__(surface, viewport, fps)
        self.box = pygame.Rect(0, 0, 10, 10)
        # center the box according to full size
        self.box.center = viewport.center
        # prerender the words and center them
        self.fontpix = font.render(title, False, color.green)
        self.fontloc = pygame.Rect((0, 0), self.fontpix.get_size())
        self.fontloc.center = viewport.center
        # reduce the size now to draw animations within a margin
        self.size = (self.viewport.width -32, self.viewport.height -32)
        # toggle delta direction
        self.xdelta = 60
        self.ydelta = 60
        self.resizingwidth = True
        self.resizingheight = False
        
    def update(self, time):
        """
        Step the transition.
        """
        
        if self.canupdate(time):
            if self.resizingheight:
                self.box = self.box.inflate(0, self.ydelta)
                self.resizingheight = self.box.h < self.size[1]
            elif self.resizingwidth:
                self.box = self.box.inflate(self.xdelta, 0)
                self.resizingwidth = self.box.w < self.size[0]
                self.resizingheight = not self.resizingwidth
            pygame.draw.rect(self.surface, color.black, self.box)
            pygame.draw.rect(self.surface, color.blue, self.box, 1)
            self.surface.blit(self.fontpix, self.fontloc)
            self.done = not self.resizingwidth and not self.resizingheight
        return not self.done


class TerminalPrinter(TransitionBase):
    """
    Simulates typing out blocks of text onto the screen.
    """
    
    def __init__(self, surface, viewport, fps, font, words, wordcolor):
        """
        surface is where to draw on.
        font is for drawing the title text.
        words is a list of strings to print. one row per list item.
        """
        
        super(TerminalPrinter, self).__init__(surface, viewport, fps)
        self.words = words
        self.wordcolor = wordcolor
        self.font = font
        self.xpadding = 32
        self.ypadding = 32
        self.lineindex = 0
        self.charindex = 0
        self.xposition, self.yposition = self.viewport.topleft
        self.done = False
        self.lastfontheight = 0
        self.waitforkey = True
        
    def update(self, time):
        """
        Step the transition.
        """

        if self.canupdate(time) and not self.done:
            if self.charindex == len(self.words[self.lineindex]):
                self.lineindex += 1
                self.xposition = self.viewport.left
                self.charindex = 0
                self.yposition += self.lastfontheight
                self.done = self.lineindex == len(self.words)
            if not self.done:
                c = self.words[self.lineindex][self.charindex]
                glyph = self.font.render(c, False, self.wordcolor)
                self.surface.blit(glyph, 
                                    (self.xposition + self.xpadding, 
                                    self.yposition + self.ypadding))
                glyphx, self.lastfontheight = glyph.get_size()
                self.xposition += glyphx
            self.charindex += 1
        return self.done
