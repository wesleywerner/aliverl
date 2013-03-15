# loads the level object data, usually AI or NPC's, the Player character.

import json
from character import Character
import trace

class LevelObjects(object):
    """ Manages the AI objects on a game level. """
    
    def __init__ (self, level):
        """ load definition file as a dictionary. """
        self.level = level
        self.definition = json.load(open('ai.def'))
        self.characters = []
        self.player = None
        
        # Loads the characters from the level data
        for layer in self.level.object_layers():
            for obj_data in layer['objects']:
                definition = None
                try:
                    definition = self.definition[str(obj_data['gid'])]
                except KeyError:
                    #trace.error('There is no ai.def entry for tile_id %s.' % (obj_data['gid']) )
                    pass
                char = Character(obj_data, definition, self.level.tile_size)
                self.characters.append(char)
                try:
                    if char.name == 'player':
                        self.player = char
                except AttributeError:
                    pass
        if self.player is None:
            trace.error('There is no "player" object in this level.')

    def xy(self):
        """ Returns (x, y) """
        return (self.x, self.y)
    
    def bump(self, a, b, is_finger_target=False):
        """ Bumps two characters together. 
        This could be a door, a switch, or another AI. """
        trace.write('# BUMP!\n\n \tA = ' + str(a) + '\n\n\tB = ' + str(b) )

        # 2. Combat
        if b.type == 'ai':
            print('#############')
            trace.write('COMBAT')
            return True
                    
        # 1. fire any triggers on the bumpee
        for action in b.properties.keys():
            try:
                action_value = b.properties[action]
                # finger somebody else
                if action.startswith('fingers'):
                    for f in [e for e in self.characters if e.name == action_value]:
                        self.bump(a, f, is_finger_target=True)
                
                # show a message
                if action.startswith('message'):
                    trace.write(action_value)

                # fingered characters only
                if is_finger_target and \
                            self.player.xy() != b.xy() and \
                            action.startswith('on_finger'):
                    
                    # grab the finger actions
                    f_acts = action_value.split('=')
                    
                    # message from this finger action
                    if f_acts[0].startswith('message'):
                        trace.write(f_acts[1])
                    
                    if f_acts[0].startswith('give'):
                        give = f_acts[1].split(' ')
                        b.properties[give[0]] = ' '.join(give[1:])
                    
                    if f_acts[0].startswith('transmute'):
                        # value could be 1 value (one-way transmute)
                        # or a csv list (rotate transmute)
                        options = f_acts[1].split(',')
                        if len(options) == 1:
                            transmute_id = int(options[0])
                        else:
                            if str(b.tile_id) in options:
                                # rotate the list with the current
                                # index as offset. 
                                idx = options.index(str(b.tile_id)) - 1
                                transmute_id = int(list(options[idx:] + options[:idx])[0])
                                trace.write('rotating to idx %s (%s)' % (idx, transmute_id))
                            else:
                                # use first index
                                transmute_id = int(options[0])
                        b.tile_id = transmute_id

                # once shots actions (append once to any action)
                if action.endswith('once'):
                    del b.properties[action]
            
            except Exception as err:
                trace.error('The tile "%s" has a malformed property: %s \
                ' % (target.name, err) )
        

        
        # 3. Blocking map tiles
        try:
            # return if the tileset property blocks
            return self.level.tile_props(b.tile_id)['blocks']
        except KeyError:
            return False

    def move_character(self, character, x_offset, y_offset, bump_callback):
        """ Moves the character, handles blocking.
        Returns True if moved, False if not.
        calls bump_callback with the Tile we bump into."""
        
        nx = character.x + x_offset
        ny = character.y + y_offset
        
        # out of bounds?
        if (nx < 0) or (nx > self.level.width - 1) or \
            (ny < 1) or (nx > self.level.height - 1):
                return False
        
        # 1. detect object collisions
        for other in self.characters:
            if other is not character and \
                other.visible and other.xy() == (nx, ny):
                    if bump_callback is not None:
                        if bump_callback(character, other):
                            return False
        
        # 2. detect map collisions
        # not too sure why we need to -1 for y :p
        # guess the tile array is a snafu.
        if self.level.tile_blocks((nx, ny-1, )):
            return False
        else:
            character.x += x_offset
            character.y += y_offset
            return True


if __name__ == '__main__':
    print('objects.py unit test\n')