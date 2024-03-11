from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def generate_admin_keyboard():
    admin_buttons = InlineKeyboardMarkup()
    
    send_broadcast_button = InlineKeyboardButton("Удалить", callback_data='delete_admin_menu')
    grant_access_button = InlineKeyboardButton("Выдать админа", callback_data='grant_access')
    revoke_access_button = InlineKeyboardButton("Отозвать доступ", callback_data='revoke_access')
    send_personal_message_button = InlineKeyboardButton("Отправить личное сообщение", callback_data='send_personal_message')
    mailing_users = InlineKeyboardButton("Сделать рассылку", callback_data='mailing')
    main_menu_button = InlineKeyboardButton("❤️Главное меню", callback_data='back_to_start')
    
    admin_buttons.row(send_broadcast_button)
    admin_buttons.row(grant_access_button, revoke_access_button)
    admin_buttons.row(send_personal_message_button)
    admin_buttons.row(mailing_users)
    admin_buttons.row(main_menu_button)
    
    return admin_buttons