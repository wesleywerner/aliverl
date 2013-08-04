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

import pygame
import color


class Sprite(pygame.sprite.Sprite):
    """
    Represents an animated sprite.
    """

    def __init__(self, name, rect, *groups):
        """
        rect(Rect) of the sprite on screen.
        *groups(sprite.Group) add sprite to these groups.
        """

        super(Sprite, self).__init__(*groups)
        self.name = name
        self.rect = rect
        self.image = None
        self._images = []
        self._start = pygame.time.get_ticks()
        self._delay = 0
        self._last_update = 0
        self._frame = 0
        self._hasframes = False
        self.fps = 1
        self.loop = -1
        self.shift_speed = 0
        self.destination = None

    @property
    def is_moving(self):
        """
        Test if this sprite is busy moving to a destination position.
        """

        if self.shift_speed and self.destination:
            return self.rect.topleft != self.destination

    def addimage(self, image, fps, loop):
        """
        Allows adding of a animated sprite image.
        The fps applies to all frames. It overwrites the previous fps value.
        """

        self._images.append(image)
        self._hasframes = len(self._images) > 0
        if len(self._images) > 0:
            self.image = self._images[0]
        if fps <= 0:
            fps = 1
        self._delay = 1000 / fps
        self.loop = loop
        self._frame = 0

    def clear(self):
        """
        Clear sprite images
        """

        while len(self._images) > 0:
            del self._images[-1]
        self._hasframes = False

    def canupdate(self, t):
        """
        Tests if it is time to update again
        time is the current game ticks. It is used to calculate when to update
            so that animations appear constant across varying fps.
        """

        if t - self._last_update > self._delay:
            return True

    def update(self, t):
        """
        Update the sprite animation if enough time has passed.
        Also update the position if it has a shift_speed and destination set.
        Called by the sprite group draw().
        """

        if self.shift_speed and self.destination:
            if self.rect.left < self.destination[0]:
                self.rect.left += self.shift_speed
            if self.rect.left > self.destination[0]:
                self.rect.left -= self.shift_speed
            if self.rect.top < self.destination[1]:
                self.rect.top += self.shift_speed
            if self.rect.top > self.destination[1]:
                self.rect.top -= self.shift_speed

        if self.canupdate(t):
            self._last_update = t
            if self._hasframes:
                self._frame += 1
                if self._frame >= len(self._images):
                    self._frame = 0
                    if self.loop > 0:
                        self.loop -= 1
                    if self.loop == 0:
                        self._hasframes = False
                        self._frame = -1
                self.image = self._images[self._frame]

    def set_position(self, x, y, shift_speed=0):
        """
        Set the sprite position.
        shift_speed determines the amount of pixels to shift the sprite to
        it's new location. 0 is an instant jump.
        """

        if shift_speed == 0:
            self.shift_speed = 0
            self.rect.topleft = (x, y)
        else:
            self.shift_speed = shift_speed
            self.destination = (x, y)


class TransitionBase(object):
    """
    Base for animated screen transitions.
    """

    def __init__(self, size=None, fps=30):
        """
        Defines a base for animations transition effects.
        Simply: a canvas that draws itself each update() -- permitting fps.

        size (width, height):
            How large our image should be.

        fps (int):
            Used to calculate constant redraw speed.

        Attributes:

            done (bool):
                True when our animation is complete.

            waitforkey (bool):
                Let our callers know to wait for a user keypress.

        """

        if not size:
            raise ValueError('TransitionBase size cannot be None')
        self.image = pygame.Surface(size)
        self.image.set_colorkey(color.magenta)
        self.rect = pygame.Rect((0, 0), size)
        self.delay = 500 / fps
        self.lasttime = 0
        self.done = False
        self.waitforkey = False

    def can_update(self, time):
        """
        Tests if it is time to update again. time is the current game ticks.
        """

        if time - self.lasttime > self.delay:
            self.lasttime = time
            return True

    def update(self, time):
        """
        Step the transition.
        use can_update(time) to test if it is time to redraw.
        This call is left empty for you to override.
        """

        if self.can_update(time):
            pass


class StaticScreen(TransitionBase):
    """
    Display a static screen with a background and some words.
    This is not an animated transition.
    """

    def __init__(self,
                size=None,
                background_color=color.magenta,
                fps=30,
                font=None,
                words=None,
                word_color=color.green,
                words_x_offset=0,
                words_y_offset=0,
                background=None
                ):
        super(StaticScreen, self).__init__(size, fps)
        self.waitforkey = True
        # use the supplied background image
        if background:
            # center it within our canvas
            bgpos = ((self.rect.width - background.get_width()) / 2,
                   (self.rect.height - background.get_height()) / 2)
            self.xpadding = words_x_offset + bgpos[0]
            self.ypadding = words_y_offset + bgpos[1]
            self.image.blit(background, bgpos)
        # draw the words on top
        if words:
            font_bmp = self.draw_text_block(
                words.split("\n"), font, False, word_color)
            self.image.blit(font_bmp, (words_x_offset, words_y_offset))


class SlideinTransition(TransitionBase):
    """
    A rectangle that stays centered on the canvas, grows in width
    until it touches the screen edges.
    Then the rectangle grows in height, while staying centered, until
    touching the top-bottom.
    """

    def __init__(self,
                size=None,
                fps=30,
                font=None,
                title='',
                inner_bg_color=color.black,
                inner_bg=None,
                outer_bg_color=color.magenta,
                outer_bg=None,
                boxcolor=color.green,
                pensize=1,
                direction_reversed=False
                ):
        """
        size:
            (width, height) tells us how large our canvas should be.

        fps:
            (int) used to calculate constant redraw speed for any fps.

        font:
            is use for drawing any title text.

        title:
            centered text drawn on the transition

        inner_bg_color:
            (r, g, b) fills the region within our box area.

        inner_bg:
            The image displayed inside the shifting box region

        outer_bg_color:
            (r, g, b) fills the region outside our box area.

        outer_bg:
            The image displayed outside the shifting box region

        boxcolor:
            color of the bounding box

        pensize:
            size of the box border

        direction_reversed:
            True to reverse the animation

        """

        super(SlideinTransition, self).__init__(size, fps)

        self.size = self.rect.size
        self.boxcolor = boxcolor
        self.pensize = pensize
        self.inner_bg_color = inner_bg_color
        self.inner_bg = inner_bg
        self.outer_bg_color = outer_bg_color
        self.outer_bg = outer_bg
        self.direction_reversed = direction_reversed

        # prerender the words and center them
        self.fontpix = font.render(title, False, color.green)
        self.fontloc = pygame.Rect((0, 0), self.fontpix.get_size())
        self.fontloc.center = self.rect.center

        if direction_reversed:
            # box fills the area and shrinks over time
            self.box = self.rect.copy()
        else:
            # box starts small and expands over time
            self.box = pygame.Rect(0, 0, 100, 20)

        # center the box according to full size
        self.box.center = self.rect.center
        if not font:
            font = pygame.font.Font(None, 16)

        # toggle delta direction
        self.xdelta = 30
        self.ydelta = 30
        self.resizingwidth = True
        self.resizingheight = False
        # switch reversed mode
        if self.direction_reversed:
            self.xdelta *= -1
            self.ydelta *= -1
            self.resizingwidth = False
            self.resizingheight = True

    def update(self, time):
        """
        Step the transition.
        """

        if self.can_update(time):
            if self.resizingheight:
                self.box = self.box.inflate(0, self.ydelta)
                self.box = self.rect.clip(self.box)
                if self.direction_reversed:
                    # because our delta resize is arbitrary
                    # limit to within positive values
                    if self.box.h < 0:
                        self.box.h = 0
                    # we are busy while the height is positive
                    self.resizingheight = self.box.h > 0
                else:
                    # we are busy while the height is < max
                    self.resizingheight = self.box.h < self.size[1]
            elif self.resizingwidth:
                self.box = self.box.inflate(self.xdelta, 0)
                self.resizingwidth = self.box.w < self.size[0]
                if not self.direction_reversed:
                    self.resizingheight = not self.resizingwidth

            # fill the outer area and draw a background
            self.image.fill(self.outer_bg_color)
            if self.outer_bg:
                #NOTE: transition outer background could be centered
                self.image.blit(self.outer_bg, (0, 0))

            # fill the inner area and draw a background
            self.image.fill(self.inner_bg_color, self.box)
            if self.inner_bg:
                self.image.blit(self.inner_bg, self.box.topleft, self.box)

            # draw our box rectangle
            pygame.draw.rect(self.image, self.boxcolor, self.box, self.pensize)

            # write the title text
            self.image.blit(self.fontpix, self.fontloc)

            # check if we are done with our animation
            self.done = not self.resizingwidth and not self.resizingheight

        return not self.done


class TerminalPrinter(TransitionBase):
    """
    Simulates typing text onto a screen.
    """

    def __init__(self,
                size=None,
                background_color=color.magenta,
                fps=30,
                font=None,
                words=None,
                word_color=color.green,
                words_x_offset=0,
                words_y_offset=0,
                background=None):
        """
        size:
            (width, height) tells us how large our canvas should be.

        background_color:
            (r, g, b) fills our canvas with the given color on creation.

        fps:
            (int) used to calculate constant redraw speed for any fps.

        font:
            is use for drawing any title text.

        title:
            is the words to display during.

        words_x_offset, words_y_offset:
            how much to offset the word position.
            If background given this is relative to
            the rect - background sizes.

        """

        if not words:
            raise ValueError('TerminalPrinter words cannot be None or empty')
        super(TerminalPrinter, self).__init__(size, fps)
        self.words = words
        self.text = ""
        self.word_color = word_color
        self.font = font
        self.xpadding = words_x_offset
        self.ypadding = words_y_offset
        self.lineindex = 0
        self.charindex = 0
        self.xposition, self.yposition = self.rect.topleft
        self.done = False
        self.lastfontheight = 0
        self.waitforkey = True
        self.size = (self.rect.width, self.rect.height)
        if not self.font:
            self.font = pygame.font.Font(None, 40)
        # center the background image
        self.background = None
        if background:
            # make a background surface
            bgpos = ((self.size[0] - background.get_width()) / 2,
                   (self.size[1] - background.get_height()) / 2)
            self.xpadding = words_x_offset + bgpos[0]
            self.ypadding = words_y_offset + bgpos[1]
            # create a new background the same size as our canvas
            self.background = pygame.Surface(self.size)
            # fill it with black
            self.background.fill(color.black)
            # paint over the given image
            self.background.blit(background, bgpos)

    def update(self, time):
        """
        Step the transition.
        """

        if self.can_update(time) and not self.done:
            if self.background:
                # draw the background image cut from the same area of our box
                self.image.blit(self.background, self.rect.topleft)
            if self.charindex == len(self.words[self.lineindex]):
                self.lineindex += 1
                self.xposition = self.rect.left
                self.charindex = 0
                self.yposition += self.lastfontheight
                self.done = self.lineindex == len(self.words)
            if not self.done:
                c = self.words[self.lineindex][self.charindex]
                glyph = self.font.render(c, True, self.word_color)
                self.background.blit(glyph,
                                    (self.xposition + self.xpadding,
                                    self.yposition + self.ypadding))
                glyphx, self.lastfontheight = glyph.get_size()
                self.xposition += glyphx
            self.charindex += 1
        return self.done


class GraphDisplay(object):
    """
    Draws a graph-like object from a given list of values.

    """

    def __init__(self,
                fps=30,
                base_color=color.green,
                title='spam',
                font=None,
                rect=(0, 0, 80, 40),
                background_image=None
                ):
        """
        beware: spam lives here.
        """

        # convert rect to pygame object
        if type(rect) is tuple:
            self.rect = pygame.Rect(rect)
        else:
            self.rect = rect
        # store the title as a image to overlay later
        if not font:
            font = pygame.font.Font(None, 16)
        self.title_bmp = font.render(title, False, color.white, color.magenta)
        self.title_bmp.set_colorkey(color.magenta)
        self.base_color = base_color
        self.image = pygame.Surface(self.rect.size)
        self.delay = 1000 / fps
        self.lasttime = 0
        # the actual graph values
        self.poly_points = None
        # the displayed graph values.
        # gets shifted towards poly_ponts on each update() call
        # to give a slide-like motion effect.
        self.display_points = None

    def set_values(self, value_list, maximum):
        """
        Set the list of values to plot, with the maximum value to scale.

        """

        # how do we calculate where to draw the graph points?
        # 1. calculate the x and y dist between points in relation to our size
        # 2. build a list of polygon points relative to the maximum
        #    and scaled to our size
        #
        # x_dist = width / len(values)
        # y_dist = height / max
        #
        # where n is the index of each value v
        # p1x = n * x_dist
        # p1y = abs(((v1 / max) * height) - height)
        # note: abs(-height) inverts the graph so that the origin is top-left.

        if len(value_list) < 2:
            return
        width = self.rect.width
        height = self.rect.height
        x_dist = float(width) / (len(value_list) - 1)
        y_dist = float(height) / maximum
        # to align the start and end points for nice closure
        self.poly_points = [(0, height)]
        for n, v in enumerate(value_list):
            px = n * x_dist
            py = abs(((float(v) / maximum) * height) - height)
            self.poly_points.append((int(px), int(py)))
        # to align the start and end points for nice closure
        self.poly_points.append((width, height))
        # initially the display matches the real values
        if not self.display_points:
            self.display_points = list(self.poly_points)

    def can_update(self, time):
        """
        Tests if it is time to update again. time is the current game ticks.

        """

        if time - self.lasttime > self.delay:
            self.lasttime = time
            return True

    def update(self, time):
        """
        Draw the image if the fps allows us.

        """

        if self.can_update(time) and self.poly_points and len(self.poly_points) > 2:
            # shift display points towards real values
            if self.display_points[0][0] != self.poly_points[0][0]:
                for p in self.display_points:
                    p[0] -= 1
            # draw the graph
            # TODO fill graph with a darkened base_color
            self.image.fill(color.black)
            pygame.draw.polygon(
                self.image, self.base_color, self.poly_points)
            pygame.draw.rect(self.image, self.base_color,
                pygame.Rect((0, 0), self.rect.size), 1)

    def draw(self, surface):
        """
        Draw the graph on the given surface.

        """

        surface.blit(self.image, self.rect)
        surface.blit(self.title_bmp, self.rect)
