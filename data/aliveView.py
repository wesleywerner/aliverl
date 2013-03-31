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

# fixes
# a bug in tiled map editor saves objects y-position with one tile's worth more.
# we offset Y by one tile less as workaround.
# https://github.com/bjorn/tiled/issues/91
FIX_YOFFSET=32

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
        screen (pygame.Surface): the screen surface.
        clock (pygame.time.Clock): keeps the fps constant.
        smallfont (pygame.Font): a small font.
        largefont (pygame.Font): a larger font.
        levelcanvas (pygame.Surface): a rendering of the level tiles.
        objectcanvas (pygame.Surface): a rendering of the level objects.
        viewport (pygame.Rect): the viewable play area.

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
        self.viewport = None
        self.tilemapdata = None
        self.spritegroup = None
    
    def notify(self, event):
        """
        Called by an event in the message queue.
        """

        if isinstance(event, TickEvent):
            self.render()
            self.clock.tick(30)
        elif isinstance(event, InitializeEvent):
            self.initialize()
        elif isinstance(event, QuitEvent):
            self.isinitialized = False
            pygame.quit()
        elif isinstance(event, NextLevelEvent):
            self.preparelevel()
            self.createsprites()
        elif isinstance(event, ShiftViewportEvent):
            ratio = self.model.level.data.tilewidth
            self.viewport = self.viewport.move(event.xy[0]*ratio, event.xy[1]*ratio)
        elif isinstance(event, PlayerMovedEvent):
            self.movesprite(event)
    
    def widgetclick(self, context, code):
        """
        A handler that gets called by UI widgets.
        #TODO UI WIDGET IMPLEMENTATION
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

        # show something on the view for pretty testing
        currentstate = self.model.state.peek()
        if currentstate == aliveModel.STATE_INTRO:
            sometext = 'Intro screen is now drawing. Space to skip.'
        elif currentstate == aliveModel.STATE_MENU:
            sometext = 'The game menu is now showing. Space to play, escape to quit.'
        elif currentstate == aliveModel.STATE_PLAY:
            sometext = 'You are now playing. Escape to go back to the menu.'
            self.screen.blit(self.levelcanvas, 
                            (-self.viewport.x, -self.viewport.y))
            #self.drawobjects()
            ## update sprite animations and draw them
        self.spritegroup.update(pygame.time.get_ticks())
        self.spritegroup.draw(self.screen)
            
        somewords = self.largefont.render(sometext, True, color.green)
        self.screen.blit(somewords, (0, 0))
        # flip the screen with all we drew
        pygame.display.flip()
        
    def preparelevel(self):
        """
        Prepare the View's resource to display the level given in event param.
        """
        
        tmx = self.model.level.tmx
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
        self.levelcanvas.fill(color.magenta)
        for y in range(tmx.height):
            for x in range(tmx.width):
                for layer in tmx.tilelayers:
                    gid = layer.at((x, y)) 
                    tile = self.tsp[gid]
                    if tile:
                        self.levelcanvas.blit(tile, 
                                    (x * tmx.tile_width, y * tmx.tile_height))

    def createsprites(self):
        """
        Create all the sprites that represent all level objects.
        """
        
        if not self.spritegroup:
            self.spritegroup = pygame.sprite.Group()
        self.spritegroup.empty()
        
        tmx = self.model.level.tmx
        for grp in tmx.objectgroups:
            for obj in grp:
                # obj has a frames list.
                # if this list is empty, use the obj.gid
                frames = []
                fps = 0
                try:
                    fps = obj.fps
                    for f in obj.frames:
                        frames.append(self.tsp[f])
                except AttributeError as e:
                    # this object has no frames or fps set
                    pass
                if len(frames) == 0:
                    frames.append(self.tsp[obj.gid])
                # tiled map editor has a bug where y position
                # of map objects are one tile too large.
                # fix with -tile_height
                x = (obj.x * tmx.tile_width)
                y = (obj.y * tmx.tile_height) - FIX_YOFFSET
                s = Sprite(
                        id(obj),
                        Rect(x, y, 
                            tmx.tile_width, 
                            tmx.tile_height),
                        frames,
                        fps,
                        self.spritegroup
                        )

    
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
        
    def initialize(self):
        """
        Set up the pygame graphical display and loads graphical resources.
        """

        result = pygame.init()
        pygame.font.init()
        pygame.display.set_caption('Alive')
        self.screen = pygame.display.set_mode((800, 512))
        self.viewport = pygame.Rect(0, 0, 512, 512)
        self.clock = pygame.time.Clock()
        self.spritegroup = pygame.sprite.Group()
        # load resources
        self.smallfont = pygame.font.Font(None, 14)
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
    
    def __init__(self, name, rect, frames, fps, *groups):
        """
        rect(Rect) of the sprite on screen.
        fps(int) frames per seconds to rotate through.
        *groups(sprite.Group) add sprite to these groups.
        """
        
        super(Sprite, self).__init__(*groups)
        self.name = name
        self.rect = rect
        self.image = None
        self._images = frames
        self._start = pygame.time.get_ticks()
        if fps <= 0: fps = 1
        self._delay = 1000 / fps
        self._last_update = 0
        self._frame = 0
        self._hasframes = len(self._images) > 1

        # set our first image.
        self.image = self._images[0]

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
            self.image = self._images[self._frame]
            self._last_update = t
