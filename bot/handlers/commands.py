from aiogram import types
from aiogram.utils.exceptions import ChatNotFound
from aiogram.types import InputFile, InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from aiogram.dispatcher import FSMContext

from bot.database import open_db, save_db, open_db_tarif
from bot.bot import dp, bot
from bot.utils import proxy_check, download_file, validate_proxy_format
from bot.keyboards.keyboard_admin import generate_admin_keyboard
from bot.keyboards import keyboard as kb
from bot.states.state import SomeState, MailingState

import io
import json
import time
import asyncio

from AsyncPayments.crystalPay import AsyncCrystalPay


from config import (
    crystal_pay_login, crystal_pay_secret, crystal_pay_salt
)

crystalPay = AsyncCrystalPay(crystal_pay_login, crystal_pay_secret, crystal_pay_salt)


allowed_users = [1]

async def reset_use_periodically():
    """ Обнуляем использования в день у пользователей """

    print('Счётчик №1 запущен')
    while True:
        await asyncio.sleep(24 * 60 * 60)
        
        db = await open_db()
        for user_id, user_data in db.items():
            if "subscription" in user_data:
                user_data["use"] = 0
                print(f'Сбросил для пользователя с ID {user_id}')
        await save_db(db)

async def subscribe():
    """ Обнуляем подписки у пользователей """
    print('Счётчик №2 запущен')
    # while True:
    #     pass

async def on_startup_commands(_):
    asyncio.create_task(reset_use_periodically())
    asyncio.create_task(subscribe())
    print('Бот запущен!')

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = str(message.from_user.id)

    new_data = {
        "is_admin": False,
        "is_super": True,
        "subscribe": "Free",
        "use": 0
    }

    db = await open_db()

    if user_id not in db:
        db[user_id] = new_data

    await save_db(db)


    # if user_id not in allowed_users:
    #     video_path = os.path.join(current_directory, "video.mp4")
    #     video = open(video_path, "rb")
    #     try:
    #         await bot.delete_message(message.chat.id, message.message_id)
    #     except MessageToDeleteNotFound as e:
    #         print(f"Ошибка удаления сообщения: {e}")
        
    #     sent_message = await bot.send_video(message.chat.id, video, caption="<b>⛔️ В доступе отказано.</b>", parse_mode='HTML')
    #     video.close()

    #     delete_button = InlineKeyboardButton("Удалить сообщение", callback_data=f'delete_message_{sent_message.message_id}')
    #     keyboard = InlineKeyboardMarkup().add(delete_button)

    #     await bot.edit_message_reply_markup(message.chat.id, message_id=sent_message.message_id, reply_markup=keyboard)
    #     return

    await bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAJdhWVZT1v5RNc1j8EXE9zMrpR79XaDAAI7AwACtXHaBhhLBtJVU8tEMwQ')
    await message.reply(f"👋 {message.from_user.first_name}, <b>добро пожаловать в бот проверки прокси, IPv4.</b>",
                        parse_mode="HTML", reply_markup=kb.generate_main_menu(user_id))
    

@dp.callback_query_handler(lambda c: c.data.startswith('delete_message_'))
async def delete_message(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id

    await bot.delete_message(chat_id, message_id=callback_query.message.message_id)
    await bot.answer_callback_query(callback_query.id, text="Сообщение удалено", show_alert=True)
    

@dp.callback_query_handler(lambda c: c.data == 'info')
async def process_callback_button(callback_query: types.CallbackQuery):
    keyboard = generate_keyboard()

    back_to_start_button = InlineKeyboardButton("⤶ Назад", callback_data='back_to_start')
    keyboard.add(back_to_start_button)

    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="<b>❗️ Выберите действие:</b>",
        parse_mode='HTML',
        reply_markup=keyboard
    )

def generate_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Разработчик (обновил код)", url="https://t.me/reques6e666"))
    return markup


@dp.callback_query_handler(lambda c: c.data == 'delete_menu')
async def delete_menu(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.answer_callback_query(callback_query.id, text="Меню скрыто", show_alert=True)

@dp.callback_query_handler(lambda c: c.data == 'cancel', state=SomeState.waiting_for_proxy)
async def cancel_action(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_id = data.get('message_id')
    if message_id:
        sent_message = await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                                  message_id=message_id,
                                                  text="Отменено",
                                                  parse_mode="HTML")
        delete_button = InlineKeyboardButton("🗑Удалить", callback_data=f'delete_message_{sent_message.message_id}')
        keyboard = InlineKeyboardMarkup().add(delete_button)
        await bot.edit_message_reply_markup(callback_query.from_user.id, message_id=sent_message.message_id, reply_markup=keyboard)

    await state.finish()
    await callback_query.answer("✅ Успешно отменено", show_alert=True)

@dp.callback_query_handler(lambda c: c.data == 'checker')
async def checker(callback_query: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    cancel_button = InlineKeyboardButton("Отменить действие", callback_data='cancel')
    keyboard.row(cancel_button)

    msg = await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                      message_id=callback_query.message.message_id,
                                      text="<i>Введите прокси для проверки в формате IP:PORT:USERNAME:PASSWORD</i>",
                                      reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(SomeState.waiting_for_proxy)
    await state.update_data(message_id=msg.message_id)

@dp.message_handler(state=SomeState.waiting_for_proxy, content_types=[ContentType.TEXT, ContentType.DOCUMENT])
async def process_proxy(message: types.Message, state: FSMContext):
    if message.content_type == ContentType.TEXT:
        proxies_text = message.text
        if not proxies_text or not proxies_text.strip():
            await message.reply("<b>⚠️ Текст должен быть непустым.</b>", parse_mode="HTML")
            return
    elif message.content_type == ContentType.DOCUMENT:
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_url = file.file_path
        proxies_text = await download_file(file_url)

        if not proxies_text or not proxies_text.strip():
            await message.reply("<b>⚠️ Файл должен содержать непустые данные.</b>", parse_mode="HTML")
            return
    else:
        await message.reply("<b>⚠️ Неподдерживаемый тип контента. Пожалуйста, используйте текстовое сообщение или отправьте файл .txt.</b>", parse_mode="HTML")
        return

    proxies = set(proxies_text.split('\n'))

    if not proxies:
        await message.reply("<b>⚠️ Проверьте верность данных и введите ещё раз.</b>", parse_mode="HTML")
        return

    await bot.send_message(message.chat.id, f"Чекер запущен...")

    valid_proxies = []
    invalid_proxies = []

    for proxy in proxies:
        if not validate_proxy_format(proxy):
            invalid_proxies.append(proxy)
            await bot.send_message(message.chat.id, f"Не правильный формат прокси: {proxy}")
            continue  

        if await proxy_check([proxy]) == True:
            valid_proxies.append(proxy)
        else:
            invalid_proxies.append(proxy)

    valid_count = len(valid_proxies)
    invalid_count = len(invalid_proxies)

    user_id = str(message.from_user.id)
    db = await open_db()
    tarifs = await open_db_tarif()
    user_data = db.get(user_id, {"is_admin": False, "is_super": True, "subscribe": "Free", "use": 0})

    if user_data['subscribe'] == 'Free':
        kd = 7
    else:
        tarif_name = user_data['subscribe']
        kd = tarifs['tarifs'][str(tarif_name.capitalize())]['kd']

    if user_data["use"] + valid_count > kd:
        await message.reply("<b>⛔️ Превышен лимит использований чекера прокси.</b>", parse_mode="HTML")
        return
    
    user_data["use"] += valid_count + invalid_count

    db[user_id] = user_data
    await save_db(db)

    valid_text = f"<b>✅ Валидные прокси ({valid_count}/{valid_count + invalid_count})</b>"
    invalid_text = f"<b>⛔️ Невалидные прокси ({invalid_count}/{valid_count + invalid_count})</b>"

    valid_proxies_file_content = '\n'.join(valid_proxies).encode('utf-8')
    if valid_proxies_file_content:
        valid_proxies_file = InputFile(io.BytesIO(valid_proxies_file_content), filename='valids.txt')
        await bot.send_document(message.chat.id, valid_proxies_file,
                                caption=f"{valid_text}\n{invalid_text}\n\nСпасибо за использование чекера!",
                                parse_mode="HTML")
    else:
        await message.reply("<b>⚠️ Нет валидных прокси для отправки.</b>", parse_mode="HTML")

    await state.finish()


    
@dp.callback_query_handler(lambda c: c.data == 'profile')
async def profile(callback_query: types.CallbackQuery):    
    user_id = callback_query.from_user.id
    user = callback_query.from_user
    
    db = await open_db()

    if user.username:
        user_link = f"<a href='tg://user?id={user_id}'>#{user.username}</a>"
    else:
        user_link = f"<a href='tg://user?id={user_id}'>Отсутствует</a>"

    profile_text = f"🙋🏻‍♂️ Твой ID: [<code>{user_id}</code>]\n" \
                   f"💎 Твой тег: <b>{user_link}</b>\n" \
                   f"💰 Подписка: <b>{db[str(user_id)]['subscribe']}</b>\n" 

    buy_subscribe = InlineKeyboardButton("💰Купить подписку", callback_data='subscribe_buy')              
    back_button = InlineKeyboardButton("🔙 Назад", callback_data='back_to_start')
    
    keyboard = InlineKeyboardMarkup().add(buy_subscribe, back_button)
    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text=profile_text, parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'subscribe_buy')
async def subscribe_buy(callback_query: types.CallbackQuery):
    with open('bot/database/tarifs.json', 'r', encoding='utf-8') as f:
        tarifs = json.load(f)

    user_id = callback_query.from_user.id

    text = "<b>💰Выберите тариф:</b>\n\n"

    for tarif_name, tarif_data in tarifs.get("tarifs", {}).items():
        text += f"<b>{tarif_data['emoji']}{tarif_name}</b>\n" \
                f"Копирайт: <code>{tarif_data.get('copyright')}</code>\n" \
                f"Реклама: <code>{tarif_data.get('adsense')}</code>\n" \
                f"Кд: <code>{tarif_data.get('kd')}/день</code>\n" \
                f"Цена: <b>{tarif_data.get('price')} Руб/месяц</b>\n\n"

    menu = kb.subscribe_buy_menu(user_id, tarifs)

    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text=text,
                                parse_mode="HTML", reply_markup=menu)


    
@dp.callback_query_handler(lambda c: c.data == 'back_to_start')
async def back_to_start(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    main_menu = kb.generate_main_menu(user_id)
    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text="<b>👋 Добро пожаловать в бот проверки прокси, IPv4.</b>",
                                parse_mode="HTML", reply_markup=main_menu)

    

@dp.callback_query_handler(lambda c: c.data == 'admin_panel')
async def admin_panel(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user = callback_query.from_user

    admin_markup = generate_admin_keyboard()

    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"🌟<b>Приветствую</b> <a href='tg://user?id={user_id}'>// {user.username}</a><b>, в админ-панели!</b>",
        parse_mode='HTML',
        reply_markup=admin_markup
    )

@dp.callback_query_handler(lambda c: c.data == 'grant_access')
async def grant_access_callback(callback_query: types.CallbackQuery):
    db = await open_db()
    if str(callback_query.from_user.id) in db and db[str(callback_query.from_user.id)].get("is_super", False):
        await bot.send_message(callback_query.from_user.id,
                            "<b>Введите ID пользователя, которому вы хотите предоставить доступ админа</b>",
                            parse_mode='HTML')
        await SomeState.waiting_for_user_id.set()
    else:
        await bot.send_message(callback_query.from_user.id, "У вас нет прав на выдачу администраторских прав.")

@dp.message_handler(state=SomeState.waiting_for_user_id)
async def process_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        db = await open_db()

        if str(user_id) in db:
            if user_id == str(message.from_user.id):
                await bot.send_message(user_id, "Вы не можете выдать админа самому себе")
            if db[str(user_id)]["is_admin"]:
                await bot.send_message(user_id, "Пользователь уже является администратором")
                return 
            else:
                db[str(user_id)]["is_admin"] = True
                await save_db(db)

                try:
                    await bot.send_message(user_id, "🥳")
                    time.sleep(1)
                    await bot.send_message(user_id, "Вам был предоставлен доступ к админ панели.")
                    await bot.send_message(
                        message.chat.id,
                        f"Пользователь с ID <code>{user_id}</code> получил доступ к админ панели.",
                        parse_mode='HTML',
                        reply_markup=generate_admin_keyboard()
                    )
                except ChatNotFound:
                    pass
        else:
            await message.reply("Пользователь с таким ID не найден в базе данных.")
    except ValueError:
        await message.reply("Ошибка. Введите корректный ID пользователя.")
    finally:
        await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'send_personal_message')
async def send_personal_message(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    cancel_button = InlineKeyboardButton("Отменить действие", callback_data='cancel')
    keyboard.row(cancel_button)

    await bot.send_message(callback_query.from_user.id,
                           "<b>Введите ID пользователя, которому хотите отправить личное сообщение:</b>",
                           parse_mode='HTML',
                           reply_markup=keyboard)
    await SomeState.waiting_for_personal_message_id.set()

@dp.message_handler(state=SomeState.waiting_for_personal_message_id)
async def process_personal_message_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)

        if user_id in allowed_users:
            await state.update_data(user_id=user_id)
            await bot.send_message(message.chat.id,
                                   "Введите сообщение, которое хотите отправить этому пользователю:")
            await SomeState.waiting_for_personal_message_text.set()
        else:
            await message.reply("Этот пользователь не имеет доступа к боту.")
            await state.finish()
    except ValueError:
        await message.reply("Ошибка. Введите корректный ID пользователя.")

@dp.message_handler(state=SomeState.waiting_for_personal_message_text)
async def process_personal_message_text(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        user_id = data.get('user_id')
        personal_message = message.text

        if user_id in allowed_users:
            delete_button = types.InlineKeyboardButton("🗑Удалить", callback_data='delete_admin_menu')
            delete_message = types.InlineKeyboardMarkup().add(delete_button)
            await bot.send_message(
                user_id,
                personal_message,
                parse_mode='HTML',
                reply_markup=delete_message
            )
            await bot.send_message(
                message.chat.id,
                f"Личное сообщение было успешно отправлено пользователю с ID <code>{user_id}</code>.",
                parse_mode='HTML',
                reply_markup=generate_admin_keyboard()
            )
        else:
            await message.reply("Этот пользователь больше не имеет доступа к боту.")
    except Exception as e:
        await message.reply("Произошла ошибка при отправке сообщения. Попробуйте еще раз.")
    finally:
        await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'revoke_access')
async def revoke_access_from_user(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id,
                           "<b>Введите ID пользователя, у которого нужно отозвать доступ:</b>",
                           parse_mode='HTML')
    await SomeState.waiting_to_revoke.set()

@dp.message_handler(state=SomeState.waiting_to_revoke)
async def process_revoke_access(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        db = await open_db()

        if str(user_id) in db:
            if user_id == str(message.from_user.id):
                await bot.send_message(user_id, "Вы не можете отозвать админа у себя.")
            if db[str(user_id)]["is_admin"] == False:
                await bot.send_message(user_id, "Пользователь не являлся администратором")
                return 
            else:
                db[str(user_id)]["is_admin"] = False
                await save_db(db)
                
                try:
                    await bot.send_message(user_id, "🥳")
                    time.sleep(1)
                    await bot.send_message(user_id, "У вас отозвали доступ к админ панели")
                    await bot.send_message(
                        message.chat.id,
                        f"У пользователя с ID <code>{user_id}</code> отозвали доступ к админ панели.",
                        parse_mode='HTML',
                        reply_markup=generate_admin_keyboard()
                    )
                except ChatNotFound:
                    pass
        else:
            await message.reply("Пользователь с таким ID не найден в базе данных.")
    except ValueError:
        await message.reply("Ошибка. Введите корректный ID пользователя.")
    finally:
        await state.finish()


@dp.message_handler()
async def handle_messages(message: types.Message):
    user_id = message.from_user.id

    if user_id not in allowed_users:
        try:
            await bot.delete_message(message.chat.id, message.message_id)
            await bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAJc5GVXHyKMoj-oSZYYNhrirj9egu_DAAIoAwACtXHaBpB6SodelUpuMwQ')
        except Exception as e:
            print(f"Ошибка удаления сообщения: {e}")
    else:
        await message.reply(f"<b>⚠️ К сожалению, я не смог распознать Вашу команду.</b>", parse_mode='HTML', reply_markup=kb.keyboard)
        

@dp.callback_query_handler(lambda c: c.data == 'delete_info_message')
async def delete_info_message(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    await bot.delete_message(chat_id, message_id=message_id)    


@dp.callback_query_handler(lambda c: c.data == 'delete_admin_menu')
async def delete_admin_menu(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    await bot.delete_message(chat_id, message_id=message_id) 


@dp.callback_query_handler(lambda c: c.data == 'mailing')
async def mailing_text(callback_query: types.CallbackQuery, state: FSMContext):
    msg = await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                      message_id=callback_query.message.message_id,
                                      text="<i>Введите текст для рассылки или отправьте изображение</i>",
                                      parse_mode="HTML")
    await state.set_state(MailingState.waiting_for_content)
    await state.update_data(message_id=msg.message_id)

@dp.message_handler(state=MailingState.waiting_for_content, content_types=['text', 'photo'])
async def process_content_input(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    db = await open_db()

    if db[str(user_id)]["is_admin"]:
        users = list(db.keys())

        await message.answer("Начинаю рассылку...")

        for i in users:
            try:
                await message.copy_to(i)
            except ChatNotFound:
                pass

        await message.answer('Рассылка закончена.')
    else:
        await message.answer('У вас нет прав.')

    await state.finish()

    
@dp.callback_query_handler(lambda c: c.data.startswith('subscribe_'))
async def subscribe_handler(callback_query: types.CallbackQuery):
    _, tarif_name, tarif_id = callback_query.data.split('_')

    db = await open_db_tarif()

    tarif = db['tarifs'][f'{tarif_name.capitalize()}']
    tarif_price = tarif['price']
    tarif_emoji = tarif['emoji']

    text = f"<b>💰Выбранный тариф: {tarif_emoji}{tarif_name}</b>\n" \
           f"💸К оплате: {tarif_price}\n" \
           f"Спасибо!❤️"

    pay_info = await crystalPay.create_payment(tarif_price)
    pay_id = pay_info.id

    payment_button = InlineKeyboardButton("💸 Оплатить", url=pay_info.url)
    check_payment_button = InlineKeyboardButton("Проверить оплату", callback_data=f'check_payment_{pay_id}_{tarif_name}')

    menu = InlineKeyboardMarkup().row(payment_button).row(check_payment_button)

    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text=text,
                                parse_mode="HTML", reply_markup=menu)

@dp.callback_query_handler(lambda c: c.data.startswith('check_payment'))
async def check_payment_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    pay_id_with_prefix = callback_query.data.split("_")

    tarif_name = pay_id_with_prefix[4]
    pay_id = f'{pay_id_with_prefix[2]}_{pay_id_with_prefix[3]}'

    info_crystal_pay = await crystalPay.get_payment_info(pay_id)

    if info_crystal_pay.state == 'notpayed':
        await bot.answer_callback_query(callback_query.id, text="Не оплачено")
    elif info_crystal_pay.state == 'payed':
        db = await open_db()

        db[str(user_id)]['subscribe'] = tarif_name.capitalize()

        await save_db(db)
        await bot.answer_callback_query(callback_query.id, text="Тариф выдан")
