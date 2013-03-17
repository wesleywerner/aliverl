from character import Character
import trace

def Combat(player, enemy):
    """ Combats the two given Characters """
    result = []
    # allow for potential damage mitigation
    player_atk = player.attack
    enemy_atk = enemy.attack
    # each deals damage
    player.health -= enemy_atk
    result.append('* the %s hits you for %s.' % (enemy.name, enemy.attack) )
    enemy.health -= player_atk
    result.append('* you hit the %s for %s.' % (enemy.name, player.attack) )
    # death
    player.dead = player.health < 1
    enemy.dead = enemy.health < 1
    # print results
    trace.write(result)
    return result
