import pygame
from pygame import image
from pygame.locals import *
from pytmx import tmxloader
import trace
import color
import aliveModel
from eventmanager import *

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
    
    def notify(self, event):
        """
        Called by an event in the message queue.
        """

        if isinstance(event, InitializeEvent):
            self.initialize()
        elif isinstance(event, QuitEvent):
            self.isinitialized = False
            pygame.quit()
        elif isinstance(event, NextLevelEvent):
            self.rendermap()
        elif isinstance(event, ShiftViewportEvent):
            ratio = self.model.level.data.tilewidth
            self.viewport = self.viewport.move(event.xy[0]*ratio, event.xy[1]*ratio)
        elif isinstance(event, TickEvent):
            self.clock.tick(30)
            self.render()

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
            self.screen.blit(self.levelcanvas, (-self.viewport.x, -self.viewport.y))
            self.renderobjects()
            self.screen.blit(self.objectcanvas, (0, 0))
            
        somewords = self.largefont.render(sometext, True, color.green)
        self.screen.blit(somewords, (0, 0))
        # flip the screen with all we drew
        pygame.display.flip()
        
    def rendermap(self):
        """
        Render the level tiles onto self.levelcanvas.
        """
        
        tiledata = self.model.level.data
        levelsize = (tiledata.width * tiledata.tilewidth,
                    tiledata.height * tiledata.tileheight)
        # create level and object canvii
        self.levelcanvas = pygame.Surface(levelsize)
        self.levelcanvas.set_colorkey(color.magenta)
        self.levelcanvas.fill(color.magenta)
        self.objectcanvas = pygame.Surface(levelsize)
        self.objectcanvas.set_colorkey(color.magenta)
        
        tw = tiledata.tilewidth
        th = tiledata.tileheight
        gt = tiledata.getTileImage

        for l in xrange(0, len(tiledata.tilelayers)):
            if tiledata.tilelayers[l].visible:
                for y in xrange(0, tiledata.height):
                    for x in xrange(0, tiledata.width):
                        tile = gt(x, y, l)
                        if tile:
                            self.levelcanvas.blit(tile, (x*tw, y*th))

    def renderobjects(self):
        """
        Render the level objects onto self.objectcanvas.
        """
        
        #NOTE in the end we need to render the objects within the Model itself.
        #       for now we render them from the map data for preview.
        #       just note how we get the image for a GID.
        self.objectcanvas.fill(color.magenta)
        tiledata = self.model.level.data
        for o in tiledata.getObjects():
            if self.viewport.contains(pygame.Rect(o.x, o.y - 32, 32, 32)):
                self.objectcanvas.blit(tiledata.images[o.gid], 
                            (o.x - self.viewport.x, o.y - 32 - self.viewport.y))

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
        # load resources
        self.smallfont = pygame.font.Font(None, 14)
        self.largefont = pygame.font.Font('bitwise.ttf', 28)
        self.defaultbackground = image.load('images/background.png').convert()
        self.menubackground = image.load('images/menu.png').convert()
        self.playbackground = image.load('images/playscreen.png').convert()
        self.dialoguebackground = image.load('images/dialog.png').convert()
        self.isinitialized = True
