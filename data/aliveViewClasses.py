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

    def addimage(self, image, fps, loop):
        """
        Allows adding of a animated sprite image.
        The fps applies to all frames. It overwrites the previous fps value.
        """

        self._images.append(image)
        self._hasframes = len(self._images) > 1
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
        Called by the sprite group draw().
        """

        if not self._hasframes:
            return
        if self.canupdate(t):
            self._last_update = t
            self._frame += 1
            if self._frame >= len(self._images):
                self._frame = 0
                if self.loop > 0:
                    self.loop -= 1
                if self.loop == 0:
                    self._hasframes = False
                    self._frame = -1
            self.image = self._images[self._frame]


class MovingSprite(Sprite):
    """
    A sprite with a vector that slides it to a destination.
    """

    def __init__(self, name, rect, destination, speed, *groups):
        super(MovingSprite, self).__init__(name, rect, *groups)
        self.destination = destination
        self.speed = speed
        self.done = False

    def update(self, t):
        # update location
        super(MovingSprite, self).update(t)
        if self.canupdate(t):
            self._last_update = t
            if self.rect.left < self.destination[0]:
                self.rect.left += self.speed
            if self.rect.left > self.destination[0]:
                self.rect.left -= self.speed
            if self.rect.top < self.destination[1]:
                self.rect.top += self.speed
            if self.rect.top > self.destination[1]:
                self.rect.top -= self.speed
            self.done = self.rect.topleft == self.destination


class TransitionBase(object):
    """
    Base for animated screen transitions.
    """

    def __init__(self, size=None, background_color=color.green, fps=30):
        """
        Defines a base for animations transition effects.
        Simply: a canvas that draws itself each update() -- permitting fps.

        size (width, height) tells us how large our canvas should be.

        background_color (r, g, b) fills our canvas with the given color on
                creation.

        fps (int) is used to calculate constant redraw speed for any fps.

        Attributes:
            done (bool):
                True when our animation is complete.
            waitforkey (bool): A flag to let our callers know to wait for
                user keypress.
        """

        if not size:
            raise ValueError('TransitionBase size cannot be None')
        self.image = pygame.Surface(size)
        self.image.set_colorkey(color.magenta)
        self.image.fill(background_color)
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
        super(StaticScreen, self).__init__(size, background_color, fps)
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
                background_color=color.magenta,
                fps=30,
                font=None,
                title='',
                background=None,
                boxcolor=color.green,
                pensize=1,
                direction_reversed=False
                ):
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
            centered text drawn on the transition

        background:
            an image that underlays the transition

        boxcolor:
            color of the bounding box

        pensize:
            size of the box border

        direction_reversed:
            True to reverse the animation

        """

        super(SlideinTransition, self).__init__(size, background_color, fps)

        # prerender the words and center them
        self.fontpix = font.render(title, False, color.green)
        self.fontloc = pygame.Rect((0, 0), self.fontpix.get_size())
        self.fontloc.center = self.rect.center
        self.size = self.rect.size
        self.boxcolor = boxcolor
        self.pensize = pensize
        self.background_color = background_color
        self.direction_reversed = direction_reversed

        # center the background image
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

        self.background = None
        if background:
            #TODO may not be neccessary if we just store background_image :p
            # make a background surface
            bgpos = ((self.size[0] - background.get_width()) / 2,
                   (self.size[1] - background.get_height()) / 2)
            self.background = pygame.Surface(self.size)
            self.background.fill(background_color)
            # paint over the given image
            self.background.blit(background, bgpos)
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
            if self.background:
                # FIXME may need to fill with background_color (magenta) here
                # draw the background image cut from the same area of our box
                self.image.fill(self.background_color)
                self.image.blit(self.background, self.box.topleft, self.box)
            pygame.draw.rect(self.image, self.boxcolor, self.box, self.pensize)
            self.image.blit(self.fontpix, self.fontloc)
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
        super(TerminalPrinter, self).__init__(size, background_color, fps)
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
