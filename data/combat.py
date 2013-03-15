from character import Character
import trace

def Combat(foo, bar):
    """ Combats the two given Characters """
    result = []
    # allow for potential damage mitigation
    foo_atk = foo.attack
    bar_atk = bar.attack
    # each deals damage
    foo.health -= bar_atk
    result.append('%s deals %s damage to %s (%s)' % (bar.name, bar.attack, foo.name, foo.health) )
    bar.health -= foo_atk
    result.append('%s deals %s damage to %s (%s)' % (foo.name, foo.attack, bar.name, bar.health) )
    # death
    foo.dead = foo.health < 1
    bar.dead = bar.health < 1
    # print results
    for r in result:
        trace.write(r)
    return result
