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
    CREATE TABLE IF NOT EXISTS Teams
    (
    teamID INTEGER PRIMARY KEY,
    charID INTEGER
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
    CREATE TABLE IF NOT EXISTS PokemonMedia
    (
    species TEXT,
    frontsprite TEXT,
    backsprite TEXT,
    minisprite TEXT,
    cry TEXT
    )
    ''')

    db.commit()
    cursor.close()
    db.close()

set_up_empty_database()