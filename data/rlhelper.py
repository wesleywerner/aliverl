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

import math

def make_matrix(width, height, initial_value):
    """
    Returns a list of initial values that can be accessed like a 2D array:

        matrix[x][y]

    """

    return [[initial_value for y in range(0, height)] for x in range(0, width)]


def get_line_segments(x1, y1, x2, y2):
    """
    Returns a list of line segments that make up a line between two points.
    Returns [(x1, y1), (x2, y2), ...]

    Source: http://roguebasin.roguelikedevelopment.org/index.php?title=Bresenham%27s_Line_Algorithm

    """

    points = []
    issteep = abs(y2 - y1) > abs(x2 - x1)
    if issteep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    rev = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        rev = True
    deltax = x2 - x1
    deltay = abs(y2 - y1)
    error = int(deltax / 2)
    y = y1
    ystep = None
    if y1 < y2:
        ystep = 1
    else:
        ystep = -1
    for x in range(x1, x2 + 1):
        if issteep:
            points.append((y, x))
        else:
            points.append((x, y))
        error -= deltay
        if error < 0:
            y += ystep
            error += deltax
    # Reverse the list if the coordinates were reversed
    if rev:
        points.reverse()
    return points


def line_of_sight(matrix, x1, y1, x2, y2):
    """
    Returns True if there is line of sight between two points.
    Uses the matrix data to rely on blocking tiles.
    This is a matrix created with make_matrix().

    """

    segs = get_line_segments(x1, y1, x2, y2)
    hits = [matrix[x][y] for x, y in segs]
    amt = hits.count(True)
    # allow 1 case: if the final destination position is blocking
    return amt == 0 or (amt == 1 and matrix[x2][y2])

def remap_coords(rect, unit_width, unit_height):
    """
    An iterator that yields remapped values as (x, y) scaled to
    a specific unit size.

    rect is a (x, y, w, h) of coordinates. The (w, h) components will
    be used to calculate the (x2, y2) used for the max range.
    unit_size is the boundary which each unit is calculated against.

    """

    for y in range(rect[1], rect[1] + rect[3], unit_height):
        for x in range(rect[0], rect[0] + rect[2], unit_width):
            yield (
                int(float(x) / float(unit_width)),
                int(float(y) / float(unit_height))
                )

def distance(x, y, u, v):
    """
    Returns the distance between two cartesian points.
    """

    return math.sqrt((x - u) ** 2 + (y - v) ** 2)

def cover_area(origin_x, origin_y, reach, max_width, max_height):
    """
    Yields a range of (x, y) coordinates from an origin within reach
    constrained to max boundaries.

    """

    for y in range(origin_y - reach, origin_y + reach):
        for x in range(origin_x - reach, origin_x + reach):
            if x > 0 and y > 0 and x < max_width and y < max_height:
                if distance(origin_x, origin_y, x, y) <= reach:
                    yield (x, y)