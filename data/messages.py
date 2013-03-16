import json
import pygame
from pygame.locals import *
import trace
import helper


class Messages(object):
    """ Stores and renders recent game messages. """
    
    def __init__ (self):
        """ Class initialiser """
        self.messages = [''] * 20
        self.canvas = None
        self.maxlen = 39
        self.font = None
        self.dialogs = None
    
    def load (self):
        self.load_dialog_data()
        self.font = pygame.font.Font('bitwise.ttf', 14)
        self.render()
        
    def add(self, message):
        """ Add message and trim the list. """
        if type(message) is list:
            for m in message:
                self.add(m)
        else:
            trace.write(message)
            self.messages.extend(helper.wrapLines(message, 39))
        self.messages = self.messages[-20:]
        self.render()
    
    def render(self):
        """ Renders new messages to our canvas. """
        self.canvas = helper.renderLines(
                        self.messages[-10:],
                        self.font,
                        True,
                        (0, 20, 0),
                        (0, 20, 0),
                        )
                        
    def load_dialog_data(self):
        """ load the dialog.def data. """
        self.dialogs = json.load(open('dialogs.def'))
