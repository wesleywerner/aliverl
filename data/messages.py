import pygame
from pygame.locals import *

class Messages(object):
    """ Stores and renders recent game messages. """
    
    def __init__ (self):
        """ Class initialiser """
        self.messages = []
        #self.canvas = pygame.Surface(canvas_size, 0, 32) 
        
    def add(self, message):
        """ Add message and trim the list. """
        self.messages.append(message)
        self.messages = self.messages[-10:]
    
    def __render(self):
        """ Renders new messages to our canvas. """
