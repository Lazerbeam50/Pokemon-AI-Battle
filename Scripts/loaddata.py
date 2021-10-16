import sqlite3

def load_moves(move):
    db = sqlite3.connect('Game data/game_data')
    cursor = db.cursor()
    cursor.execute('''
        SELECT  id,
                identifier,
                type_id,
                power,
                pp,
                accuracy,
                priority,
                target_id,
                damage_class_id,
                effect_id,
                effect_chance
        FROM moves
        WHERE identifier = ?
        ''', (move,))
    data = cursor.fetchall()
    cursor.close()
    db.close()
    return data

def load_player(player):
    db = sqlite3.connect('Game data/game_data')
    cursor = db.cursor()
    cursor.execute(f'''
        SELECT *
        FROM Characters
        WHERE charID = {player}
        ''')
    data = cursor.fetchall()
    cursor.close()
    db.close()
    return data

def load_team(team):
    db = sqlite3.connect('Game data/game_data')
    cursor = db.cursor()
    cursor.execute(f'''
            SELECT *
            FROM Teams t
            JOIN BattlePokemon p ON t.teamID = p.teamID
            WHERE t.teamID = {team}
            ''')
    data = cursor.fetchall()
    cursor.close()
    db.close()
    return data

def load_pokemon_sprites(pokemon):
    db = sqlite3.connect('Game data/game_data')
    cursor = db.cursor()
    cursor.execute('''
                SELECT *
                FROM PokemonMedia
                WHERE species = ?
                ''',(pokemon,))
    data = cursor.fetchall()
    cursor.close()
    db.close()
    return data

def load_pokemon_types(pokemon):
    db = sqlite3.connect('Game data/game_data')
    cursor = db.cursor()
    cursor.execute('''
                    SELECT t.type_id
                    FROM PokemonSpecies s
                    JOIN PokemonTypes t ON s.id = t.pokemon_id
                    WHERE s.identifier = ?
                    ORDER BY t.slot
                    ''', (pokemon,))
    data = cursor.fetchall()
    cursor.close()
    db.close()
    return data

def type_matchup(attacker, defender):
    db = sqlite3.connect('Game data/game_data')
    cursor = db.cursor()
    cursor.execute(f'''
                    SELECT damage_factor
                    FROM TypeMatchups
                    WHERE damage_type_id = {attacker} AND target_type_id = {defender}
                    ''')
    data = cursor.fetchall()
    cursor.close()
    db.close()
    return data