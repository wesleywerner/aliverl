import pygame
import trace

class Input(object):
    """ Handles game input """
    
    def __init__ (self, alive):
        """ Class initialiser """
        self.alive = alive
    
    def handler(self, context, code):
        """ Handles ui click events. """
        trace.write('input received on %s: %s' % (context, code))
