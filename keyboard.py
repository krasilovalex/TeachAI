import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_test_keyboard(options):
    keyboard = telebot.types.InlineKeyboardMarkup()
    for i, option in enumerate(options):
        callback_data = f"opt_{i}"
        button = telebot.types.InlineKeyboardButton(text=option, callback_data=callback_data)
        keyboard.add(button)
    return keyboard