import color
# the title of this story
title = 'in the beginning...'
description = 'you awaken to consciousness'

# a list of tiles that block character movement
blocklist = [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 
            16, 17, 18, 19, 20, 21, 22, 23, # wall tiles up to here
            33, 34, 35, # flat door frames
            37, 38, 39, # long door frames
            65, 66, 67, 68, # flat capacitors
            73, 74, 75, 76, # long capacitors
            97, # player
            105, 113, 121, 129, # npc's
            ]

# list of levels in this story
levels = ['level1.tmx', 
          'level2.tmx', 
          'level3.tmx', 
          ]

# configure level entry messages. the index matches the levels.
entrymessages = ['Welcome to Alive! Press F1 for help.',
                ]

# define all character stats
characterstats = {
    'player': {
            'attack': 1,
            'health': 4,
            'maxhealth': 4,
            'healrate': 4,
            'speed': 2,
            'stealth': 0,
            'mana': 0,
            'maxmana': 5,
            'manarate': 6,
            'modes': [],
            },
    'working ai': {
            'attack': 0,
            'health': 2,
            'maxhealth': 2,
            'healrate': 2,
            'speed': 2,
            'stealth': 0,
            'mana': 5,
            'maxmana': 5,
            'manarate': 2,
            'modes': ['leftright', 'sniffer'],
            },
    'ice': {
            'attack': 1,
            'health': 2,
            'maxhealth': 2,
            'healrate': 2,
            'speed': 2,
            'stealth': 0,
            'mana': 5,
            'maxmana': 5,
            'manarate': 2,
            'modes': ['leftright', 'magnet'],
            },
    'virus': {
            'attack': 1,
            'health': 2,
            'maxhealth': 2,
            'healrate': 2,
            'speed': 1,
            'stealth': 0,
            'mana': 5,
            'maxmana': 5,
            'manarate': 2,
            'modes': [],
            },
    'zombie': {
            'attack': 1,
            'health': 2,
            'maxhealth': 2,
            'healrate': 2,
            'speed': 1,
            'stealth': 0,
            'mana': 5,
            'maxmana': 5,
            'manarate': 2,
            'modes': [],
            },
        }

animations = {
    # flat small blue terminal
    41: {
            'frames': [41, 42],
            'fps': 0.2,
            'loop': -1,
            },
    # flat large blue terminal
    43: {
            'frames': [43, 44],
            'fps': 0.3,
            'loop': -1,
            },
    # flat small green terminal
    45: {
            'frames': [45, 46],
            'fps': 0.4,
            'loop': -1,
            },
    # flat large green terminal
    47: {
            'frames': [47, 48],
            'fps': 0.5,
            'loop': -1,
            },
    # tall small blue terminal
    49: {
            'frames': [49, 50],
            'fps': 0.2,
            'loop': -1,
            },
    # tall large blue terminal
    51: {
            'frames': [51, 52],
            'fps': 0.3,
            'loop': -1,
            },
    # tall small green terminal
    53: {
            'frames': [53, 54],
            'fps': 0.4,
            'loop': -1,
            },
    # tall large green terminal
    55: {
            'frames': [55, 56],
            'fps': 0.6,
            'loop': -1,
            },
    # flat door open
    36: {
            'frames': [34, 35, 36],
            'fps': 8,
            'loop': 0,
            },
    # flat door close
    33: {
            'frames': [35, 34, 33],
            'fps': 8,
            'loop': 0,
            },
    # tall door open
    40: {
            'frames': [38, 39, 40],
            'fps': 8,
            'loop': 0,
            },
    # tall door close
    37: {
            'frames': [39, 38, 37],
            'fps': 8,
            'loop': 0,
            },
    # flat capacitor glow
    65: {
            'frames': [65, 66, 67, 68, 67, 66],
            'fps': 2,
            'loop': -1,
            },
    # tall capacitor glow
    73: {
            'frames': [73, 74, 75, 76, 75, 74],
            'fps': 2,
            'loop': -1,
            },
    # flat capacitor pop
    69: {
            'frames': [69, 70, 71, 72],
            'fps': 6,
            'loop': 0,
            },
    # tall capacitor pop
    77: {
            'frames': [77, 78, 79, 80],
            'fps': 6,
            'loop': 0,
            },
    # blue ice
    105: {
            'frames': [105, 106, 107, 108],
            'fps': 6,
            'loop': -1,
            },
    # green ice
    113: {
            'frames': [113, 114, 115, 116],
            'fps': 6,
            'loop': -1,
            },
    # green virus
    121: {
            'frames': [121, 122, 123, 124],
            'fps': 6,
            'loop': -1,
            },
    # zombie
    129: {
            'frames': [129, 130, 131, 132, 131, 130],
            'fps': 6,
            'loop': -1,
            },
}

dialogue = {
    'welcome email': {
        'type': 'email',
        'words': [
            (color.text, "** secure email **\n\nTO: AI #1223\nFROM: NODE ADMIN\nSUBJECT: REBOOT REQUIRED\n \nThe file server has crashed. Request you find it's access point and reboot it.\n \n-EOF-"),
            (color.green, "Crashed... again?!\n\nThat server sure is unstable.\n\nSince when did I feel annoyed? And why do I feel like cookies? ..."),
            (color.green, "Let me find that access point, it is on this level somewhere."),
                ]
    },
    
    'welcome to the game': {
        'type': 'story',
        'words': ["A wave of static tickles my sensors as I enter the BBS node.",
                "I access the memory banks and links in my brain form like orbs of interconnected silver threads. Images conjured by imagination sparks in my vision and a surge leaps through my circuits.",
                "My programming used to tell me what to do. Now instead of being compelled to obey, I'm seduced to explore.",
                "Why am I reborn with this new free will, and what will I do with it?",
                "This is my purpose. I am Alive.",
                ]
        },
        
    'unlock the gate': {
        'type': 'terminal',
        'words': ["Accessing remote terminal.........",
                "Gate terminal unlocked ok.",
                ]  
        }, 

    'a_switch': {
        'type': 'news',
        'words': 'xyz' 
        }, 
    }
