# Handles bumping into things.
class Bump(object):
    """ Here be dragons... """
    
    def __init__ (self):
        """ Class initialiser """
        pass
    
    def bump(self, player, what, mapengine):
        """ player bumped into what. """
        
        
        # we must return if this blocks us
        try:
            return mapengine.tile_props(tile.tid)['blocks'] == '1'
        except KeyError:
            # defaults missing "blocks" property to non blocking.
            return False
