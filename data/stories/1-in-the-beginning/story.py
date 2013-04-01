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

# define npc and player stats. (lowercase keys please)
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
            'frames': [],
            'fps': 0
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
            'frames': [],
            'fps': 0
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
            'frames': [],
            'fps': 1
            },
        }

animations = {
    41: {
            'frames': [41, 42],
            'fps': 0.2
            },
    43: {
            'frames': [43, 44],
            'fps': 0.3
            },
    45: {
            'frames': [45, 46],
            'fps': 0.4
            },
    47: {
            'frames': [47, 48],
            'fps': 0.5
            },
    49: {
            'frames': [49, 50],
            'fps': 0.2
            },
    51: {
            'frames': [51, 52],
            'fps': 0.3
            },
    53: {
            'frames': [53, 54],
            'fps': 0.4
            },
    55: {
            'frames': [55, 56],
            'fps': 0.5
            },
}

# define story dialogue. shown by giving a level object the property:
#   dialogue<_foo_once>=<name>
dialogue = {

    'welcome_term': {
        'type': 'story',
        'words': 'This is a line of dialogue'
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
