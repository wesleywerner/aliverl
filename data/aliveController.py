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
                    self.evManager.Post(QuitEvent())
                
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
                    elif currentstate == aliveModel.STATE_PLAY:
                        self.playkeydown(event)
                        
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
    
    def playkeydown(self, event):
        """
        Handles keys for game play.
        Escape pops the stack.
        """
        
        movement = {
                    pygame.K_h: (-1, +0),
                    pygame.K_l: (+1, +0),
                    pygame.K_j: (+0, +1),
                    pygame.K_k: (+0, -1),
                    pygame.K_y: (-1, -1),
                    pygame.K_u: (+1, -1),
                    pygame.K_b: (-1, +1),
                    pygame.K_n: (+1, +1),

                    pygame.K_KP4: (-1, +0),
                    pygame.K_KP6: (+1, +0),
                    pygame.K_KP2: (+0, +1),
                    pygame.K_KP8: (+0, -1),
                    pygame.K_KP7: (-1, -1),
                    pygame.K_KP9: (+1, -1),
                    pygame.K_KP1: (-1, +1),
                    pygame.K_KP3: (+1, +1),
                    }
        if event.key == pygame.K_ESCAPE:
            self.evManager.Post(StateChangeEvent(None))
        elif event.key in movement.keys():
            self.evManager.Post(PlayerMoveEvent(movement[event.key]))
        else:
            inEvent = InputEvent(unicodechar=event.unicode, clickpos=None)
            self.evManager.Post(inEvent)
