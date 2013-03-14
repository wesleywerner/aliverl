class Character(object):
    """ Represents a level character, NPC or player. """
    
    def __init__ (self, level_data, definition, tile_size):
        """ Create a new Character from the given data.
        level_data contains the values for the current map.
        tile_size specifies (width, height) for the tile size.
        definition contains the AI stats (ATK,HP...)
        
        level_data sample:
        _* means we use this as an attribute_
        _x and y are translated to index positions_

        {
         "gid":58,
         "height":0,
         "name":"ICE",
         "properties":      *
            {
            "on_finger_1":"transmute=14"
            },
         "type":"",         *
         "width":0,
         "x":64,            *
         "y":512            *
        }
        
        definition sample:
        
        {
        "tile_id": 58,
        "name": "ICE",
        "attack": 1,
        "health": 2,
        "speed": 2,
        "healrate": 2,
        "stealth": 0,
        "mana": 5,
        "manarate": 2,
        "mode": "patrol"
        }
        """
        self.name = ''
        self.type = ''
        # apply definition file (overwrites level data for type and name)
        if definition:
            for k, v in definition.items():
                setattr(self, k, v)
        # add level specific data
        for k, v in level_data.items():
            if k in ('name', 'type'):
                # no overwrite existing values (level door names)
                if getattr(self, k) == '':
                    setattr(self, k, v)
            elif k in ('properties', 'x', 'y'):
                setattr(self, k, v)
        # rework position to indexed 
        self.x = self.x / tile_size[0]
        self.y = self.y / tile_size[1]
        # if no definition exists, add it anyway
        if 'tile_id' not in self.__dict__.keys():
            setattr(self, 'tile_id', level_data['gid'])
        # all other attributes
        self.visible = True
    
    def prop(self, key, default=None):
        """ Returns the value for the key property or default on KeyErrror. """
        try:
            return self.properties[key]
        except KeyError:
            return default
    
    def xy(self):
        return (self.x, self.y)
    
    def __str__(self):
        return '; '.join(['%s=%s' % (k, v) for k, v in self.__dict__.items()])
    
if __name__ == '__main__':
    print('character.py unit test')
    test_level_data = {
         "gid":58,
         "height":0,
         "name":"ICE",
         "properties":
            {
            "on_finger_1":"transmute=14"
            },
         "type":"",
         "width":0,
         "x":64,
         "y":512
        }
    test_definition = {
        "tile_id": 58,
        "name": "ICE",
        "attack": 1,
        "health": 2,
        "speed": 2,
        "healrate": 2,
        "stealth": 0,
        "mana": 5,
        "manarate": 2,
        "mode": "patrol"
        }
    npc = Character(test_level_data, test_definition, (32, 32))
    print(npc.properties, npc.type, npc.x, npc.y)
