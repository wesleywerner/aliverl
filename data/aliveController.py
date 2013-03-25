import pygame
from eventmanager import *

class KeyboardMouse:
   """
   Handles keyboard input.
   """
   
   def __init__(self, evManager):
      self.evManager = evManager
      evManager.RegisterListener(self)
   
   def notify(self, event):
      """
      Called by an event in the message queue.
      """
      
      if isinstance(event, TickEvent):
         # Called for each game tick. We check our keyboard presses here.
         for event in pygame.event.get():
            
            # always handle window closing events
            if event.type == pygame.QUIT:
               self.evManager.Post(QuitEvent)
            
            if event.type == pygame.KEYDOWN:
               inEvent = InputEvent(unicodechar=event.unicode, clickpos=None)
               self.evManager.Post(inEvent)

            if event.type == pygame.K_ESCAPE:
               trace.write('escape key pushed')
               self.evManager.Post(QuitEvent)
