# the title of this story
title = 'in the beginning...'
description = 'you awaken to consciousness'

# a list of tiles that block character movement
blocklist = []

# list of levels to play
levels = ['level1.tmx', 'level3.tmx', 'level3.tmx', ]

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
            'mode': ''
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
            'mode': 'patrol'
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
            'mode': 'patrol'
            }
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
