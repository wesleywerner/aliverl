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
    
    def xy(self):
        """ Returns (x, y) """
        return (self.x, self.y)
        
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
    
    def object_by_name(self, name):
        """ Return a tile by name. """
        search = [ti for ti in self.objects if ti.name == name]
        if search:
            return search[0]
        
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
        
        # out of bounds?
        if (nx < 0) or (nx > self.width - 2) or \
            (ny < 1) or (nx > self.height - 1):
                return False
        
        # detect object collisions
        for obj in self.objects:
            if obj is not tile and \
                obj.visible and \
                obj.x == nx and obj.y == ny:
                # commented out: always bump into objects.
                #if obj.prop('blocks'):
                if hit_callback is not None:
                    if hit_callback(self, obj):
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
        # clear 
        self.object_canvas.fill((255, 0, 255))
        for obj in [ e for e in self.objects if e is not None ]:
            self.draw_object(obj)
        # draw the player last (z-order fix)
        self.draw_object(levelmap.object_by_name('player'))
    
    def draw_object(self, obj):
        """ draw this object to the object canvas. """
        if obj.visible:
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
    
    def action_object(self, target, is_finger_target=False):
        """ Queries the target object to do what it's properties define. 
        We only action map and tile actions here. """
        for action in target.props.keys():
            try:
                # finger
                if action.startswith('fingers'):
                    for f in [ e for e in self.objects 
                                if e.name == target.props[action] ]:
                        self.action_object(f, is_finger_target=True)
                
                # (fingered targets only)
                if is_finger_target and \
                    self.object_by_name('player').xy() != target.xy() and \
                    action.startswith('on_finger'):
                    finger_actions = target.props[action].split('=')
                    
                    if finger_actions[0].startswith('transmute'):
                        # value could be 1 value (one-way transmute)
                        # or a csv list (rotate transmute)
                        options = finger_actions[1].split(',')
                        if len(options) == 1:
                            transmute_id = int(options[0])
                        else:
                            print(options)
                            if str(target.tid) in options:
                                # rotate the list with the current
                                # index as offset. 
                                idx = options.index(str(target.tid)) - 1
                                transmute_id = int(list(options[idx:] + options[:idx])[0])
                                print('rotating to idx %s (%s)' % (idx, transmute_id))
                            else:
                                # use first index
                                transmute_id = int(options[0])
                        target.tid = transmute_id
                        target.isdirty = True
                        
            except IndexError:
                print('the tile named %s has a bad property set. \
                ' % (target.name,) )
        
def test_hit_callback(mapengine, tile):
    """ Test for hitting blocking objects or tiles. """
    print tile
    mapengine.action_object(tile)
    
    # we must return if this hit blocked us
    try:
        return mapengine.tile_props(tile.tid)['blocks'] == '1'
    except KeyError:
        # defaults missing "blocks" property to non blocking.
        return False
    
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
                    p = levelmap.object_by_name('player')
                    levelmap.move_tile(p, 1, 0, test_hit_callback)
                if event.key == K_h:
                    p = levelmap.object_by_name('player')
                    levelmap.move_tile(p, -1, 0, test_hit_callback)
                if event.key == K_j:
                    p = levelmap.object_by_name('player')
                    levelmap.move_tile(p, 0, 1, test_hit_callback)
                if event.key == K_k:
                    p = levelmap.object_by_name('player')
                    levelmap.move_tile(p, 0, -1, test_hit_callback)
                if event.key == K_b:
                    p = levelmap.object_by_name('player')
                    levelmap.move_tile(p, -1, 1, test_hit_callback)
                if event.key == K_n:
                    p = levelmap.object_by_name('player')
                    levelmap.move_tile(p, 1, 1, test_hit_callback)
                if event.key == K_y:
                    p = levelmap.object_by_name('player')
                    levelmap.move_tile(p, -1, -1, test_hit_callback)
                if event.key == K_u:
                    p = levelmap.object_by_name('player')
                    levelmap.move_tile(p, 1, -1, test_hit_callback)
                if event.key == K_ESCAPE:
                    running = False
