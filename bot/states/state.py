from aiogram.dispatcher.filters.state import StatesGroup, State

class SomeState(StatesGroup):
    waiting_for_proxy = State()
    waiting_to_revoke = State()
    waiting_for_personal_message_text = State()
    waiting_for_personal_message_id = State()
    waiting_for_user_id = State()

class MailingState(StatesGroup):
    waiting_for_content = State()