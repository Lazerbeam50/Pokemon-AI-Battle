"""
Used to set up the empty database and tables.
"""
import sqlite3

def set_up_empty_database():
    db = sqlite3.connect('Game data/game_data')
    cursor = db.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Characters
    (
    charID INTEGER PRIMARY KEY,
    name TEXT,
    sprite TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS BattlePokemon
    (
    pokeID INTEGER PRIMARY KEY,
    teamID INTEGER,
    nickname TEXT,
    species TEXT,
    gender TEXT,
    item TEXT,
    ability TEXT,
    hpEV INTEGER,
    atkEV INTEGER,
    defEV INTEGER,
    spaEV INTEGER,
    spdEV INTEGER,
    speEV INTEGER,
    hpIV INTEGER,
    atkIV INTEGER,
    defIV INTEGER,
    spaIV INTEGER,
    spdIV INTEGER,
    speIV INTEGER,
    nature TEXT,
    move1 TEXT,
    move2 TEXT,
    move3 TEXT,
    move4 TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Moves
    (
    id INTEGER,
    identifier TEXT PRIMARY KEY,
    type_id INTEGER,
    power INTEGER,
    pp INTEGER,
    accuracy INTEGER,
    priority INTEGER,
    target_id INTEGER,
    damage_class_id INTEGER,
    effect_id INTEGER,
    effect_chance INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PokemonMedia
    (
    species TEXT,
    frontsprite TEXT,
    backsprite TEXT,
    minisprite TEXT,
    cry TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PokemonSpecies
    (
    id,
    identifier TEXT PRIMARY KEY
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PokemonStats
    (
    pokemon_id INTEGER,
    stat_id INTEGER,
    base_stat INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PokemonTypes
    (
    pokemon_id INTEGER,
    type_id INTEGER,
    slot INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Teams
    (
    teamID INTEGER PRIMARY KEY,
    charID INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS TypeMatchups
    (
    damage_type_id INTEGER,
    target_type_id INTEGER,
    damage_factor INTEGER
    )
    ''')

    db.commit()
    cursor.close()
    db.close()

set_up_empty_database()