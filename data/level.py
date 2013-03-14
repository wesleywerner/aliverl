# See the file COPYING for the license.
#
# This handles loading the map data from a json format.
# We build the map levels using Tiled (http://www.mapeditor.org/)
# and export it to json.
#
# note on the file format:
# + only have one tilelayer layer
# + only have one objectgroup layer
#

import json
import pygame
from pygame.locals import *

TILESET = 'maps/alive-tileset.png'

class MapTile(object):
    """ Stores tile information. """
    def __init__(self, tid, x, y, props):
        self.tid = tid
        self.x = x
        self.y = y
        self.blocks = 0
        self.last_x = x
        self.last_y = y
        self.props = props
        self.visible = True
        self.name = None
        try:
            self.blocks = self.props['blocks']
        except KeyError as err:
            pass
    
    def __str__(self):
        return 'tid (%s) %s: (%s/%s) %s' % (self.tid, self.name, self.x, self.y, self.props) 

    def xy(self):
        """ Returns (x, y) """
        return (self.x, self.y)
        
class Level(object):
    """ Stores the game map data. """
    
    def __init__ (self):
        """ Load the mapfile. """
        self.level = 1
        self.data = None
        self.height = 0
        self.width = 0
        self.tile_h = 0
        self.tile_w = 0
        self.tile_size = None
        self.tile_canvas = None
        self.character_canvas = None
        self.tiles = None
        self.per_row = None
        self.tileset = None
        self.load_level()
    
    def load_level(self):
        """ Loads the level data of level (int). """
        self.data = json.load(open('maps/level%s.json' % (self.level, )))
        self.height = self.data["height"]
        self.width = self.data["width"]
        self.tile_h = self.data["tileheight"]
        self.tile_w = self.data["tilewidth"]
        self.tile_size = (self.tile_w, self.tile_h)
        self.tile_canvas = None
        self.character_canvas = None
        self.tiles = [ [None] * self.width for x in xrange(self.height) ]
        self.per_row = self.data["tilesets"][0]["imagewidth"] / self.tile_w
        self.tileset = pygame.image.load(TILESET).convert_alpha()
        self.render_map()
    
    def object_layers(self):
        """ Returns a list of all objectgroup layers. """
        return [e for e in self.data['layers'] if e['type'] == 'objectgroup' ]
        
    def next_level(self):
        """ Jumps to the next level. """
        self.level += 1
        self.load_level()
    
    def tile_blocks(self, xy):
        """ Returns if the tile at (x, y) would block movement. """
        return self.tiles[xy[0]][xy[1]].blocks
        
    def tileset_xy(self, tid):
        """ Returns (x, y) tileset coordinates for the given tile id. """
        row = (tid-1) / self.per_row
        y = row * self.tile_h
        x = (tid - 1 - (row * self.per_row)) * self.tile_h
        return (x, y)
    
    def tile_props(self, tid):
        """ FIX: does our caller need a rewrite?
        Return a tile's properties dictionary. 
        Note this is not the same as the objectgroup properties. """
        try:
            #print(self.data["tilesets"][0]["tileproperties"], tid-1)
            return self.data["tilesets"][0]["tileproperties"][str(tid-1)]
        except:
            return {}

    def render_map(self):
        """ Renders the map tiles to the canvas attribute. """
        canvas_size = ( self.width * self.tile_w, 
                        self.height * self.tile_h )
        self.tile_canvas = pygame.Surface(
                        canvas_size, 
                        0, 32)
        self.tile_canvas.set_colorkey((255, 0, 255))
        self.tile_canvas.fill((255, 0, 255))
        tiledata = [e for e in self.data["layers"] if e["name"] == "map"][0]["data"]
        for y in range(self.height):
            for x in range(self.width):
                # tile index
                tid = tiledata[x + (y * self.height)]
                self.tiles[x][y] = MapTile( tid, x, y, 
                                            self.tile_props(tid) )
                # destination on target surface
                dest_rect = pygame.Rect(
                            (x * self.tile_w, y * self.tile_h), 
                            self.tile_size
                            )
                # area in source image
                area_rect = pygame.Rect(
                                self.tileset_xy(tid), 
                                self.tile_size)
                # draw the tile on the canvas
                self.tile_canvas.blit(
                                source=self.tileset,
                                dest=dest_rect,
                                area=area_rect
                                )
    
    def draw_characters(self, characters):
        """ Draw to the character_canvas. """
        if self.character_canvas is None:
            canvas_size = ( self.width * self.tile_w, 
                            self.height * self.tile_h )
            self.character_canvas = pygame.Surface(
                            canvas_size, 
                            0, 32)
            self.character_canvas.set_colorkey((255, 0, 255))
        
        # clear 
        self.character_canvas.fill((255, 0, 255))
        
        # draw
        for obj in [ e for e in characters if e.visible]:
            # destination on target surface
            dest_rect = pygame.Rect(
                        (obj.x * self.tile_w, 
                        (obj.y - 1) * self.tile_h), 
                        self.tile_size
                        )
            # area in source image
            area_rect = pygame.Rect(
                            self.tileset_xy(obj.tile_id), 
                            self.tile_size)
            # draw the tile on the canvas
            self.character_canvas.blit(
                            source=self.tileset,
                            dest=dest_rect,
                            area=area_rect
                            )        
        
        # draw the player last (z-order fix)
        #self.draw_object(levelmap.object_by_name('player'))
            


   
if __name__ == '__main__':
    
    print('setup pygame')
    pygame.init()
    pygame.display.set_caption('map tech')
    screen = pygame.display.set_mode( (640, 640) )
    clock = pygame.time.Clock()
    print('loading map')
    levelmap = Level()
    levelmap.load_level()
    print('render map canvas')
    levelmap.render_map()
    print('running main loop')
    running = True
    
    x = pygame.image.load('images/background.png').convert_alpha()
    
    while running:
    
        # render
        clock.tick(30)
        screen.blit( x, (0, 0) )
        screen.blit( levelmap.tile_canvas, (0, 0) )
        pygame.display.flip()

        # handle input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
