import json

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def is_admin(user_id):
    with open('bot/database/db.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    user_data = data.get(str(user_id), {})  
    return user_data.get("is_admin", False) 

def generate_main_menu(user_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔎 Чекер", callback_data='checker'),
               InlineKeyboardButton("👤 Профиль", callback_data='profile'))
    markup.add(InlineKeyboardButton("❔ Инфо", callback_data='info'))

    if is_admin(user_id):
        admin_button = InlineKeyboardButton("🛠️ Админ панель", callback_data='admin_panel')
        markup.add(admin_button)

    return markup

def subscribe_buy_menu(user_id, tarifs):
    markup = InlineKeyboardMarkup()

    tarif_buttons = []
    for tarif_name, tarif_data in tarifs.get("tarifs", {}).items():
        button_text = f"{tarif_data['emoji']}{tarif_name} - {tarif_data['price']} ₽"
        callback_data = f'subscribe_{tarif_name.lower()}_{tarif_data["id"]}'
        tarif_button = InlineKeyboardButton(button_text, callback_data=callback_data)
        tarif_buttons.append(tarif_button)

    markup.add(*tarif_buttons)
    return markup

back_button = InlineKeyboardButton("⁉️ Главное меню", callback_data='back_to_start')
keyboard = InlineKeyboardMarkup().add(back_button)