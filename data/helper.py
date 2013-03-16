import pygame

def wrapLines(message, maxlength):
    """ Takes a long string and returns a list of lines. 
    maxlength is the characters per line. """
    lines = []
    while len(message) > maxlength:
        cutoff = message.find(' ', maxlength)
        lines.insert(0,message[:cutoff])
        message = message[cutoff:]
    # add any remainder
    lines.insert(0,message)
    # unreverse the order
    lines.reverse()
    return lines

def renderLines(lines, font, antialias, color, colorize=None, background=None):
    """ # Simple functions to easily render pre-wrapped text onto a single
    # surface with a uniform background.
    # Author: George Paci

    # Results with various background color alphas:
    #  no background given: ultimate blit will just change figure part of text,
    #      not ground i.e. it will be interpreted as a transparent background
    #  background alpha = 0: "
    #  background alpha = 128, entire bounding rectangle will be equally blended
    #      with background color, both within and outside text
    #  background alpha = 255: entire bounding rectangle will be background color
    #
    # (At this point, we're not trying to respect foreground color alpha;
    # we could by compositing the lines first onto a transparent surface, then
    # blitting to the returned surface.)
    
    colorize sets by how much each rgb value is upped for each line.
    (0, 10, 0) will up green by 10 for each line printed.
     """
    
    fontHeight = font.get_height()
    surfaces = []
    c = color
    if colorize:
        for ln in lines:
            c = ( c[0] + colorize[0], c[1] + colorize[1], c[2] + colorize[2])
            surfaces.append(font.render(ln, antialias, c))
    else:
        surfaces = [font.render(ln, antialias, color) for ln in lines]
    maxwidth = max([s.get_width() for s in surfaces])
    result = pygame.Surface((maxwidth, len(lines)*fontHeight), pygame.SRCALPHA)
    if background == None:
        result.fill((90,90,90,0))
    else:
        result.fill(background)

    for i in range(len(lines)):
      result.blit(surfaces[i], (0,i*fontHeight))
    return result

def renderTextBlock(text, font, antialias, color, colorize=None, background=None):
    """ renders block text with newlines. """
    brokenText = text.replace("\r\n","\n").replace("\r","\n")
    return renderLines(
                        brokenText.split("\n"), 
                        font, 
                        antialias, 
                        color, 
                        colorize, 
                        background
                        )

if __name__ == "__main__":
    #print(wrapLines('The server at lipsum.com cant be found because the DNS look-up failed.', 
    #10))
    message = 'The server at lipsum.com cant be found because the DNS look-up failed.'
    maxlength = 15

    lines = []
    # reverse
    message = message[::-1]
    while len(message) > maxlength:
        cutoff = message.find(' ', maxlength)
        lines.append(message[:cutoff][::-1])
        message = message[cutoff:]
    # add any remainder
    lines.append(message[::-1])
    # unreverse the order
    lines.reverse()
    print lines

    print('\n')

    maxlength = 10
    lines = []
    message = "The server at lipsum.com cant be found because the DNS look-up failed. DNS is the network service that translates a websites name to its Internet address."
    while len(message) > maxlength:
        cutoff = message.find(' ', maxlength)
        lines.insert(0,message[:cutoff])
        message = message[cutoff:]
    # add any remainder
    lines.insert(0,message)
    # unreverse the order
    lines.reverse()
    print lines
