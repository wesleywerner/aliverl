import os
import pygame   # used in TilesetParser only
import struct
from xml.etree import ElementTree

class ObjectHelper(object):
    """
    Provide functionality to print out object attributes.
    """
    
    def __repr__(self):
        return '%s has %s at 0x%x\n\n' % \
            ( type(self), ', '.join( [ '%s=%s' % (k, v) for k, v in self.__dict__.items() ] ) , 
            id(self) )

class TMXParser(ObjectHelper):
    """
    Parses tmx file data into sensible objects.
    Does not rely on any drawing libraries.
    """

    def __init__(self, filename):
        """
        filename(str) of the .tmx file to load.
        
        Note that layers are merged together.
        
        Attributes:
        
            version: map build version.
            orientation: orthogonal or isometric.
            width: map tiles wide.
            height: map tiles high.
            tile_width: tile pixel width.
            tile_height: tile pixel height.
            px_width: map pixel width   (width * tile_width).
            px_height: map pixel height (height * tile_height).
            filename: path of the file loaded.
            tilesets: list of tileset image sources.
            tilelayers: list of Tilelayer.
            objectgroups: list of Mapobjects.
        """
        
        with open(filename) as f:
            map = ElementTree.fromstring(f.read())
        
        self.version = map.attrib['version']
        self.orientation = map.attrib['orientation']
        self.width = int(map.attrib['width'])
        self.height  = int(map.attrib['height'])
        self.tile_width = int(map.attrib['tilewidth'])
        self.tile_height = int(map.attrib['tileheight'])
        self.px_width = self.width * self.tile_width
        self.px_height = self.height * self.tile_height
        self.filename = filename
        self.tilesets = []
        self.tilelayers = []
        self.objectgroups = []

        for tag in map.findall('tileset/image'):
            self.tilesets.append(Tileset(tag))

        for tag in map.findall('layer'):
            self.tilelayers.append(Tilelayer(tag))
        
        for tag in map.findall('objectgroup'):
            self.objectgroups.append(Objectgroup(tag, 
                                    (self.tile_width, self.tile_height)))
    
    def tilesize(self, multiplier=1):
        """
        Return (tile_width, tile_height).
        """
        
        return (self.tile_width * multiplier, self.tile_height * multiplier)
        

class Tileset(ObjectHelper):
    """
    Stores tmx tileset information.
    """

    def __init__ (self, tag):
        self.source = tag.attrib['source']
        self.width = int(tag.attrib['width'])
        self.height = int(tag.attrib['height'])
        if 'trans' in tag.attrib.keys():
            self.trans = tag.attrib['trans']
        else:
            self.trans = 'ff00ff'
            print('no transparency key set for this tmx map. Using magenta.')
            
        

class Tilelayer(ObjectHelper):
    """
    Stores tmx map layer data.
    
    """

    def __init__ (self, tag):
        self.name = tag.attrib['name']
        self.width = int(tag.attrib['width'])
        self.height = int(tag.attrib['height'])
        
        data = tag.find('data')
        self.encoding = data.attrib['encoding']
        self.compression = data.attrib['compression']
        data = data.text.strip()
        data = data.decode('base64').decode('zlib')
        data = struct.unpack('<%di' % (len(data)/4,), data)
        self.data = data
        assert len(data) == self.width * self.height
        
    def at(self, pos):
        """
        Return the gid at the given (x, y) index coordinate.
        """
        
        return self.data[pos[0] + (pos[1] * self.width)]
        
        
class Objectgroup(ObjectHelper):
    """
    Stores a list of map objects.
    """

    def __init__ (self, tag, tilesize):
        """
        Create an object group from xml tag.
        tilesize is (w, h).
        """
        
        self.name = tag.attrib['name']
        self.width = int(tag.attrib['width'])
        self.height = int(tag.attrib['height'])
        self.container = []
        for tag in tag.findall('object'):
            self.container.append(Mapobject(tag, tilesize))

    def add(self,n,k,comment):
        self.container.append([n,k,comment])

    def __str__(self):
        return str(self.container)

    def __repr__(self):
        return str(self.container)

    def __getitem__(self, key):
        return self.container[key]

    def __len__(self):
        return len(self.container)        


class Mapobject(ObjectHelper):
    """
    Stores a map object.
    Attributes:
    
        name: object name as given in the map editor.
        gid: graphic id
        px: pixel x position
        py: pixel y position
        x: map x position (index)
        y: map y position (index)
        properties: dict of map defined propeties
    """

    def __init__ (self, tag, tilesize):
        """
        Create this item from a xml tag.
        tilesize is (w, h)
        """
        
        if 'name' in tag.attrib.keys():
            self.name = tag.attrib['name']
        else:
            self.name = 'Unamed'
        if 'type' in tag.attrib.keys():
            self.type = tag.attrib['type']
        else:
            self.type = ''
        self.gid = int(tag.attrib['gid'])
        self.px = int(tag.attrib['x'])
        self.py = int(tag.attrib['y'])
        self.x = self.px / tilesize[0]
        self.y = self.py / tilesize[1]
        self.properties = {}
        for prop in tag.findall('properties/property'):
            self.properties[prop.attrib['name']] = prop.attrib['value']
    
    def getpixelxy(self):
        """
        Return (self.px, self.py).
        """
        
        return (self.px, self.py)
        
    def getxy(self):
        """
        Return (self.x, self.y)
        """

        return (self.x, self.y)

    def setxy(self, xy):
        """
        Set a new (x, y)
        """
        
        self.x, self.y = xy


class TilesetParser(dict):
    """
    Parses an image into subsets for easy reference.
    Relies on pygame to load images.
    you may use len() on this object to get the number of tiles.
    """
    
    def __init__(self, filename, tilesize, colorkey):
        """
        filename(str) of the image to load.
        tilesize((x, y)) of each tile size.
        colorkey((r, g, b)) of the transparency key. no alpha here.
        """
        
        self._tiles = {}
        image = pygame.image.load(filename).convert()
        image.set_colorkey(colorkey)
        w, h = image.get_size()
        w, h = (w / tilesize[0], h / tilesize[1])
        
        for y in range(0, h):
            for x in range(0, w):
                gid = x + (y * w) + 1
                self._tiles[gid] = image.subsurface(
                                    pygame.Rect(
                                            (x * tilesize[0], y * tilesize[1]), 
                                            tilesize))
        
    def __getitem__(self, gid):
        """
        Get a tile image by graphic index.
        """

        if gid in self._tiles.keys():
            return self._tiles[gid]
    
    def __len__(self):
        """
        Return the number of image tiles.
        """
        
        return len(self._tiles)


if __name__ == '__main__':
    import pygame
    pygame.init()
    
    def test_tilsetparser():
        screen = pygame.display.set_mode((640, 32))
        tsp = TilesetParser('stories/1-in-the-beginning/alive-tileset.png', (32, 32), (255, 0, 255))
        print('loaded ', len(tsp), 'tiles')
        print('showing the first 20')
        for x in range(1, 20):
            screen.blit(tsp[x], ((x-1)*32, 0))
            pygame.display.flip()
    
    def test_tmxparser():
        screen = pygame.display.set_mode((640, 32))
        tmx = TMXParser('stories/1-in-the-beginning/level1.tmx')
        for t in tmx.tilesets:
            print(t)
        for td in tmx.tilelayers:
            print(td.at((0, 0)))
            print(td.at((1, 0)))
            print(td.at((0, 1)))
            print(td.at((1, 1)))
        for o in tmx.objectgroups:
            print(o)
    
    def test_tmxrendering():
        screen = pygame.display.set_mode((640, 480))
        tsp = TilesetParser('stories/1-in-the-beginning/alive-tileset.png', 
                            (32, 32), (255, 0, 255))
        tmx = TMXParser('stories/1-in-the-beginning/level1.tmx')
        # draw tiles
        for y in range(tmx.height):
            for x in range(tmx.width):
                for layer in tmx.tilelayers:
                    gid = layer.at((x, y)) 
                    tile = tsp[gid]
                    if tile:
                        screen.blit(tile, 
                                    (x * tmx.tile_width, y * tmx.tile_height))
        # draw objects
        for grp in tmx.objectgroups:
            for obj in grp:
                tile = tsp[obj.gid]
                if tile:
                    x = (obj.x * tmx.tile_width)
                    # a bug in the map editor
                    # saves the y position for objects 
                    # one tile too much
                    y = (obj.y * tmx.tile_height) - tmx.tile_height
                    screen.blit(tile, (x, y))
                
        # flip the bird
        pygame.display.flip()
        while True:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
        
    test_tmxparser()
    #test_tilsetparser()
    test_tmxrendering()
