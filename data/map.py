# See the file COPYING for the license.
# map.py
#
# This handles loading the map data from a json format.
# We build the map levels using Tiled (http://www.mapeditor.org/)
# and export it to json.
#
# note about the json file format:
#   [tilesets][x][tileproperties] use dictionary lookup
#   for a tile by index - 1
import json
import time
import pygame
from pygame.locals import *

class Map(object):
    """ Stores the game map data. """
    
    def __init__ (self, mapfile):
        """ Load the mapfile. """
        self.data = json.load(open(mapfile))
        self.height = self.data["height"]
        self.width = self.data["width"]
        self.tileheight = self.data["tileheight"]
        self.tilewidth = self.data["tilewidth"]
        self.canvas = None
        self.blocks = [ [0] * self.width for x in xrange(self.height) ]
        self.per_row = self.data["tilesets"][0]["imagewidth"] / self.tilewidth
    
    def render(self):
        """ Renders the map tiles to a returned pygame surface. """
        canvas_size = ( self.width * self.tilewidth, 
                        self.height * self.tileheight )
        self.canvas = pygame.Surface(canvas_size, pygame.SRCALPHA, 32)
        tiledata = [e for e in self.data["layers"] if e["name"] == "map"][0]["data"]
        try:
            tileprops = self.data["tilesets"][0]["tileproperties"]
        except:
            pass
        tileset = pygame.image.load('maps/alive-tileset.png').convert_alpha()
        for y in range(self.height - 1):
            for x in range(self.width - 1):
                # tile index
                index = x + (y * self.height)
                tileid = tiledata[index]
                # is it blockable?
                try:
                    self.blocks[x][y] = int(tileprops[str(tileid-1)]['blocks'])
                    #print('blocks %s/%s' % (x, y) )
                except:
                    pass
                # destination on target surface
                dest_rect = pygame.Rect(
                            (x * self.tilewidth, y * self.tileheight), 
                            (self.tilewidth, self.tileheight)
                            )
                # area in source image
                row = tileid / self.per_row
                ty = row * self.tileheight
                tx = (tileid - 1 - (row * self.per_row)) * self.tileheight
                area_rect = pygame.Rect(
                            (tx, ty), 
                            (self.tilewidth, self.tileheight))
                self.canvas.blit(
                                source=tileset,
                                dest=dest_rect,
                                area=area_rect
                                )
    
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
