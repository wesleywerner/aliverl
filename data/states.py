# game state machine options
import pygame

# constants
intro = 0
menu = 1
help = 2
about = 3
play = 4
dialog = 5

class MachineState(object):
    """ manages the machine's state. """
    
    def __init__ (self, statestack):
        """ Class initialiser """
        self.statestack = statestack
    
    def peek(self):
        """ Returns the current machine state. """
        try:
            return self.statestack[-1]
        except IndexError:
            # empty stack
            return None
    
    def pop(self):
        """ Remove the current state and return it. """
        try:
            self.statestack.pop()
        except IndexError:
            # empty stack
            return None
    
    def push(self, statevalue):
        """ push a state onto the stack. Returns the pushed value. """
        self.statestack.append(statevalue)
        return statevalue
