import pygame
import aliveModel
from eventmanager import *

class KeyboardMouse(object):
    """
    Handles keyboard input.
    """

    def __init__(self, evManager, model):
        self.evManager = evManager
        evManager.RegisterListener(self)
        self.model = model

    def notify(self, event):
        """
        Called by an event in the message queue.
        """

        if isinstance(event, TickEvent):
            # Called for each game tick. We check our keyboard presses here.
            for event in pygame.event.get():
                # always handle window closing events
                if event.type == pygame.QUIT:
                    self.evManager.Post(QuitEvent)
                
                # all key downs
                if event.type == pygame.KEYDOWN:
                    currentstate = self.model.state.peek()
                    # STATE_INTRO: space pops the stack
                    if currentstate == aliveModel.STATE_INTRO:
                        if event.key == pygame.K_SPACE:
                            self.evManager.Post(StateChangeEvent(None))
                    # STATE_MENU: spacebar plays, escape pops
                    elif currentstate == aliveModel.STATE_MENU:
                        if event.key == pygame.K_SPACE:
                            self.evManager.Post(StateChangeEvent(aliveModel.STATE_PLAY))
                        elif event.key == pygame.K_ESCAPE:
                            self.evManager.Post(StateChangeEvent(None))
                    # STATE_PLAY: escape pops, while all others get sent to the UI.
                    elif currentstate == aliveModel.STATE_PLAY:
                        if event.key == pygame.K_ESCAPE:
                            self.evManager.Post(StateChangeEvent(None))
                        else:
                            inEvent = InputEvent(unicodechar=event.unicode, clickpos=None)
                            self.evManager.Post(inEvent)
                        
                        # # NOTE: This was used to test the viewport rendering.
                        # # It works great, by the way.
                        #if event.key == pygame.K_DOWN:
                            #self.evManager.Post(ShiftViewportEvent((0, 1)))
                        #if event.key == pygame.K_UP:
                            #self.evManager.Post(ShiftViewportEvent((0, -1)))
                        #if event.key == pygame.K_LEFT:
                            #self.evManager.Post(ShiftViewportEvent((-1, 0)))
                        #if event.key == pygame.K_RIGHT:
                            #self.evManager.Post(ShiftViewportEvent((1, 0)))
