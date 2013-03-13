# See the file COPYING for the license.
# map.py
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

class MapTile(object):
    """ Stores tile information. """
    def __init__(self, tid, x, y, props):
        self.tid = tid
        self.x = x
        self.y = y
        self.type = None
        self.last_x = x
        self.last_y = y
        self.props = props
        self.isdirty = True
        self.visible = True
        self.name = None
    
    @classmethod
    def from_dict(cls, datadict, tile_w, tile_h):
        c = cls(
                datadict['gid'],
                datadict['x'] / tile_w,
                datadict['y'] / tile_h,
                datadict['properties']
                )
        c.type = datadict['type']
        c.name = datadict['name']
        return c
        
    def __str__(self):
        return '%s, %s, %s: (%s/%s) %s' % (self.tid, self.name, self.type, self.x, self.y, self.props) 
    
    def move(self, x_offset, y_offset):
        """ Move this tile to a new location. """
        self.last_x = self.x
        self.last_y = self.y
        self.x += x_offset
        self.y += y_offset
        self.isdirty = True
        
    def prop(self, prop_name):
        """ Return the tile property of prop_name, or None. """
        try:
            return self.props[prop_name]
        except:
            return None

class Map(object):
    """ Stores the game map data. """
    
    def __init__ (self, mapfile):
        """ Load the mapfile. """
        self.data = json.load(open(mapfile))
        self.height = self.data["height"]
        self.width = self.data["width"]
        self.tile_h = self.data["tileheight"]
        self.tile_w = self.data["tilewidth"]
        self.tile_size = (self.tile_w, self.tile_h)
        self.tile_canvas = None
        self.object_canvas = None
        self.tiles = [ [None] * self.width for x in xrange(self.height) ]
        self.objects = []
        self.per_row = self.data["tilesets"][0]["imagewidth"] / self.tile_w
        self.tileset = pygame.image.load('maps/alive-tileset.png').convert_alpha()
    
    def tileset_xy(self, tid):
        """ Returns (x, y) tileset coordinates for the given tile id. """
        row = (tid-1) / self.per_row
        y = row * self.tile_h
        x = (tid - 1 - (row * self.per_row)) * self.tile_h
        return (x, y)

    
    def tile_props(self, tid):
        """ Return a tile's properties dictionary. 
        Note this is not the same as the objectgroup properties. """
        try:
            return self.data["tilesets"][0]["tileproperties"][str(tid-1)]
        except:
            return {}
    
    def load_objects(self):
        """ Loads the map file objectgroup layer. """
        try:
            objs = [e for e in self.data["layers"] if e["type"] == "objectgroup"][0]["objects"]
        except IndexError:
            raise Exception('This map file does not contain a objectgroup layer. Load failed.')
        for obj in objs:
            self.objects.append( MapTile.from_dict( 
                            obj, self.tile_w, self.tile_h
                            ))
    
    def move_tile(self, tile, x_offset, y_offset, hit_callback):
        """ Moves the given tile with an offset. Handles blocking.
        Returns True if moved, False if not.
        calls hit_callback with the Tile we bump into."""
        
        nx = tile.x + x_offset
        ny = tile.y + y_offset
        
        # detect object collisions
        for obj in self.objects:
            if obj is not tile and \
                obj.visible and \
                obj.x == nx and obj.y == ny:
                # commented out: always bump into objects.
                if obj.prop('blocks'):
                    if hit_callback is not None:
                        hit_callback(self, obj)
                        return False
        
        # detect map tile collisions
        # not too sure why we need to -1 for y :p
        # guess the tile array is a snafu.
        try:
            target = self.tiles[nx][ny-1]
        except IndexError:
            return False
        if target.prop('blocks'):
            return target
        else:
            tile.move(x_offset, y_offset)
            return True
        
        
    def render_map(self):
        """ Renders the map tiles to the canvas attribute. """
        canvas_size = ( self.width * self.tile_w, 
                        self.height * self.tile_h )
        self.tile_canvas = pygame.Surface(
                        canvas_size, 
                        0, 32)
        self.tile_canvas.set_colorkey((255, 0, 255))
        self.tile_canvas.fill((255, 0, 255))
        tiledata = [e for e in self.data["layers"] if e["type"] == "tilelayer"][0]["data"]
        for y in range(self.height - 1):
            for x in range(self.width - 1):
                # tile index
                tid = tiledata[x + (y * self.height)]
                self.tiles[x][y] = MapTile( tid, x, y, 
                                            self.tile_props(tid) )
                # destination on target surface
                dest_rect = pygame.Rect(
                            (x * self.tile_w, y * self.tile_h), 
                            self.tile_size
                            )
                if tid in (7, 8):
                    print(self.tileset_xy(tid))
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
    
    def render_objects(self):
        """ Draw level objects to the object_canvas attribute.
        We only draw objects that have moved since last draw, dirty ones. """
        if self.object_canvas is None:
            canvas_size = ( self.width * self.tile_w, 
                            self.height * self.tile_h )
            self.object_canvas = pygame.Surface(
                            canvas_size, 
                            0, 32)
            self.object_canvas.set_colorkey((255, 0, 255))
        self.object_canvas.fill((255, 0, 255))
        for obj in [ e for e in self.objects if e is not None ]:
            if obj.isdirty:
                ## clear the last known location
                #self.object_canvas.fill(
                                        #(255, 0, 255),
                                        #pygame.Rect(
                                            #(obj.last_x * self.tile_w, (obj.last_y-1) * self.tile_h),
                                            #(self.tile_w, self.tile_h)
                                        #)
                                        #)
                if obj.visible:
                    # draw the new location
                    # destination on target surface
                    dest_rect = pygame.Rect(
                                (obj.x * self.tile_w, 
                                (obj.y - 1) * self.tile_h), 
                                self.tile_size
                                )
                    # area in source image
                    area_rect = pygame.Rect(
                                    self.tileset_xy(obj.tid), 
                                    self.tile_size)
                    # draw the tile on the canvas
                    self.object_canvas.blit(
                                    source=self.tileset,
                                    dest=dest_rect,
                                    area=area_rect
                                    )
    
    def remove_object(self, obj):
        """ Remove an object from the game screen. """
        obj.dirty = True
        obj.visible = False
        
def test_hit_callback(mapengine, tile):
    """ Test for hitting blocking objects or tiles. """
    print tile
    #mapengine.remove_object(tile)
    
if __name__ == '__main__':
    
    print('setup pygame')
    pygame.init()
    pygame.display.set_caption('map tech')
    screen = pygame.display.set_mode( (640, 640) )
    clock = pygame.time.Clock()
    print('loading map')
    levelmap = Map('maps/test.json')
    levelmap.load_objects()
    print('render map canvas')
    levelmap.render_map()
    print('running main loop')
    running = True
    
    x = pygame.image.load('images/background.png').convert_alpha()
    
    while running:
    
        # render
        clock.tick(30)
        #screen.fill( (0, 0, 0) )
        levelmap.render_objects()
        screen.blit( x, (0, 0) )
        screen.blit( levelmap.tile_canvas, (0, 0) )
        screen.blit( levelmap.object_canvas, (0, 0) )
        pygame.display.flip()

        # handle input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == KEYDOWN:
                if event.key == K_l:
                    p = levelmap.objects[0]
                    levelmap.move_tile(p, 1, 0, test_hit_callback)
                if event.key == K_h:
                    p = levelmap.objects[0]
                    levelmap.move_tile(p, -1, 0, test_hit_callback)
                if event.key == K_j:
                    p = levelmap.objects[0]
                    levelmap.move_tile(p, 0, 1, test_hit_callback)
                if event.key == K_k:
                    p = levelmap.objects[0]
                    levelmap.move_tile(p, 0, -1, test_hit_callback)
                if event.key == K_b:
                    p = levelmap.objects[0]
                    levelmap.move_tile(p, -1, 1, test_hit_callback)
                if event.key == K_n:
                    p = levelmap.objects[0]
                    levelmap.move_tile(p, 1, 1, test_hit_callback)
                if event.key == K_y:
                    p = levelmap.objects[0]
                    levelmap.move_tile(p, -1, -1, test_hit_callback)
                if event.key == K_u:
                    p = levelmap.objects[0]
                    levelmap.move_tile(p, 1, -1, test_hit_callback)
                if event.key == K_ESCAPE:
                    running = False
