# this tech demo features custom ui elements.
#
# buttons:
#       drawn from greyscale images
#       allow change of hue
#
# attributes:
#       code, a unique identifier this control signals when actioned.
#       enabled, do hover, click and hotkeys if true.
#       hotkey, for keyboard awesomeness.
#       position, (x, y) where to draw on screen. neg values for ralign snap.
#       imagemapsource, (x, y) the coords in the theme image map.
#       size, (w, h) this element width and height
#       ishovering, true or false
#       
# 
# signals note:
#       instead of letting these controls handle what happens when
#       actioned, we should use an event system to pass signals back
#       to the host. they can decide what to do from there.
#
# efficiancy note:
#       no need to store each element's bitmap. we draw it's image
#       from a single imagemap.
#
import sys
import time
import pygame
from pygame.locals import *
import helper
import color
import states

class UxBase(object):
    """ The base class that UI elements are based on. """
    def __init__(
            self, code, title, description, 
            enabled, hotkey, source_rect, 
            dest_rect):
        self.code = code
        self.context = None
        self.title = title
        self.description = description
        self.enabled = enabled
        self.hotkey = hotkey
        self.dest_rect = dest_rect
        self.source_rect = source_rect
        self.ishovering = False
        self.isclicked = False
    
    def istarget(self, position):
        """ determines if the given position (x, y) is over us.
        position can also be int, the key code."""
        target_type = type(position)
        if target_type is tuple:
            return self.dest_rect.collidepoint(position)
        else:
            return position == self.hotkey
    
    def hover(self, position):
        """ test if the given point hovers over us. """
        last_state = self.ishovering
        self.ishovering = self.istarget(position)
        # true means redraw this element
        return self.ishovering or self.ishovering != last_state
    
    def click(self, position):
        """ test if the given point is clicking us. """
        last_state = self.isclicked
        self.isclicked = self.istarget(position)
        # true means redraw this element
        return self.isclicked != last_state
       
class UxManager(object):
    """ Stores UI elements and handles drawing them.
    
    The context attribute allows us to limit actions on subsets
    of elements, i.e. 'main', 'menu', or 'options' screens.
    This attribute is optional, None is the default.
    
    use add() to populate with elements.
    Not unlike herding cats.
    """
    
    def __init__(self, theme, canvas_size, click_callback):
        self.context = None
        self.canvas_size = canvas_size
        self.theme = theme
        self.elements = []
        self.tooltip_area = None
        self.tooltip_canvas = None
        self.canvas = None
        self.imagemap = None
        self.imagemap_disabled = None
        self.imagemap_hover = None
        self.imagemap_clicked = None
        self.font = None
        self.click_callback = click_callback
    
    def load (self):
        self.font = pygame.font.Font('bitwise.ttf', 18)
        self.load_image_data()
    
    def context_elements(self):
        """ only return elements within our current context."""
        return [e for e in self.elements if e.context == self.context]
    
    def set_context(self, context):
        self.context = context
        self.refresh_canvas()
    
    def add(self, element, context=None):
        """ add an element to us. munch. """
        element.context = context
        self.elements.append(element)
    
    def remove(self, element):
        """ remove this one. thanks. """
        self.elements.remove(element)
    
    def hover(self, position, context=None):
        """ is there a sharp pointy thing hanging over our heads? """
        for element in self.context_elements():
            if element.hover(position):
                self.draw_element(element)
                self.draw_element_tooltip(element)
                return 
            self.clear_tooltips()
    
    def click(self, position):
        """ I hear it tickles when you're clicked the first time. """
        for element in self.context_elements():
            if element.click(position):
                self.draw_element(element)
                if self.click_callback is not None:
                    self.click_callback(self.context, element.code)
                return
    
    def unclick(self):
        """ is there a sharp pointy thing hanging over our heads? """
        for element in self.context_elements():
            element.isclicked = False
            self.draw_element(element)
            return 

    def refresh_canvas(self):
        """ tell all our elements to go draw themselves. """
        # set up the canvas with transparency key
        if self.canvas is None:
            self.canvas = pygame.Surface(
                                        self.canvas_size, 
                                        0, 
                                        32)
            self.tooltip_canvas = pygame.Surface(
                                        self.tooltip_area.size, 
                                        0, 
                                        32)
            self.tooltip_canvas.set_colorkey((255, 0, 255))
        self.clear_tooltips()
        self.canvas.set_colorkey((255, 0, 255))
        self.canvas.fill((255, 0, 255))
        for element in self.context_elements():
            self.draw_element(element)
    
    def draw_element(self, element):
        """ draw this one element onto our canvas. we will re-use this
        to only redraw dirty areas. """
        source_map = None
        if element.enabled == False:
            source_map = self.imagemap_disabled
        else:
            if element.isclicked:
                source_map = self.imagemap_clicked
            elif element.ishovering:
                source_map = self.imagemap_hover
            else:
                source_map = self.imagemap
        self.canvas.blit(
                    source=source_map,
                    dest=element.dest_rect,
                    area=element.source_rect
                    )
        #self.draw_element_text(element)
    
    def draw_element_text(self, element):
        """ draw an element's text. """
        # print the element's title
        timg = self.font.render(element.title, False, (255, 255, 255) )
        tpos = ( element.dest_rect.left + element.dest_rect.width, 
                element.dest_rect.top + 12)
        self.canvas.blit(source=timg, dest=tpos)
        
        # print the hotkey below
        timg = self.font.render(element.hotkey, False, (255, 255, 255) )
        tpos = (tpos[0], tpos[1] + 12)
        self.canvas.blit(source=timg, dest=tpos)
    
    def draw_element_tooltip(self, element):
        """ draw an element's tooltip. """
        if self.tooltip_area:
            #tip = pygame.Surface(
            #            self.tooltip_area.size,
            #            0, 32)
            # blue fill
            #tip.fill(color.yellow)
            timg = helper.renderTextBlock(
                        '%s\nhotkey: %s' % (element.description, 
                                                element.hotkey.upper()),
                        font=self.font,
                        antialias=True,
                        color=color.yellow,
                        background=color.blue
                        )
            #self.tooltip_canvas.blit( tip, (0, 16) )
            self.tooltip_canvas.blit( timg, (2, 18) )
    
    def clear_tooltips(self):
        """ Clears the tooltip canvas. """
        self.tooltip_canvas.fill((255, 0, 255))
        
    def load_image_data(self):
        """ load the theme's image data. 
        we use funky color manipulation to copy the map for other UI
        states, like disabled, hover, clicked or attention drawing. """

        # load her up
        self.imagemap = pygame.image.load(self.theme).convert_alpha()
        
        # copy and desaturate (disabled elements)
        self.imagemap_disabled = self.alter_hue(-1, self.imagemap)
        
        # same for hovering
        self.imagemap_hover = self.alter_hue(40, self.imagemap)
        
        # same for clicked
        self.imagemap_clicked = self.alter_hue(180, self.imagemap)
        
        # these hues work nicely:
        #    40, purple
        #    60, pink
        #   120, red
        #   140, amber
        #   180, yellow
        #   240, green
        #   300, cyan
    
    def alter_hue(self, hue, surface_to_clone):
        """ This cleverness rotates the pixel rgb values through 
        360 degress of hues. 
        thanks goes to:
        http://forum.chaos-project.com/index.php?topic=8400.0;wap2"""
        colorized_surface = surface_to_clone.copy()
        colorized_surface.lock()
        for x in range(colorized_surface.get_width()):
            for y in range(colorized_surface.get_height()):
                color = pygame.Color(*colorized_surface.get_at( (x, y) ))
                hsva = list(color.hsva)
                # hue of -1 will desaturate the pixel instead
                if hue == -1:
                    hsva[1] = 0
                else:
                    hsva[0] = (hsva[0] + hue) % 360.0
                color.hsva = hsva
                colorized_surface.set_at( (x, y), (color.r, color.g, color.b, color.a) )
        colorized_surface.unlock()
        return colorized_surface
    
    def setup(self):
        """ set up the UI for the game.
        This is the only method in the class that is not reusable. """
        self.tooltip_area = pygame.Rect(0, 0, 400, 100)
        
        # define all buttons for all contexts
        self.add(   UxBase( 
                    'stats', 
                    title='stats',
                    description='Display the full stats screen.',
                    enabled=True, 
                    hotkey='@', 
                    source_rect=pygame.Rect(0, 0, 32, 32),
                    dest_rect=pygame.Rect(246, 16, 32, 32)
                    )
        , context=states.play)
        
        # no point to pre render if we don't know our context yet :]
        #self.refresh_canvas()
        

if __name__ == "__main__":
    pygame.init()
    pygame.font.init()
    font = pygame.font.Font(pygame.font.get_default_font(), 8)
    pygame.display.set_caption('ui elements tech demo')
    screen = pygame.display.set_mode( (640, 480) )
    clock = pygame.time.Clock()
    UI = UxManager('images/buttons.png', (640, 480), None )
    
    # add a button
    button = UxBase( 'button1', 
                    title='ZAP',
                    description='',
                    enabled=True, 
                    hotkey='z', 
                    source_rect=pygame.Rect(0, 0, 32, 32),
                    dest_rect=pygame.Rect(12, 12, 32, 32)
                    )
    UI.add(button, context='main')
    
    # add another
    button = UxBase( 'button2', 
                    title='OBFUS',
                    description='',
                    enabled=True, 
                    hotkey='o', 
                    source_rect=pygame.Rect(32, 0, 32, 32),
                    dest_rect=pygame.Rect(12, 72, 32, 32)
                    )
    UI.add(button, context='main')
    
    for buttonsgalore in range(1, 5):
        UI.add(UxBase('button_' + str(buttonsgalore), 
                    title='OBFUS ' + str(buttonsgalore),
                    description='',
                    enabled=(True, False)[buttonsgalore % 4 == 0], 
                    hotkey=str(buttonsgalore), 
                    source_rect=pygame.Rect(64, 0, 32, 32),
                    dest_rect=pygame.Rect(12, 72 + (buttonsgalore * 32), 32, 32) )
                    )
    for buttonsgalore in range(5, 9):
        UI.add(UxBase('button_' + str(buttonsgalore), 
                    title='PING ' + str(buttonsgalore),
                    description='',
                    enabled=(True, False)[buttonsgalore % 4 == 0], 
                    hotkey=str(buttonsgalore), 
                    source_rect=pygame.Rect(98, 0, 32, 32),
                    dest_rect=pygame.Rect(132, 72 + ((buttonsgalore-4) * 32), 32, 32) )
                    )
    UI.refresh_canvas()
    running = True
    while running:
    
        # draw the UI
        clock.tick(30)
        screen.fill( (0, 0, 0) )
        screen.blit( UI.canvas, (0, 0) )
        pygame.display.flip()
        
        # hover test
        UI.hover( pygame.mouse.get_pos() )
        
        # check for input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == KEYDOWN:
            
                if event.key == K_ESCAPE:
                    running = False
                    
                elif event.key == K_UP:
                    UI.alter_hue(20)
                    UI.refresh_canvas()
                    
                elif event.key == K_DOWN:
                    UI.alter_hue(-20)
                    UI.refresh_canvas()
                
                elif event.key == K_SLASH:
                    if UI.context == None:
                        UI.set_context('main')
                    else:
                        UI.set_context(None)
                    UI.refresh_canvas()
                    print('our context is now %s' % (UI.context) )
                
                # send this hotkey to the UI manager
                UI.click(event.key)
                
            elif event.type == KEYUP:
                # send this hotkey to the UI manager
                UI.unclick(event.key)
                pass
                
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    UI.click(event.pos)
                    
            elif event.type == MOUSEBUTTONUP:
                UI.unclick(event.pos)
