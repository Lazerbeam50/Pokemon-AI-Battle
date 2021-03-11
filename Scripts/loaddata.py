import sqlite3

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