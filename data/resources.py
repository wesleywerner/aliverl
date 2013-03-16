import pygame
import states

class Resources(object):
    """ Manages some game resources. """
    
    def __init__ (self):
        """ Class initialiser """
        # background for each state
        self.backgrounds = None
    
    def load (self):
        self.backgrounds = {
            states.intro: None,
            states.menu: None,
            states.help: None,
            states.about: None,
            states.play: pygame.image.load('images/playscreen.png').convert_alpha()
            }
