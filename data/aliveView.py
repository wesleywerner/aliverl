import os
import pygame
from pygame import image
from pygame.locals import *
import trace
import color
import aliveModel
import viewhelper as helper
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
        playarea (Rect): location on screen to draw gameplay.
        statsarea (Rect): area to draw player stats.
        messagearea (Rect): area to draw the recent messages.
        viewport (Rect): which portion of the game map we are looking at.
        spritegroup (Group): contains all animated, movable objects in play.
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
        self.messagearea = None
        self.viewport = None
        self.spritegroup = None
        self.messages = [''] * 20
    
    def notify(self, event):
        """
        Called by an event in the message queue.
        """

        if isinstance(event, TickEvent):
            self.render()
            self.clock.tick(30)
        elif isinstance(event, PlayerMovedEvent):
            self.movesprite(event)
        elif isinstance(event, MessageEvent):
            self.messages.extend(helper.wrapLines(event.message, 30))
        elif isinstance(event, KillCharacterEvent):
            self.removesprite(event.character)
            self.messages.append('The %s dies' % (event.character.name))
        elif isinstance(event, UpdateObjectGID):
            self.transmutesprite(event)
        elif isinstance(event, NextLevelEvent):
            self.preparelevel()
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
            
        elif state in (aliveModel.STATE_PLAY, aliveModel.STATE_GAMEOVER):
            self.drawstats()
            self.screen.blit(self.playbackground, (0, 0))
            self.screen.blit(self.statscanvas, self.statsarea)
            self.drawmessages()
            self.screen.blit(self.levelcanvas, self.playarea, self.viewport)
            # update sprites
            self.objectcanvas.fill(color.magenta)
            self.spritegroup.update(pygame.time.get_ticks())
            self.spritegroup.draw(self.objectcanvas)
            self.screen.blit(self.objectcanvas, self.playarea, self.viewport)
            
            if state == aliveModel.STATE_GAMEOVER:
                #TODO Overlay a game over message.
                sometext = 'You have died :('
        
        somewords = self.largefont.render(sometext, True, color.green)
        self.screen.blit(somewords, (0, 0))
        pygame.display.flip()
    
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
    
    def drawmessages(self):
        """
        Draw recent game messages.
        """
        
        self.screen.blit(
                        helper.renderLines(
                            self.messages[-8:],
                            self.smallfont,
                            False,
                            (0, 20, 0),
                            (0, 20, 0)),
                        self.messagearea.topleft)
        # cull
        self.messages = self.messages[-20:]
        
        
    def renderLines(self, lines, font, antialias, color, background=None):
        """
        Draws a list of lines to a surface.
        """

        print(type(font), font)
        fontHeight = font.get_height()
        if type(color) is list:
            surfaces = [font.render(k, antialias, v) for k,v in zip(lines, color)]
        else:
            surfaces = [font.render(ln, antialias, color) for ln in lines]
        # can't pass background to font.render, because it doesn't respect the alpha

        maxwidth = max([s.get_width() for s in surfaces])
        result = pygame.Surface((maxwidth, len(lines)*fontHeight), pygame.SRCALPHA)
        if background == None:
            result.fill((90,90,90,0))
        else:
            result.fill(background)

        for i in range(len(lines)):
          result.blit(surfaces[i], (0,i*fontHeight))
        return result

    def renderTextBlock(self, text, font, antialias, color, background=None):
        """
        Draws text lines with newlines to a surface.
        """
        brokenText = text.replace("\r\n","\n").replace("\r","\n")
        return renderLines(brokenText.split("\n"), font, antialias, color, background)

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
            self.objectcanvas = pygame.Surface((tmx.px_width, tmx.px_height))
            self.objectcanvas.set_colorkey(color.magenta)
        if not self.statscanvas:
            self.statscanvas = pygame.Surface(self.statsarea.size)
            self.statscanvas.set_colorkey(color.magenta)
        self.levelcanvas.fill(color.magenta)
        for y in range(tmx.height):
            for x in range(tmx.width):
                for layer in tmx.tilelayers:
                    gid = layer.at((x, y)) 
                    tile = self.tsp[gid]
                    if tile:
                        self.levelcanvas.blit(tile, 
                                    (x * tmx.tile_width, y * tmx.tile_height))

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
        for sprite in self.spritegroup:
            if sprite.name == event.objectid:
                sprite.rect = sprite.rect.move(
                    event.direction[0] * tmx.tile_width,
                    event.direction[1] * tmx.tile_height)
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

    def initialize(self):
        """
        Set up the pygame graphical display and loads graphical resources.
        """

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
        self.largefont = pygame.font.Font('bitwise.ttf', 28)
        self.defaultbackground = image.load('images/background.png').convert()
        self.menubackground = image.load('images/menu.png').convert()
        self.playbackground = image.load('images/playscreen.png').convert()
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
            self.image = self._images[self._frame]
            self._last_update = t
    
