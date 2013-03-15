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

class AliveRL(object):
    """ This is where all game state objects live. """
    
    def __init__ (self):
        """ Initialise the game state. """
        self.level = Level()
        self.objects = LevelObjects(self.level)
        self.audio = audio.Audio()
    
if __name__ == '__main__':
    
    print('starting the hamster')
    pygame.init()
    pygame.display.set_caption('Alive')
    screen = pygame.display.set_mode( (640, 640) )
    clock = pygame.time.Clock()
    alive = AliveRL()
    #alive.audio.playmusic(0)
    running = True
    
    # place inside the UI class that renders each loop
    x = pygame.image.load('images/background.png').convert_alpha()
    
    while running:
        
        # render
        alive.level.draw_characters(alive.objects.characters)
        clock.tick(30)
        screen.blit(x, (0, 0))
        screen.blit(alive.level.tile_canvas, (0, 0))
        screen.blit(alive.level.character_canvas, (0, 0))
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
                    if alive.objects.move_player_phase(event):
                        alive.objects.move_npc_phase()
