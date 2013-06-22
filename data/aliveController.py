import pygame
import aliveModel
from eventmanager import *


class KeyboardMouse(object):
    """
    Handles keyboard input.
    """

    def __init__(self, evManager, model, view):
        self.evManager = evManager
        evManager.RegisterListener(self)
        self.model = model
        self.view = view

    def notify(self, event):
        """
        Called by an event in the message queue.
        """

        try:
            if isinstance(event, TickEvent):
                for event in pygame.event.get():
                    # always handle window closing events
                    if event.type == pygame.QUIT:
                        self.evManager.Post(QuitEvent())

                    # all key downs
                    if event.type == pygame.KEYDOWN:
                        state = self.model.state.peek()
                        if state == aliveModel.STATE_INTRO:
                            self.intro_keys(event)
                        elif state == aliveModel.STATE_MENU:
                            self.menu_keys(event)
                        elif state == aliveModel.STATE_PLAY:
                            self.play_keys(event)
                        elif state == aliveModel.STATE_GAMEOVER:
                            self.game_over_keys(event)
                        elif state == aliveModel.STATE_DIALOG:
                            self.dialogue_keys(event)
                        elif state == aliveModel.STATE_CRASH:
                            self.crash_keys(event)
                        else:
                            # allow escaping from unhandled states
                            self.evManager.Post(StateChangeEvent(None))
        except:
            self.evManager.Post(CrashEvent())

    def play_keys(self, event):
        """
        Handles game play keys.
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
        elif event.key == pygame.K_F1:
            self.evManager.Post(StateChangeEvent(aliveModel.STATE_HELP))
        elif event.key in movement.keys():
            self.evManager.Post(PlayerMoveRequestEvent(movement[event.key]))
        else:
            inEvent = InputEvent(unicodechar=event.unicode, clickpos=None)
            self.evManager.Post(inEvent)

    def dialogue_keys(self, event):
        """
        Handles dialogue keys.
        """

        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
            self.view.next_dialogue()
        elif event.key == pygame.K_ESCAPE:
            self.view.close_dialogue()

    def menu_keys(self, event):
        """
        Handles menu keys.
        """

        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.evManager.Post(StateChangeEvent(aliveModel.STATE_PLAY))
        elif event.key == pygame.K_ESCAPE:
            self.evManager.Post(StateChangeEvent(None))

    def intro_keys(self, event):
        """
        Handles intro keys.
        """

        if event.key in (pygame.K_SPACE, pygame.K_ESCAPE):
            self.evManager.Post(StateChangeEvent(None))

    def game_over_keys(self, event):
        """
        Handles game over keys.
        """

        if event.key in (pygame.K_SPACE, pygame.K_ESCAPE):
            self.evManager.Post(StateChangeEvent(None))

    def crash_keys(self, event):
        """
        Handles the emergency crash kart keys.
        """

        if event.key == pygame.K_ESCAPE:
            self.evManager.Post(QuitEvent())
        elif event.key == pygame.K_RETURN:
            self.evManager.Post(StateChangeEvent(None))
