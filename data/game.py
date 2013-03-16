# See the file COPYING for the license.
import sys
import pygame
from pygame.locals import *
from character import Character
from level import Level
from objects import LevelObjects
from bump import Bump
import trace
import audio
from messages import Messages
import stats

class AliveRL(object):
    """ This is where all game state objects live. """
    
    def __init__ (self):
        """ Initialise the game state. """
        self.level = Level()
        self.objects = LevelObjects(self)
        self.audio = audio.Audio()
        self.messages = Messages()
        
    
if __name__ == '__main__':
    
    print('starting the hamster')
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption('Alive')
    screen = pygame.display.set_mode( (800, 512) )
    clock = pygame.time.Clock()
    alive = AliveRL()
    #alive.audio.playmusic(0)
    running = True
    
    # place inside the UI class that renders each loop
    x = pygame.image.load('images/playscreen.png').convert_alpha()
    
    while running:
        
        # render
        alive.level.draw_characters(alive.objects.characters)
        clock.tick(30)
        screen.blit(x, (0, 0))
        screen.blit(alive.level.tile_canvas, (288, 0))
        screen.blit(alive.level.character_canvas, (288, 0))
        screen.blit(alive.messages.canvas, (16, 352))
        screen.blit(stats.draw_stats(alive.objects.player, alive.level),
                    (10, 54) )
        pygame.display.flip()
        
        # handle input
        #for event in pygame.event.get():
        event = pygame.event.wait()
        if event:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                else:
                    alive.objects.move_player_phase(event)
