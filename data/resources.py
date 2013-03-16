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
            states.play: pygame.image.load('images/playscreen.png').convert_alpha(),
            states.dialog: None,
            'dialog': pygame.image.load('images/dialog.png').convert_alpha()
            }
        # copy the dialog background as the play one. we show the dialog text
        # overlayed on the map.
        self.backgrounds[states.dialog] = self.backgrounds[states.play]
