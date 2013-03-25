import pygame
import trace
from eventmanager import *

class GraphicalView:
   """
   Draws the model state onto the screen.
   """
   
   def __init__(self, evManager):
      self.evManager = evManager
      evManager.RegisterListener(self)
      self.isinitialized = False
      self.screen = None
      self.clock = None

   def notify(self, event):
      """
      Called by an event in the message queue.
      """
      
      if isinstance(event, InitializeEvent):
         self.initialize()
      if isinstance(event, TickEvent):
         self.clock.tick(30)
      
   def initialize(self):
      """
      Set up the pygame graphical display.
      """
      
      result = pygame.init()
      pygame.font.init()
      pygame.display.set_caption('Alive')
      self.screen = pygame.display.set_mode((800, 512))
      self.clock = pygame.time.Clock()
      self.isinitialized = True

