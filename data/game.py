# See the file COPYING for the license.
import sys
import pygame
from pygame.locals import *
from character import Character
from level import Level
from objects import LevelObjects
from bump import Bump
import input
import trace
import audio
from messages import Messages
from ui import UxManager
import stats
import states
import resources

class AliveRL(object):
    """ This is where all game state objects live. """
    
    def __init__ (self):
        """ Initialise the game state. """
        self.level = Level()
        self.objects = LevelObjects(self)
        self.audio = audio.Audio()
        self.messages = Messages()
        self.input = input.Input(self)
        # ui manager handles drawing and clicking widgets
        self.ui = UxManager('images/buttons.png', (500, 500), 
                            self.input.handler )
        # setup the state machine
        self.state = states.MachineState( [states.menu, states.play] )
        # load some resources
        self.res = resources.Resources()
    
    def run (self):
        """ Become... Alive! """
        print('starting the hamster...')
        print('init pygame...')
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption('Alive')
        screen = pygame.display.set_mode( (800, 512) )
        clock = pygame.time.Clock()
        print('make the game engine Alive...')
        # we can only load() these after pygame init() :]
        alive = AliveRL()
        alive.level.load()
        alive.objects.load()
        alive.messages.load()
        alive.ui.load()
        alive.ui.setup()
        alive.res.load()
        alive.audio.playmusic(0)
        running = True
        
        # place inside the UI class that renders each loop
        #x = pygame.image.load('images/playscreen.png').convert_alpha()
        
        while running:
            
            # an empty stack means permadeath
            if not alive.state.peek():
                running = False
                return
                
            # test for widgets mouse hover & hotkey click
            alive.ui.hover( pygame.mouse.get_pos() )
            # draw the characters canvas
            alive.level.draw_characters(alive.objects.characters)
            # blit the current state background
            bg = alive.res.backgrounds[alive.state.peek()]
            if bg:
                screen.blit(bg, (0, 0))
            
            # draw different things depending which state we are in
            
            # blit the map tiles
            screen.blit(alive.level.tile_canvas, (288, 0))
            # blit the characters
            screen.blit(alive.level.character_canvas, (288, 0))
            screen.blit(alive.messages.canvas, (16, 352))
            screen.blit(stats.draw_stats(alive.objects.player, alive.level),
                        (10, 0) )   # (10, 54)
            screen.blit(alive.ui.canvas, (0, 0) )
            screen.blit(alive.ui.tooltip_canvas, pygame.mouse.get_pos() )
            pygame.display.flip()

            # limit fps
            clock.tick(30)
            
            # handle input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    # send as hotkey to the UI manager
                    alive.ui.click(event.unicode)
                    # Escape the loop
                    if event.key == K_ESCAPE:
                        running = False
                    # test for movement keys
                    alive.objects.move_player_phase(event)
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        alive.ui.click(event.pos)
                elif event.type == MOUSEBUTTONUP or event.type == KEYUP:
                    alive.ui.unclick()

if __name__ == '__main__':
    test = AliveRL()
    test.run()
