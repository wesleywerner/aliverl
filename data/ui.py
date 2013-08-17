#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see http://www.gnu.org/licenses/.
#
# Wesley Werner 2013
# This is a basic UI elements module for pygame.
# Button elements draw their selves from a png image.
# The manager handles their hover and fires a callback on click.

import pygame
import color


class UxButton(object):
    """
    A button that handles drawing itself and hover and click events.

    rect:
        The location on the screen to draw this ux.
        It is a PyGame Rect object, you may also give a (x, y, w, h) tuple
        in which case it will be converted for you.

    image_rect:
        A similar type as rect that defines the ux image on an image map.
        This points to the "normal" state image. Other state images
        are derived from this one. The order of these images on the map
        follow follow: normal - hover - clicked - disabled

    code:
        Unique identifier by which to recognize this ux in callbacks.

    hotkey:
        A string character or keycode that will pass the click.

    enabled:
        Determines if the disabled image is drawn, and if this ux
        responds to hover and click events.

    border_color:
        Draws a thin border around this ux, or None.

    context:
        The context under which this ux lives within the containing UxManager.
        This ux will only be visible and interactible if it's context
        matches that of the UxManager.

        It may be a single value, or a list of values. Your value will be
        converted to a list if it is not one already.

    data:
        Stores custom user data.

    visible:
        Determines if the widget will draw itself.

    """

    def __init__(self,
                rect=None,
                image_rect=None,
                code='',
                hotkey=None,
                enabled=True,
                border_color=None,
                context=None
                ):
        if type(rect) is tuple or type(rect) is list:
            self.rect = pygame.Rect(*rect)
        else:
            self.rect = rect
        if type(image_rect) is tuple or type(rect) is list:
            self.image_rect = pygame.Rect(*image_rect)
        else:
            self.image_rect = image_rect
        self.code = code
        self.hotkey = hotkey
        self.enabled = enabled
        self.border_color = border_color
        if type(context) is list:
            self.context = context
        else:
            self.context = [context]
        self.ishovering = False
        self.isclicked = False
        self.hotkey_image = None
        self.data = None
        self.visible = True

    def _istarget(self, position):
        """
        Determines if the given position is over us.
        Position can be a (x, y) tuple or a hotkey.
        """

        if type(position) is tuple:
            return self.rect.collidepoint(position)
        else:
            return position == self.hotkey

    def hover(self, position):
        """
        Test if the given point hovers over us.
        Returns True if our hover state has changed.
        """

        # last_state allows us to not retrigger an already hovered ux
        last_state = self.ishovering
        self.ishovering = self._istarget(position)
        return self.ishovering != last_state

    def click(self, position):
        """
        Test if the given point is clicking us.
        """

        # last_state allows us to not retrigger an already clicked ux
        last_state = self.isclicked
        self.isclicked = self._istarget(position)
        return self.isclicked != last_state

    def calculated_rect(self):
        """
        Calculates our source rectangle from our state.
        """

        # normal - hover - clicked - disabled
        x_offset = 0
        if self.enabled:
            if self.isclicked:
                # 3rd image is clicked
                x_offset = 2
            elif self.ishovering:
                # 2nd image is hovering
                x_offset = 1
        else:
            # 4th image is disabled
            x_offset = 3
        return pygame.Rect(self.image_rect.left +
            (x_offset * self.image_rect.width),
            self.image_rect.top,
            self.image_rect.width,
            self.image_rect.height
            )

    def draw(self, source, target):
        """
        Draw ourselves onto target from the source surface.
        """

        this_rect = self.calculated_rect()
        target.blit(source, self.rect, this_rect)
        if self.enabled and self.hotkey_image:
            target.blit(self.hotkey_image, self.rect.move(38, 17))
        if self.border_color:
            pygame.draw.rect(target, self.border_color, self.rect, 1)


class UxMovingButton(UxButton):
    """
    A button that has a destination position, and an update() method to step
    towards this position to give a motion effect.

    """

    def __init__(self,
                rect=None,
                image_rect=None,
                code='',
                hotkey=None,
                enabled=True,
                border_color=None,
                context=None,
                ):
        super(UxMovingButton, self).__init__(
            rect, image_rect, code, hotkey, enabled, border_color, context)
        self.destination = None
        self.destinations = {}
        self.overlay = None

    def store_destination(self, x, y, key):
        """
        Store a destination to move towards as a key.
        You may pass None to x or y to preserve the button's current value for it.

        """

        self.destinations[key] = pygame.Rect(
            (x is None and self.rect.left or x,
            y is None and self.rect.top or y),
            self.rect.size)

    def recall_destination(self, key):
        """
        Recall a previously stored destination.

        """

        if self.destinations.has_key(key):
            self.destination = self.destinations[key]

    def update(self, manager_context):
        """
        Step the button position towards destination.

        """

        if self.destination:
            x_diff = self.destination.left - self.rect.left
            y_diff = self.destination.top - self.rect.top
            self.rect = self.rect.move(int(x_diff / 10), int(y_diff / 10))

        if not manager_context in self.context and self.visible:
            self.visible = self.rect != self.destination

    def draw(self, source, target):
        """
        Draw ourselves onto target from the source surface.
        """

        this_rect = self.calculated_rect()
        target.blit(source, self.rect, this_rect)
        if self.overlay:
            target.blit(self.overlay, self.rect)

class UxTabButton(UxButton):
    """
    A button that acts like a tab control.
    It does not draw a disabled state.
    Unclick events do not affect us either.
    It has an extra attribute, group, which will unselect any other
    tab buttons in the same group on click (handled by UxManager).

    """

    def __init__(self,
                rect=None,
                image_rect=None,
                code='',
                hotkey=None,
                enabled=True,
                border_color=None,
                context=None,
                group=None
                ):
        super(UxTabButton, self).__init__(
            rect, image_rect, code, hotkey, enabled, border_color, context)
        self.group = group

    def click(self, position):
        """
        Overrides base to only click, but not unclick.
        Test if the given point is clicking us.
        """

        if not self.isclicked:
            is_clicked = self._istarget(position)
            if is_clicked:
                self.isclicked = True
                return True

    def calculated_rect(self):
        """
        Overrides base to ignore disabled state.
        Calculates our source rectangle from our state.
        """

        # normal - clicked
        x_offset = 0
        if self.isclicked:
            x_offset = 1
        return pygame.Rect(self.image_rect.left +
            (x_offset * self.image_rect.width),
            self.image_rect.top,
            self.image_rect.width,
            self.image_rect.height
            )


class UxManager(object):
    """
    Stores a collection of elements and handles drawing them.

    The context attribute allows us to limit actions on subsets
    of elements, i.e. 'main', 'menu', or 'options' screens.
    This attribute is optional, None is the default.

    use add() to populate with elements.
    Not unlike herding cats.
    """

    def __init__(self,
                size=None,
                image_filename=None,
                font=None,
                click_callback=None,
                colorkey=(255, 0, 255)
                ):
        #self.rect = rect
        self.font = font
        self.click_callback = click_callback
        self.colorkey = colorkey

        # initialize other attributes
        self.context = None
        self.elements = []
        self.context_elements = []
        self.image = pygame.Surface(size)
        self.image.set_colorkey(colorkey)
        self.source = pygame.image.load(image_filename)

    def _draw_element_hotkey(self, element):
        """
        Draws the element's hotkey onto an image stored on the element.
        So we do not have to hardcode keys into images.

        """

        if element.hotkey and not element.hotkey_image:
            element.hotkey_image = self.font.render(
                element.hotkey.upper(),
                False,
                color.green,
                color.magenta
                )
            element.hotkey_image.set_colorkey(color.magenta)

    def _refresh_context_elements(self):
        """
        Rebuild the list of context elements.
        """

        self.context_elements = []
        for ux in self.elements:
            if self.context in ux.context:
                self.context_elements.append(ux)
                ux.visible = True
                if type(ux) is UxMovingButton:
                    ux.recall_destination('show')
            else:
                if type(ux) is UxMovingButton:
                    ux.recall_destination('hide')
                else:
                    ux.visible = False

    def set_context(self, context):
        """
        Set the new context of this UxManager.
        Only elements under this context will be drawn and respond to events.
        """

        self.context = context
        self._refresh_context_elements()
        #self.update()

    def get_by_code(self, code):
        """
        Get an element by code.

        """

        matches = [e for e in self.elements if e.code == code]
        if matches:
            return matches[0]

    def add(self, element, hide_hotkey=False):
        """
        Add an element to this UxManager. munch.
        """

        self.elements.append(element)
        self._refresh_context_elements()
        if not hide_hotkey and not isinstance(element, UxTabButton):
            self._draw_element_hotkey(element)

    def remove(self, element):
        """
        Remove this ux from the UxManager. thanks.
        """

        self.elements.remove(element)
        self._refresh_context_elements()

    def remove_by_code(self, code_list):
        """
        Remove a list of elements by code.

        """

        for code in code_list:
            element = self.get_by_code(code)
            if element:
                self.remove(element)

    def hover(self, position):
        """
        Test if the position is over any ux elements.
        """

        for ux in self.context_elements:
            if ux.hover(position):
                ux.draw(self.source, self.image)
                return

    def click(self, position):
        """
        I hear it tickles when you're clicked the first time.
        """

        for ux in self.context_elements:
            if ux.enabled and ux.click(position):
                if isinstance(ux, UxTabButton):
                    self.unselect_other_tabs(ux)
                ux.draw(self.source, self.image)
                if self.click_callback is not None:
                    self.click_callback(self.context, ux)

    def unclick(self):
        """
        Mark all ux elements as unclicked. Used on MOUSEUP events.
        """

        for ux in self.context_elements:
            if not isinstance(ux, UxTabButton):
                if ux.isclicked:
                    ux.isclicked = False
                    ux.draw(self.source, self.image)

    def unselect_other_tabs(self, exclude_tab):
        """
        Unselect all tab in our context that live in the same group
        as exclude_tab.

        """

        for tab in self.context_elements:
            if tab is not exclude_tab and isinstance(tab, UxTabButton):
                if tab.group == exclude_tab.group and tab.isclicked:
                    tab.isclicked = False
                    tab.draw(self.source, self.image)

    def update(self):
        """
        Tell all our elements to go draw themselves.
        """

        self.image.fill(self.colorkey)
        for ux in self.elements:
            if type(ux) is UxMovingButton:
                ux.update(self.context)
            if ux.visible:
                ux.draw(self.source, self.image)

    def alter_hue(self, hue, surface_to_clone):
        """ This cleverness rotates the pixel rgb values through
        360 degress of hues.
        thanks goes to:
        http://forum.chaos-project.com/index.php?topic=8400.0;wap2"""
        colorized_surface = surface_to_clone.copy()
        colorized_surface.lock()
        for x in range(colorized_surface.get_width()):
            for y in range(colorized_surface.get_height()):
                color = pygame.Color(*colorized_surface.get_at((x, y)))
                hsva = list(color.hsva)
                # hue of -1 will desaturate the pixel instead
                if hue == -1:
                    hsva[1] = 0
                else:
                    hsva[0] = (hsva[0] + hue) % 360.0
                color.hsva = hsva
                colorized_surface.set_at((x, y),
                                        (color.r, color.g, color.b, color.a))
        colorized_surface.unlock()
        return colorized_surface


def test_callback(context, control):
    print(control.code)

if __name__ == "__main__":
    print('pygame ui unit test running')
    import sys
    import time
    pygame.init()
    pygame.font.init()
    #font = pygame.font.Font(pygame.font.get_default_font(), 8)
    pygame.display.set_caption('ui elements tech demo')
    screen = pygame.display.set_mode((640, 480))
    clock = pygame.time.Clock()

    # build some controls
    UI = UxManager(
        size=(640, 480),
        image_filename='images/ui.png',
        font=None,
        click_callback=test_callback,
        colorkey=(255, 0, 255)
        )

    # add a button
    button = UxButton(
        rect=(10, 10, 57, 45),
        image_rect=(0, 0, 57, 45),
        code='zap',
        hotkey='z',
        enabled=True,
        border_color=None,
        context=None
        )
    UI.add(button)

    # add a button
    button = UxButton(
        rect=(10, 55, 57, 45),
        image_rect=(0, 0, 57, 45),
        code='zap',
        hotkey='z',
        enabled=False,
        border_color=None,
        context=None
        )
    UI.add(button)

    # display a window
    running = True
    while running:

        # hover test
        UI.hover(pygame.mouse.get_pos())

        # draw the UI
        clock.tick(30)
        screen.fill((46, 46, 63))
        UI.update()
        screen.blit(UI.image, (0, 0))
        pygame.display.flip()

        # check for input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SLASH:
                    if UI.context is None:
                        UI.set_context('main')
                    else:
                        UI.set_context(None)
                    print('our context is now %s' % (UI.context))

                # send this hotkey to the UI manager
                UI.click(event.unicode)

            elif event.type == pygame.KEYUP:
                # send this hotkey to the UI manager
                UI.unclick()
                pass

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    UI.click(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                UI.unclick()
