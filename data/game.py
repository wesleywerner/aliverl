# See the file COPYING for the license.
import map
import pygame
from pygame.locals import *

class Alive(object):
    """ This is where all game state objects live. """
    
    def __init__ (self):
        """ Initialise the game state. """
        self.map = None
        self.level = 1
    
    def levelup(self):
        """ Move the state to the next level. """
        self.level += 1
        self.map = map.Map('maps/level%s' % (self.level,) )
        self.map.render()
    
if __name__ == '__main__':
    
    print('loading map')
    levelmap = Map('maps/test.map')
    print('setup pygame')
    pygame.init()
    pygame.display.set_caption('map tech')
    screen = pygame.display.set_mode( (640, 640) )
    clock = pygame.time.Clock()
    print('render map canvas')
    levelmap.render()
    print('running main loop')
    running = True
    while running:
    
        # render
        clock.tick(30)
        screen.fill( (0, 0, 0) )
        screen.blit( levelmap.canvas, (0, 0) )
        pygame.display.flip()

        # handle input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
