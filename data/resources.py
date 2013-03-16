import pygame
import states

class Resources(object):
    """ Manages some game resources. """
    
    def __init__ (self):
        """ Class initialiser """
        # background for each state
        self.backgrounds = None
        self.defaultbg = None
    
    def load (self):
        self.defaultbg = pygame.image.load('images/background.png').convert_alpha()
        self.backgrounds = {
            states.intro: None,
            states.menu: pygame.image.load('images/menu.png').convert_alpha(),
            states.help: None,
            states.about: None,
            states.play: pygame.image.load('images/playscreen.png').convert_alpha()
            }
