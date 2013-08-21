#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see http://www.gnu.org/licenses/.

import pygame
from const import *
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

                        if state == STATE_INTRO:
                            self.intro_keys(event)

                        elif state in (STATE_MENU_MAIN,
                                        STATE_MENU_SAVED,
                                        STATE_MENU_STORIES,
                                        STATE_MENU_OPTIONS):
                            self.menu_keys(event)

                        elif state == STATE_PLAY:
                            self.play_keys(event)

                        elif state == STATE_LEVEL_FAIL:
                            self.level_failed_keys(event)

                        elif state == STATE_DIALOG:
                            self.dialogue_keys(event)

                        elif state == STATE_CRASH:
                            self.crash_keys(event)

                        elif state == STATE_HELP:
                            self.help_keys(event)

                        elif state in (
                                        STATE_INFO_HOME,
                                        STATE_INFO_UPGRADES,
                                        STATE_INFO_WINS
                                        ):
                            self.info_keys(event)

                        else:
                            # allow escaping from unhandled states
                            self.evManager.Post(StateChangeEvent(None))
                    elif event.type == pygame.KEYUP:
                            self.evManager.Post(
                                InputEvent(char=None, clickpos=None))
        except:
            self.evManager.Post(CrashEvent())

    def play_keys(self, event):
        """
        Handles game play keys.
        """

        mods = pygame.key.get_mods()
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
        debug_keys = {
                    pygame.K_F2: 'animation cheatsheet',
                    pygame.K_F3: 'restart level',
                    pygame.K_F4: 'warp to next level',
                    pygame.K_F5: 'reveal map',
                    pygame.K_F6: 'heal all',
                    pygame.K_F7: 'demo map',
                    }
        if event.key == pygame.K_ESCAPE:
            self.evManager.Post(StateChangeEvent(None))
        elif event.key in movement.keys():
            self.evManager.Post(PlayerMoveRequestEvent(movement[event.key]))
        elif event.key == pygame.K_TAB:
            self.evManager.Post(TargetTileEvent())
        elif event.unicode == '>':
            self.model.warp_level()
        elif mods & pygame.KMOD_CTRL:
            if event.key in debug_keys.keys():
                self.evManager.Post(DebugEvent(debug_keys[event.key]))
            elif event.key == pygame.K_F1:
                trace.write('Debug commands')
                trace.write('^F2=render tile + animation cheatsheets')
                trace.write('^F3=restart the current level')
                trace.write('^F4=warp to the next level')
                trace.write('^F5=reveal the map')
                trace.write('^F6=heal health, power, and give 10 free upgrades')
                trace.write('^F7=warp to map building demo')
        elif event.key == pygame.K_F1:
            self.evManager.Post(StateChangeEvent(STATE_HELP))
        else:
            inEvent = InputEvent(char=event.unicode, clickpos=None)
            self.evManager.Post(inEvent)

    def dialogue_keys(self, event):
        """
        Handles dialogue keys.
        """

        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
            self.view.next_dialogue()
        elif event.key == pygame.K_ESCAPE:
            self.view.close_dialogue()

    def help_keys(self, event):
        """
        Handle help screen keys.
        """

        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
            self.view.next_dialogue()
        elif event.key == pygame.K_ESCAPE:
            self.view.close_dialogue()

    def menu_keys(self, event):
        """
        Handles menu keys.
        """

        if event.key == pygame.K_ESCAPE:
            self.evManager.Post(StateChangeEvent(None))
        elif event.key == pygame.K_F1:
            self.evManager.Post(StateChangeEvent(STATE_HELP))
        else:
            inEvent = InputEvent(char=event.unicode, clickpos=None)
            self.evManager.Post(inEvent)

    def intro_keys(self, event):
        """
        Handles intro keys.
        """

        if event.key in (pygame.K_SPACE, pygame.K_ESCAPE):
            self.evManager.Post(StateChangeEvent(None))

    def info_keys(self, event):
        """
        Handles info screen keys.
        """

        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            self.evManager.Post(StateChangeEvent(None))
        else:
            # pass keys to view listening for ui interaction
            inEvent = InputEvent(char=event.unicode, clickpos=None)
            self.evManager.Post(inEvent)

    def level_failed_keys(self, event):
        """
        Handles level failed keys.
        """

        if event.key in (pygame.K_SPACE, pygame.K_ESCAPE):
            self.evManager.Post(StateChangeEvent(None))
            self.model.restart_level()

    def crash_keys(self, event):
        """
        Handles the emergency crash kart keys.
        """

        if event.key == pygame.K_ESCAPE:
            self.evManager.Post(QuitEvent())
        elif event.key == pygame.K_RETURN:
            self.evManager.Post(StateChangeEvent(None))
