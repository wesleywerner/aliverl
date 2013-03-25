import pygame
from eventmanager import *

class GameEngine:
    """
    Tracks the game state.
    """

    def __init__(self, evManager):
        self.evManager = evManager
        evManager.RegisterListener(self)
        self.running = True

    def notify(self, event):
        """
        Called by an event in the message queue. 
        """

        if isinstance(event, QuitEvent):
            self.running = False

    def run(self):
        """
        Starts the game engine loop.

        This pumps a Tick event into the message queue for each loop.
        The loop ends when this object hears a QuitEvent in notify(). 
        """

        # tell all listeners to prepare themselves before we start
        self.evManager.Post(InitializeEvent())
        while self.running:
            newTick = TickEvent()
            self.evManager.Post(newTick)
