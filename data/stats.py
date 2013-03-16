# for rendering player stats
import pygame
from pygame.locals import *
import color

def draw_stats(player, level, full_info=False):
    """ draw and return the player stats box. """
    def __get_color_band(ratio):
        # gradient more green for healthy, red for hurt
        if ratio > 0.8:
            return color.green
        elif ratio > 0.5:
            return color.yellow
        else:
            return color.red

    font = pygame.font.Font('bitwise.ttf', 14)
    canvas = pygame.Surface((275, 160), pygame.SRCALPHA)
    colors = []
    lines = []

    # basic stats
    lines.append( str(player.health) + ' health' )
    colors.append(__get_color_band(player.health / float(player.maxhealth)))
    lines.append( str(player.mana) + ' mana' )
    colors.append(__get_color_band(player.mana / float(player.maxmana)))
    canvas.blit( renderLines(lines, font, True, colors ,), (170, 16))
    if not full_info:
        return canvas

    # full stats
    lines = []
    colors = []
    lines.append( str(player.attack) + ' attack' )
    colors.append( color.text )
    lines.append( str(player.stealth) + ' stealth' )
    colors.append( color.text )
    canvas.blit( renderLines(lines, font, True, colors ,), (10, 10))
    return canvas

def renderLines(lines, font, antialias, color, background=None):
    """ Draws a list of lines to a surface. """
    
    fontHeight = font.get_height()
    if type(color) is list:
        surfaces = [font.render(k, antialias, v) for k,v in zip(lines, color)]
    else:
        surfaces = [font.render(ln, antialias, color) for ln in lines]
    # can't pass background to font.render, because it doesn't respect the alpha

    maxwidth = max([s.get_width() for s in surfaces])
    result = pygame.Surface((maxwidth, len(lines)*fontHeight), pygame.SRCALPHA)
    if background == None:
        result.fill((90,90,90,0))
    else:
        result.fill(background)

    for i in range(len(lines)):
      result.blit(surfaces[i], (0,i*fontHeight))
    return result

def renderTextBlock(text, font, antialias, color, background=None):
    """ Draws text lines with newlines to a surface. """
    brokenText = text.replace("\r\n","\n").replace("\r","\n")
    return renderLines(brokenText.split("\n"), font, antialias, color, background)
