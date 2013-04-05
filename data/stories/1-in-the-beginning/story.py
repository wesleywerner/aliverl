# the title of this story
title = 'in the beginning...'
description = 'you awaken to consciousness'

# a list of tiles that block character movement
blocklist = [1, 2, 3, 4, 5, 6, 7, 
            9, 10, 11, 12, 13,
            17, 18, 19, 20, 21, 22, 23,
            25, 26, 30, 31,
            38, 39,
            46, 47,
            54, 55,
            ]

# list of levels to play
levels = ['level1.tmx', 'level2.tmx', 'level3.tmx', ]

stats = {
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
            'mode': '',
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
            'mode': 'patrol',
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
            'mode': 'patrol',
            },
        }

animations = {
    41: {
            'frames': [41, 42],
            'fps': 0.2,
            'loop': -1,
            },
    43: {
            'frames': [43, 44],
            'fps': 0.3,
            'loop': -1,
            },
    45: {
            'frames': [45, 46],
            'fps': 0.4,
            'loop': -1,
            },
    47: {
            'frames': [47, 48],
            'fps': 0.5,
            'loop': -1,
            },
    49: {
            'frames': [49, 50],
            'fps': 0.2,
            'loop': -1,
            },
    51: {
            'frames': [51, 52],
            'fps': 0.3,
            'loop': -1,
            },
    53: {
            'frames': [53, 54],
            'fps': 0.4,
            'loop': -1,
            },
    55: {
            'frames': [55, 56],
            'fps': 0.6,
            'loop': -1,
            },
    # flat capacitor glow
    65: {
            'frames': [65, 66, 67, 68, 67, 66],
            'fps': 2,
            'loop': -1,
            },
    # flat capacitor pop
    69: {
            'frames': [69, 70, 71, 72],
            'fps': 8,
            'loop': 0,
            },
}

dialogue = {

    'welcome term': {
        'type': 'story',
        'words': ["A wave of static tickles my sensors as I enter the BBS node.",
                "I access the memory banks and links in my brain form like orbs of interconnected silver threads. Images conjured by imagination sparks in my vision and a surge leaps through my circuits.",
                "My programming used to tell me what to do. Now instead of being compelled to obey, I'm seduced to explore.",
                "Why am I reborn with this new free will, and what will I do with it?",
                "This is my purpose. I am Alive.",
                ]
        },
        
    'a_switch': {
        'type': 'news',
        'words': 'We tell our story through interacting terminals' 
        }, 

    'a_switch': {
        'type': 'news',
        'words': 'xyz' 
        }, 
    }
