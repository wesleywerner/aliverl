# See the file COPYING for the license.
import sys
import pygame
from pygame.locals import *
from character import Character
from level import Level
from objects import LevelObjects
from bump import Bump
import input
import trace
import audio
import messages
from ui import UxManager
import stats
import states
import resources

class AliveRL(object):
    """ This is where all game state objects live. """
    
    def __init__ (self):
        """ Initialise the game state. """
        self.level = Level()
        self.objects = LevelObjects(self)
        self.audio = audio.Audio()
        self.messages = messages.Messages()
        self.input = input.Input(self)
        # ui manager handles drawing and clicking widgets
        self.ui = UxManager('images/buttons.png', (500, 500), 
                            self.input.handler )
        # setup the state machine
        self.state = states.MachineState( [states.play,] )
        # load some resources
        self.res = resources.Resources()
    
def run ():
    """ Become... Alive! """

    def draw_play ():
        """ draws all things states.play """
        # blit the map tiles
        screen.blit(
                    alive.level.tile_canvas, 
                    (288, 0)
                    )
        # blit npc and player characters
        screen.blit(
                    alive.level.character_canvas, 
                    (288, 0)
                    )
        # blit game messages
        screen.blit(
                    alive.messages.canvas, 
                    (16, 352)
                    )
        # blit player stats box
        screen.blit(
                    stats.draw_stats(
                                    alive.objects.player, 
                                    alive.level),
                    (10, 0) 
                    )
    
    def draw_menu():
        """ draws all things states.menu """
        pass
        
    def draw_dialog():
        """ draws all things state.dialog """
        pass
        #TODO draw a background for dialogs state, add it to resources.py
        #TODO render some kind of dialog words using helper.renderLines

    def input_play(event):
        """ handles all things states.play """
        if event.type == KEYDOWN:
            # Escape to the menu
            if event.key == K_ESCAPE:
                alive.state.pop()
                alive.ui.set_context(alive.state.peek())
            # test for movement
            alive.objects.move_player_phase(event)

    def input_menu(event):
        """ handles all things states.play """
        if event.type == KEYDOWN:
            # Exit
            if event.key == K_ESCAPE:
                alive.state.pop()
                alive.ui.set_context(alive.state.peek())
            elif event.key == K_SPACE:
                alive.state.push(states.play)
                alive.ui.set_context(alive.state.peek())
    
    print('starting the hamster...')
    print('init pygame...')
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption('Alive')
    screen = pygame.display.set_mode( (800, 512) )
    clock = pygame.time.Clock()
    print('make the game engine Alive...')
    # we can only load() these after pygame init() :]
    alive = AliveRL()
    alive.level.load()
    alive.objects.load()
    alive.messages.load()
    # load ui widget and set the first context
    alive.ui.load()
    alive.ui.setup()
    alive.ui.set_context(alive.state.peek())
    alive.ui.refresh_canvas()
    # load addition resources
    alive.res.load()
    #alive.audio.playmusic(0)
    running = True
    
    while running:
        
        # an empty stack means permadeath
        if not alive.state.peek():
            running = False
            return
            
        # test for widgets mouse hover & hotkey click
        alive.ui.hover( pygame.mouse.get_pos() )
        # render the characters canvas (in memory of course)
        alive.level.draw_characters(alive.objects.characters)
        # blit the current state background
        try:
            bg = alive.res.backgrounds[alive.state.peek()]
            screen.blit(bg, (0, 0))
        except:
            screen.blit(alive.res.defaultbg, (0, 0))
        # draw different things depending on current machine state
        try:
            {
                states.play: draw_play,
                states.menu: draw_menu,
                states.dialog: draw_dialog
            }.get(alive.state.peek(), None)()
        except TypeError:
            # there is no draw loop for this state
            pass
        
        # always blit ui widgets
        screen.blit(
                    alive.ui.canvas, (0, 0) 
                    )
        # always blit floating tooltips
        screen.blit(
                    alive.ui.tooltip_canvas, 
                    pygame.mouse.get_pos() 
                    )
        
        # always flip and limit fps
        pygame.display.flip()
        clock.tick(30)

        # handle input
        for event in pygame.event.get():
            
            # always handle window closing events
            if event.type == pygame.QUIT:
                running = False
            
            # always send hotkey to widgets
            if event.type == pygame.KEYDOWN:
                alive.ui.click(event.unicode)

            # handle input depending on current machine state
            try:
                {
                    states.play: input_play,
                    states.menu: input_menu
                }.get(alive.state.peek(), None)(event)
            except TypeError:
                # there is no draw loop for this state.
                # so let us handle the Escape key for this case.
                if event.type == pygame.KEYDOWN and event.key == K_ESCAPE:
                    alive.state.pop()
                    alive.ui.set_context(alive.state.peek())
            
            # MOUSE
            if event.type == MOUSEBUTTONDOWN:
                # handle widget click
                alive.ui.click(event.pos)
            elif event.type == MOUSEBUTTONUP or event.type == KEYUP:
                # unfocus any clicked buttons
                alive.ui.unclick()

if __name__ == '__main__':
    run()
