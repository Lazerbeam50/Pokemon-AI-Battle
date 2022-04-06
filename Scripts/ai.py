"""
Hold AI classes and all methods/functions for decision making
"""

import math
import random

import loaddata
import misc

class CombinedOption:
    def __init__(self, option1, option2):
        self.option1 = option1
        self.option2 = option2
        try:
            self.score = option1.score + option2.score
        except AttributeError:
            self.score = option1.score

class MoveData:
    def __init__(self, data, pokemon=None):
        self.id = data[0][0]
        self.identifier = data[0][1]
        self.typeID = data[0][2]
        self.power = misc.is_blank(data[0][3], None)
        self.pp = data[0][4]
        self.accuracy = misc.is_blank(data[0][5], None)
        self.priority = data[0][6]
        self.targetID = data[0][7]
        self.damageClassID = data[0][8]
        self.effectID = data[0][9]
        self.effectChance = misc.is_blank(data[0][10], None)

        #Check for hidden power
        if self.id == 237 and pokemon is not None:
            #Set up type bits
            if pokemon.hpIV % 2 == 0:
                a = 0
            else:
                a = 1
            if pokemon.atkIV % 2 == 0:
                b = 0
            else:
                b = 1
            if pokemon.defIV % 2 == 0:
                c = 0
            else:
                c = 1
            if pokemon.speIV % 2 == 0:
                d = 0
            else:
                d = 1
            if pokemon.spaIV % 2 == 0:
                e = 0
            else:
                e = 1
            if pokemon.spdIV % 2 == 0:
                f = 0
            else:
                f = 1

            #Calculate type value
            self.typeID = math.floor(((a + (2 * b) + (4 * c) + (8 * d) + (16 * e) + (32 * f)) * 5)/21) + 2

            #Set up damage bits
            if pokemon.hpIV % 4 in range(2, 4):
                u = 1
            else:
                u = 0
            if pokemon.atkIV % 4 in range(2, 4):
                v = 1
            else:
                v = 0
            if pokemon.defIV % 4 in range(2, 4):
                w = 1
            else:
                w = 0
            if pokemon.speIV % 4 in range(2, 4):
                x = 1
            else:
                x = 0
            if pokemon.spaIV % 4 in range(2, 4):
                y = 1
            else:
                y = 0
            if pokemon.spdIV % 4 in range(2, 4):
                z = 1
            else:
                z = 0

            #Calculate power
            self.power = math.floor((((u + (2 * v) + (4 * w) + (8 * x) + (16 * y) + (32 * z)) * 40)/63) + 30)

class PotentialMove:
    def __init__(self, identifier, typeID, damageClassID):
        self.identifier = identifier
        self.typeID = typeID
        self.damageClassID = damageClassID

class SingleOption:
    def __init__(self, user, move, score, target):
        self.user = user
        self.move = move
        self.score = score
        self.target = target

class AI:
    """
    Holds information gathered from battle and team preview, assumptions made about the opponents team,
    information about the AI team and methods for decision making
    """
    def __init__(self, team):
        self.enemyPokemonSeen = []
        self.gatherInfo = True
        self.useDefault = False
        self.team = team

    def compute_checks(self, values, inBattle=False):
        #Clear out check and counter lists
        for poke in values.team1.pokemon + values.team2.pokemon:
            poke.checks = []
            poke.checkedBy = []
            poke.counters = []
            poke.counteredBy = []

        if inBattle:
            #If we know which 4 pokemon the opponent has brought, only calculate checks for those pokemon
            if len(self.enemyPokemonSeen) == 4:
                team1 = [pkmn for pkmn in values.team1.pokemon if pkmn.nickname in self.enemyPokemonSeen]
            else:
                team1 = values.team1.pokemon
            team2 = values.battle.p2Active + values.battle.p2Side
        else:
            team1 = values.team1.pokemon
            team2 = self.team.pokemon
        #Iterate through each combination of player and AI pokemon
        for poke1 in team1:
            for poke2 in team2:
                #Iterate through all of players known and assumed moves, saving best damage factor
                bestDamage1 = self.get_best_damage_factor(poke1.potentialMoves, poke1, poke2)
                bestDamage1 = max(self.get_best_damage_factor(poke1.moveData, poke1, poke2), bestDamage1)

                # Iterate through all of AI's moves, saving best damage factor
                bestDamage2 = self.get_best_damage_factor(poke2.moveData, poke2, poke1)

                #Assign check and/or counters
                if bestDamage1 >= 200:
                    poke1.checks.append(poke2)
                    poke2.checkedBy.append(poke1)
                elif bestDamage1 < 100:
                    poke1.counteredBy.append(poke2)
                    poke2.counters.append(poke1)

                if bestDamage2 >= 200:
                    poke2.checks.append(poke1)
                    poke1.checkedBy.append(poke2)
                elif bestDamage2 < 100:
                    poke2.counteredBy.append(poke1)
                    poke1.counters.append(poke2)

    def gather_info(self, values, line):
        print("AI gathering line:", line)
        try:
            #If line is an enemy move, see if it is already in the known enemy move list
            if line.split("|")[1] == 'move' and line.split("|")[2][:2] == 'p1':
                move = line.split("|")[3].lower().replace(" ", "")
                for pkmn in values.battle.p1Active:
                    if pkmn.nickname == line.split("|")[2][5:].lower():
                        user = pkmn
                if move not in user.knownMoves:
                    # If not already listed, load data and add it add it
                    user.knownMoves.append(move)
                    user.moveData.append(MoveData(loaddata.load_moves(move)))
                    #If any of the enemy move lists are 4 items long, empty its potential moves list
                    if len(user.moveData) >= 4:
                        user.potentialMoves = []
                    #If any changes have taken place, recalculate checks and counters
                    self.compute_checks(values, inBattle=True)
            #If line is a switch, see if the ai has already seen this pokemon
            elif line.split("|")[1] == 'switch':
                player = line.split("|")[2][:2]
                pkmn = values.pokemon[player][line.split("|")[2][5:].lower()]
                pkmn.reset_stat_stages()
                if pkmn.nickname not in self.enemyPokemonSeen and player == 'p1':
                    self.enemyPokemonSeen.append(pkmn.nickname)
                    self.compute_checks(values, inBattle=True)
            #Record stat changes
            elif line.split("|")[1] == '-boost':
                player = line.split("|")[2][:2]
                pkmn = values.pokemon[player][line.split("|")[2][5:].lower()]
                pkmn.statStages[line.split("|")[3]] = min(
                    pkmn.statStages[line.split("|")[3]] + int(line.split("|")[4]), 6
                )
            elif line.split("|")[1] == '-unboost':
                player = line.split("|")[2][:2]
                pkmn = values.pokemon[player][line.split("|")[2][5:].lower()]
                pkmn.statStages[line.split("|")[3]] = max(
                    pkmn.statStages[line.split("|")[3]] - int(line.split("|")[4]), -6
                )

        except KeyError:
            pass
        except IndexError:
            pass

    def get_best_damage_factor(self, moveList, attacker, defender):
        bestDamage = 0
        for move in moveList:
            if move.damageClassID != 1:
                #damage1 = loaddata.type_matchup(move.typeID, defender.type1)[0][0]
                damage1 = self.get_type_effectiveness(move.typeID, defender.type1, attacker.knownAbility,
                                                      defender.knownAbility)
                if defender.type2 is not None:
                    #damage2 = loaddata.type_matchup(move.typeID, defender.type2)[0][0]
                    damage2 = self.get_type_effectiveness(move.typeID, defender.type2, attacker.knownAbility,
                                                          defender.knownAbility)
                else:
                    damage2 = 100
                bestDamage = int(max((damage1 * damage2) / 100, bestDamage))

        return bestDamage

    def handle_action_keyerror(self, values, battle, i):
        if 'trapped' in values.player2.request['active'][i]:
            choice = battle.p2Active[i].moves['moves'][0]
            values.player2.choices.append([battle.p2Active[i].nickname,
                                           choice['move'],
                                           choice['id'],
                                           1,
                                           "Placeholder"
                                           ])
        elif values.player2.request['active'][i]['moves'][0]['id'] in ('solarbeam', 'fly', 'dive', 'dig',
                                                                       'razorwind', 'skullbash', 'bounce',
                                                                       'skyattack'):
            choice = battle.p2Active[i].moves['moves'][0]
            values.player2.choices.append([battle.p2Active[i].nickname,
                                           choice['move'],
                                           choice['id'],
                                           1,
                                           "Placeholder"
                                           ])
        else:
            values.player2.choices.append(['default'])

    def get_standard_damage_score(self, battle, values, attacker, move, moveData, target):
        #Type matchup
        typeMatchup1 = self.get_type_effectiveness(moveData.typeID, target.type1, attacker.knownAbility,
                                                   target.knownAbility)
        if target.type2 is None:
            typeMatchup2 = 100
        else:
            typeMatchup2 = self.get_type_effectiveness(moveData.typeID, target.type2, attacker.knownAbility,
                                                   target.knownAbility)

        typeMatchup = int((typeMatchup1 * typeMatchup2)/100)

        #STAB
        if (moveData.typeID == attacker.type1 or moveData.typeID == attacker.type2
                or attacker.knownAbility == "normalize"):
            stab = 1.5
        else:
            stab = 1

        #Spread
        if move["target"] in ('all', 'allAdjacent', 'allAdjacentFoes'):
            spread = 0.75
        else:
            spread = 1

        #Accuracy
        accuracy = moveData.accuracy/100

        #Checks/Counters

        checks = 1 + (1 * len(target.checks)) + (0.5 * len(target.counters))

        score = typeMatchup * stab * spread * accuracy * checks

        return int(score)

    def get_type_effectiveness(self, moveType, defenderType, attackerAbility, defenderAbility):
        if moveType in (1, 2) and attackerAbility == "scrappy" and defenderType == 8:
            return 100
        elif moveType == 5 and defenderAbility == "levitate":
            return 0
        elif moveType == 10 and defenderAbility in ("flashfire", "flash-fire", "flash fire"):
            return 0
        elif moveType in (10, 15) and defenderAbility in ("thickfat", "thick-fat", "thick fat", "heatproof"):
            return 50
        elif moveType == 10 and defenderAbility in ("dryskin", "dry-skin", "dry skin"):
            return 125
        elif moveType == 11 and defenderAbility in ("waterabsorb", "water-absorb", "water absorb", "dryskin",
                                                    "dry-skin", "dry skin"):
            return 0
        elif moveType == 13 and defenderAbility in ("voltabsortb", "volt-absorb", "volt absorb", "motordrive",
                                                    "motor-drive", "motor drive"):
            return 0
        elif attackerAbility == "normalize":
            return loaddata.type_matchup(1, defenderType)[0][0]
        else:
            return loaddata.type_matchup(moveType, defenderType)[0][0]

    def handle_force_switch(self, battle, values):
        # Iterate through options in request
        options = []
        for pkmn in values.player2.request['side']['pokemon']:
            # Randomly select a pokemon that is not active and still has HP
            if not pkmn['active'] and pkmn['condition'] != '0 fnt':
                options.append(pkmn)
        # Set up choices list

        random.shuffle(options)
        fainted = int(values.player2.request['forceSwitch'][0]) + int(values.player2.request['forceSwitch'][1])
        #Attempted fix for double ko bug. When no pkmn are active and only one is on the bench, use the default action
        if fainted == 2 and len(options) == 1:
            values.player2.choices.append(['default'])
        else:
            for i in range(min(fainted, len(options))):
                values.player2.choices.append([
                    "",
                    options[i]['ident'][4:]
                ])

        battle.p2Ready = True
        if battle.p1Ready:
            battle.state = 8
            battle.doneSetup = False

class Pallet(AI):

    """
    Completely random decision making. No ally targeting or switching.
    """

    def __init__(self, team):
        AI.__init__(self, team)
        self.gatherInfo = False

    def team_preview(self, values):
        order = [0, 1, 2, 3, 4, 5]
        random.shuffle(order)
        self.team.selected = [self.team.pokemon[order[0]],
                              self.team.pokemon[order[1]],
                              self.team.pokemon[order[2]],
                              self.team.pokemon[order[3]]
                              ]

    def select_actions(self, battle, values):
        for i in range(len(battle.p2Active)):
            try:
                availableMoves = []
                for move in battle.p2Active[i].moves['moves']:
                    if move['pp'] > 0 and not move['disabled']:
                        availableMoves.append(move)
                choice = random.choice(availableMoves)
                target = None
                if 'target' in choice:
                    if choice['target'] in ['normal', 'any']:
                        target = random.choice(battle.p1Active)
                    elif choice['target'] == 'adjacentAlly':
                        target = -3 - battle.p2Active[i].allyLocation
                if target is None:
                    values.player2.choices.append([battle.p2Active[i].nickname,
                                                   choice['move'],
                                                   choice['id']
                                                   ])
                elif choice['target'] == 'adjacentAlly':
                    values.player2.choices.append([battle.p2Active[i].nickname,
                                                   choice['move'],
                                                   choice['id'],
                                                   target,
                                                   "Placeholder"])
                else:
                    values.player2.choices.append([battle.p2Active[i].nickname,
                                                   choice['move'],
                                                   choice['id'],
                                                   target.enemyLocation,
                                                   target.nickname])
            except KeyError:
                if i == 0:
                    self.handle_action_keyerror(values, battle, i)
                else:
                    self.useDefault = True

        if self.useDefault:
            self.handle_action_keyerror(values, battle, 1)

            self.useDefault = False

        battle.p2Ready = True

class NewBark(Pallet):

    """
    Completely random decision making. No ally targeting. 10% chance to switch each pokemon per turn if possible.
    """

    def __init__(self, team):
        Pallet.__init__(self, team)
        self.gatherInfo = False

    def select_actions(self, battle, values):

        switchOptions = [
            option for option in battle.p2Side if (
                    not option.switchTarget and option.request['condition'] != '0 fnt'
            )
        ]

        for i in range(len(battle.p2Active)):
            try:
                availableMoves = []
                for move in battle.p2Active[i].moves['moves']:
                    if move['pp'] > 0 and not move['disabled']:
                        availableMoves.append(move)
                choice = random.choice(availableMoves)
                target = None
                if 'target' in choice:
                    if choice['target'] in ['normal', 'any']:
                        target = random.choice(battle.p1Active)
                    elif choice['target'] == 'adjacentAlly':
                        target = -3 - battle.p2Active[i].allyLocation
                if switchOptions and random.randint(1, 10) == 1:
                    option = random.choice(switchOptions)
                    switchOptions.remove(option)
                    option.switchTarget = True
                    values.player2.choices.append([
                        option.nickname,
                        option.slotLocation
                    ])
                elif target is None:
                    values.player2.choices.append([battle.p2Active[i].nickname,
                                                   choice['move'],
                                                   choice['id']
                                                   ])
                elif choice['target'] == 'adjacentAlly':
                    values.player2.choices.append([battle.p2Active[i].nickname,
                                                   choice['move'],
                                                   choice['id'],
                                                   target,
                                                   "Placeholder"])
                else:
                    values.player2.choices.append([battle.p2Active[i].nickname,
                                                   choice['move'],
                                                   choice['id'],
                                                   target.enemyLocation,
                                                   target.nickname])
            except KeyError:
                if i == 0:
                    self.handle_action_keyerror(values, battle, i)
                else:
                    self.useDefault = True

        if self.useDefault:
            self.handle_action_keyerror(values, battle, 1)

            self.useDefault = False

        battle.p2Ready = True

class Littleroot(AI):
    """
    Standard AI
    """

    def __init__(self, team):
        AI.__init__(self, team)

    def team_preview(self, values):

        #Assign types to pokemon

        for team in (values.team1, values.team2):
            for poke in team.pokemon:
                types = loaddata.load_pokemon_types(poke.species)
                poke.type1 = types[0][0]
                try:
                    poke.type2 = types[1][0]
                except IndexError:
                    poke.type2 = None

        #Assume opponent's moves

        for poke in values.team1.pokemon:
            poke.potentialMoves.append(PotentialMove("Generic move", poke.type1, 2))
            if poke.type2 is not None:
                poke.potentialMoves.append(PotentialMove("Generic move", poke.type2, 2))

        #Load moves and set known ablity
        for poke in self.team.pokemon:
            moves = (poke.move1, poke.move2, poke.move3, poke.move4)
            poke.knownAbility = poke.ability
            for move in moves:
                poke.moveData.append(MoveData(loaddata.load_moves(move), poke))

        self.compute_checks(values)

        order = [0, 1, 2, 3, 4, 5]
        random.shuffle(order)

        self.team.selected = [self.team.pokemon[order[0]],
                              self.team.pokemon[order[1]],
                              self.team.pokemon[order[2]],
                              self.team.pokemon[order[3]]
                              ]

    def select_actions(self, battle, values):
        #Note number of active pokemon
        numberActive = 0
        #Iterate through active pokemon
        singleOptions = [[],[]]
        for i in range(len(battle.p2Active)):
            try:
                #Iterate through moves
                availableMoves = []
                for move in battle.p2Active[i].moves['moves']:
                    if move['pp'] > 0 and not move['disabled']:
                        availableMoves.append(move)

                # Iterate through available move options
                for move in availableMoves:
                    #Calculate scores for move options
                    score1 = 0
                    score2 = None
                    moveData = [m for m in battle.p2Active[i].moveData if move['id'] == m.identifier][0]
                    #If move is damaging and hits all opponents
                    if moveData.damageClassID in range(2, 4) and move['target'] in ('all', 'allAdjacent'):
                        for foe in battle.p1Active:
                            score1 += self.get_standard_damage_score(battle, values, battle.p2Active[i], move, moveData,
                                                                    foe)
                        if len(battle.p2Active) == 2:
                            if i == 0:
                                j = 1
                            else:
                                j = 0
                            score1 -= self.get_standard_damage_score(battle, values, battle.p2Active[i], move, moveData,
                                                                    battle.p2Active[j]) * 1.5
                    elif moveData.damageClassID in range(2, 4) and move['target'] == 'allAdjacentFoes':
                        for foe in battle.p1Active:
                            score1 += self.get_standard_damage_score(battle, values, battle.p2Active[i], move, moveData,
                                                                    foe)

                    elif moveData.damageClassID in range(2, 4) and move['target'] in ('any', 'normal'):
                        try:
                            score1 = self.get_standard_damage_score(battle, values, battle.p2Active[i], move, moveData,
                                                                    battle.p1Active[0])
                            score2 = self.get_standard_damage_score(battle, values, battle.p2Active[i], move, moveData,
                                                                    battle.p1Active[1])
                        except IndexError:
                            pass

                    else:
                        score1 = 100
                        if move['target'] in ('any', 'normal'):
                            score2 = 100

                    singleOptions[i].append(SingleOption(battle.p2Active[i], move, max(score1, 0), 0))
                    if score2 is not None:
                        singleOptions[i].append(SingleOption(battle.p2Active[i], move, max(score2, 0), 1))

                numberActive += 1

            except KeyError:
                if i == 0:
                    self.handle_action_keyerror(values, battle, i)
                else:
                    self.useDefault = True


        #If two active pokemon, create cross join of options and sum scores
        combinedOptions = []
        if numberActive == 2:
            for option1 in singleOptions[0]:
                for option2 in singleOptions[1]:
                    combinedOptions.append(CombinedOption(option1, option2))
        else:
            if not singleOptions[0]:
                i = 1
            else:
                i = 0
            for option1 in singleOptions[i]:
                combinedOptions.append(CombinedOption(option1, None))
        #Randomly choose between the joint highest combinations
        if combinedOptions:
            try:
                topScore = max([o.score for o in combinedOptions])
            except ValueError:
                print("Let's look!")
            finalOptions = [o for o in combinedOptions if o.score == topScore]
            choice = random.choice(finalOptions)

            #Write choice to showdown
            options = [choice.option1, choice.option2]
            for option in options:
                try:
                    target = None
                    if 'target' in option.move:
                        if option.move['target'] in ['normal', 'any']:
                            try:
                                target = battle.p1Active[option.target]
                            except IndexError:
                                print("Let's look!")
                        elif option.move['target'] == 'adjacentAlly':
                            target = -3 - option.user.allyLocation
                    if target is None:
                        values.player2.choices.append([option.user.nickname,
                                                       option.move['move'],
                                                       option.move['id']
                                                       ])
                    elif option.move['target'] == 'adjacentAlly':
                        values.player2.choices.append([option.user.nickname,
                                                       option.move['move'],
                                                       option.move['id'],
                                                       target,
                                                       "Placeholder"])
                    else:
                        values.player2.choices.append([option.user.nickname,
                                                       option.move['move'],
                                                       option.move['id'],
                                                       target.enemyLocation,
                                                       target.nickname])

                except AttributeError:
                    pass

            if self.useDefault:
                self.handle_action_keyerror(values, battle, 1)

                self.useDefault = False

        battle.p2Ready = True

