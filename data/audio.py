import pygame

class Audio(object):
    """ Controls music and sound for Alive. """
    
    def __init__ (self):
        """ Class initialiser """
        self.playlist = [
            'audio/universalnetwork2_real.xm',
            'audio/kbmonkey-ditty.it'
            ]
    
    def playmusic(self, level):
        pygame.mixer.music.fadeout(1000)
        pygame.mixer.music.load(self.playlist[level])
        pygame.mixer.music.play()
