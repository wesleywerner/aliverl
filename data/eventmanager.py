import trace

class Event(object):
    """
    A superclass for any events that might be generated by an
    object and sent to the EventManager.
    """
    
    def __init__(self):
        self.name = "Generic event"
    def __str__(self):
        return self.name
    
    
class QuitEvent(Event):
    """
    Quit event.
    """
    
    def __init__ (self):
        self.name = "Quit event"
    
    
class TickEvent(Event):
    """
    Tick event.
    """
    
    def __init__ (self):
        self.name = "Tick event"
    
    
class InputEvent(Event):
    """
    Keyboard or mouse input event.
    """
    
    def __init__(self, unicodechar, clickpos):
        self.name = "Input event"
        self.char = unicodechar
        self.clickpos = clickpos
    def __str__(self):
        return '%s, char=%s, clickpos=%s' % (self.name, self.char, self.clickpos)
    

class PlayerMoveRequestEvent(Event):
    """
    Request to move the player object.
    Direction (x, y): tile offset to move.
    """
    
    def __init__(self, direction):
        self.name = 'Player move request event'
        self.direction = direction

    def __str__(self):
        return '%s offset %s' % (self.name, self.direction)
    
class PlayerMovedEvent(Event):
    """
    Request to move the player object.
    Direction (x, y): tile offset to move.
    """
    
    def __init__(self, objectid, direction):
        self.name = 'Player moved event'
        self.direction = direction
        self.objectid = objectid

    
class InitializeEvent(Event):
    """
    Tells all listeners to initialize themselves.
    This includes loading libraries and resources.
    
    Avoid initializing such things within listener __init__ calls 
    to minimize snafus (if some rely on others being yet created.)
    """
    
    def __init__ (self):
        self.name = "Initialize event"


class NextLevelEvent(Event):
    """
    At the start of each game level.
    Tell Views to prepare resources.
    """
    
    def __init__ (self, filename):
        self.name = "Next level event"
        self.filename = filename


class StateChangeEvent(Event):
    """
    Change the model state machine.
    Given a None state will pop() instead of push.
    """
    
    def __init__(self, state):
        self.name = "State change event"
        self.state = state
    def __str__(self):
        if self.state:
            return '%s pushed %s' % (self.name, self.state)
        else:
            return '%s popped' % (self.name, )


class ShiftViewportEvent(Event):
    """
    Move the Viewport around.
    It is that area which the game takes place.
    """
    
    def __init__ (self, xy):
        self.name = 'Shift viewport event'
        self.xy = xy


class CombatEvent(Event):
    """
    Initiates a combat turn.
    """
    
    def __init__(self, attacker, defender):
        """
        attacker and defender are MapObjects.
        The former indicates it's their move.
        """
        
        self.name = 'Combat event'
        self.attacker = attacker
        self.defender = defender
    
    def __str__(self):
        return '%s <%s -> %s>' % (self.name, self.attacker.name, self.defender.name)
    

class MessageEvent(Event):
    """
    Sends a game message for the user to read.
    """
    
    def __init__(self, messages):
        """
        message can be a single string, or a list of them.
        """
        
        self.name = 'Message event'
        if type(message) is str:
            self.messages = list(message)
        elif type(message) is list:
            self.messages = messages
        
    def __str__(self):
        return '\n * %s'.join(self.messages)


class EventManager(object):
    """
    We coordinate communication between the Model, View, and Controller.
    """
    
    def __init__(self):
        from weakref import WeakKeyDictionary
        self.listeners = WeakKeyDictionary()

    def RegisterListener(self, listener):
        """ 
        Adds a listener to our spam list. 
        It will receive Post()ed events through it's notify(event) call. 
        """
        
        self.listeners[listener] = 1

    def UnregisterListener(self, listener):
        """ 
        Remove a listener from our spam list.
        This is implemented but hardly used.
        Our weak ref spam list will auto remove any listeners who stop existing.
        """
        
        if listener in self.listeners.keys():
            del self.listeners[listener]
        
    def Post(self, event):
        """
        Post a new event to the message queue.
        It will be broadcast to all listeners.
        """
        
        not isinstance(event, TickEvent) and trace.write(str(event))
        for listener in self.listeners.keys():
            listener.notify(event)
