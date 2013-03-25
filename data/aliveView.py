import pygame
from pygame import image
import trace
import color
import aliveModel
from eventmanager import *

class GraphicalView(object):
    """
    Draws the model state onto the screen.
    """

    def __init__(self, evManager):
        self.evManager = evManager
        evManager.RegisterListener(self)
        self.isinitialized = False
        self.screen = None
        self.clock = None
        self.smallfont = None
        self.largefont = None
        
    def notify(self, event):
        """
        Called by an event in the message queue.
        """

        if isinstance(event, InitializeEvent):
            self.initialize()
        if isinstance(event, QuitEvent):
            self.isinitialized = False
            pygame.quit()
        if isinstance(event, LoadLevel):
            self.preplevel(event.level)
        if isinstance(event, TickEvent):
            self.clock.tick(30)
            self.render()

    def render(self):
        """
        Draw the current game state on screen.
        """
        
        if not self.isinitialized:
            return
        # show something on the view for pretty testing
        somewords = self.largefont.render(
            'This pygame view is rendering.', True, color.green)
        self.screen.fill(color.black)
        self.screen.blit(self.defaultbackground, (0, 0))
        self.screen.blit(somewords, (0, 0))
        # flip the screen with all we drew
        pygame.display.flip()
        
    def preplevel(self, level):
        """
        Prepares any graphical resources for the given level.
        This even includes creating all object sprites from the model's
        map data.
        """
        
        pass

    def initialize(self):
        """
        Set up the pygame graphical display.
        Loads graphical resources.
        Should only be called once.
        """

        result = pygame.init()
        pygame.font.init()
        pygame.display.set_caption('Alive')
        self.screen = pygame.display.set_mode((800, 512))
        self.clock = pygame.time.Clock()
        # load resources
        self.smallfont = pygame.font.Font(None, 14)
        self.largefont = pygame.font.Font('bitwise.ttf', 28)
        self.defaultbackground = image.load('images/background.png').convert()
        self.menubackground = image.load('images/menu.png').convert()
        self.playbackground = image.load('images/playscreen.png').convert()
        self.dialoguebackground = image.load('images/dialog.png').convert()
        self.isinitialized = True
