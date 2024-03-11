import json

async def open_db():
    try:
        with open('bot/database/db.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError
    return db

async def save_db(data):
    with open('bot/database/db.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def open_db_tarif():
    try:
        with open('bot/database/tarifs.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError
    return db