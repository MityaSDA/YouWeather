import telebot
import requests
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import os
import threading
import time
import pytz
from datetime import timezone

# === 🔑 Ключи ===
TELEGRAM_TOKEN = "your_token_boat_is_BotFather"
WEATHER_API_KEY = "your_API_key_с_weatherapi.com"
bot = telebot.TeleBot(TELEGRAM_TOKEN)
DATA_FILE = "users.json"

# === Темы с оформлением виджетов ===
THEMES = {
    "light": {
        "sun": "☀️", "cloud": "🌤", "rain": "🌧", "snow": "❄️", "night": "🌙",
        "header": "🟦", "body": "⬜", "accent": "🟨"
    },
    "dark": {
        "sun": "🌞", "cloud": "☁️", "rain": "🌧💦", "snow": "🌨", "night": "🌑",
        "header": "⬛", "body": "⬛", "accent": "🟧"
    },
}

# === Работа с JSON ===
def load_user_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_user_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_prefs, f, ensure_ascii=False, indent=2)

user_prefs = load_user_data()

# === Определение города и часового пояса по IP ===
def get_location_by_ip():
    try:
        res = requests.get("https://ipinfo.io/json", timeout=5)
        data = res.json()
        return data.get("city", "Москва"), data.get("timezone", "Europe/Moscow")
    except:
        return "Москва", "Europe/Moscow"

# === Получение погоды ===
def get_weather(city):
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&lang=ru"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка получения погоды: {e}")
        return {"error": "API error"}

def get_forecast(city):
    try:
        url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city}&days=3&lang=ru"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка получения прогноза: {e}")
        return {"error": "API error"}

# === Главное меню с кнопками ===
def main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🌦 Погода сейчас", callback_data="now"),
        InlineKeyboardButton("📅 Прогноз на 3 дня", callback_data="forecast"),
    )
    kb.add(
        InlineKeyboardButton("📆 Прогноз на завтра", callback_data="tomorrow"),
        InlineKeyboardButton("🎨 Сменить тему", callback_data="theme"),
    )
    kb.add(
        InlineKeyboardButton("🏙 Изменить город", callback_data="change_city"),
        InlineKeyboardButton("⏰ Настроить время утренней рассылки", callback_data="set_time"),
    )
    kb.add(
        InlineKeyboardButton("🔄 Обновить прогноз", callback_data="refresh_now")
    )
    return kb

# === Обработчики ===
@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.chat.id)
    if user_id not in user_prefs:
        city, tz = get_location_by_ip()
        user_prefs[user_id] = {
            "city": city,
            "theme": "light",
            "timezone": tz,
            "morning_time": "08:00"
        }
        save_user_data()

    bot.send_message(
        user_id,
        f"👋 Привет! Я погодный бот 🌤\n"
        f"Я могу присылать прогноз каждый день и обновления каждые 3 часа.\n\n"
        f"Твой город: <b>{user_prefs[user_id]['city']}</b>\n"
        f"Время утренней рассылки: <b>{user_prefs[user_id]['morning_time']}</b>",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = str(call.message.chat.id)
    if user_id not in user_prefs:
        bot.answer_callback_query(call.id, "Сначала запустите бота командой /start")
        return
        
    prefs = user_prefs.get(user_id, {"city": "Москва", "theme": "light", "timezone": "Europe/Moscow", "morning_time": "08:00"})
    city = prefs["city"]
    theme = prefs["theme"]

    if call.data == "now":
        data = get_weather(city)
        send_weather_now(call.message, data, theme)
    elif call.data == "forecast":
        data = get_forecast(city)
        send_forecast(call.message, data, theme)
    elif call.data == "tomorrow":
        data = get_forecast(city)
        send_tomorrow_forecast(call.message, data, theme)
    elif call.data == "change_city":
        bot.send_message(user_id, "🏙 Напиши новый город:")
        bot.register_next_step_handler(call.message, change_city)
    elif call.data == "theme":
        new_theme = "dark" if theme == "light" else "light"
        prefs["theme"] = new_theme
        user_prefs[user_id] = prefs
        save_user_data()
        bot.send_message(
            user_id,
            f"🎨 Тема изменена на {'🌙 тёмную' if new_theme == 'dark' else '☀️ светлую'}",
            reply_markup=main_menu(),
        )
    elif call.data == "set_time":
        bot.send_message(user_id, "⏰ Введи время утренней рассылки в формате ЧЧ:ММ (например 07:30):")
        bot.register_next_step_handler(call.message, set_morning_time)
    elif call.data == "refresh_now":
        data = get_weather(city)
        send_weather_now(call.message, data, theme)

# === Функции настройки и изменения города ===
def set_morning_time(message):
    user_id = str(message.chat.id)
    time_text = message.text.strip()
    try:
        datetime.strptime(time_text, "%H:%M")
        user_prefs[user_id]["morning_time"] = time_text
        save_user_data()
        bot.send_message(user_id, f"✅ Время утренней рассылки установлено на {time_text}", reply_markup=main_menu())
    except ValueError:
        bot.send_message(user_id, "❌ Неверный формат времени. Используй ЧЧ:ММ (например 08:00)")
        bot.register_next_step_handler(message, set_morning_time)

def change_city(message):
    user_id = str(message.chat.id)
    city = message.text.strip()
    try:
        # Используем WeatherAPI для определения города и часового пояса
        weather_data = get_weather(city)
        if "error" in weather_data:
            bot.send_message(user_id, "❌ Город не найден. Попробуйте другой.")
            return
            
        tz = weather_data["location"]["tz_id"]
        user_prefs[user_id]["city"] = city
        user_prefs[user_id]["timezone"] = tz
        save_user_data()

        bot.send_message(
            user_id,
            f"✅ Город изменён на <b>{city}</b>",
            parse_mode="HTML",
            reply_markup=main_menu(),
        )
    except Exception as e:
        bot.send_message(user_id, "❌ Ошибка при смене города. Попробуйте позже.")

# === Функции отправки погоды с темой ===
def send_weather_now(message, data, theme):
    if "error" in data:
        bot.send_message(message.chat.id, "😕 Город не найден.")
        return

    loc = data["location"]["name"]
    temp = data["current"]["temp_c"]
    feels = data["current"]["feelslike_c"]
    cond = data["current"]["condition"]["text"]
    icon_url = "https:" + data["current"]["condition"]["icon"]
    hum = data["current"]["humidity"]
    wind = data["current"]["wind_kph"]
    time_msg = datetime.strptime(data["location"]["localtime"], "%Y-%m-%d %H:%M")
    emoji_theme = THEMES[theme]

    msg = (
        f"{emoji_theme['header']} <b>{loc}</b> {emoji_theme['header']}\n"
        f"🕒 {time_msg.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"{emoji_theme['body']}{emoji_theme['cloud']} <b>{cond}</b>\n"
        f"🌡 Температура: <b>{temp}°C</b> (ощущается как {feels}°C)\n"
        f"💨 Ветер: {wind} км/ч  💧 Влажность: {hum}%\n"
        f"{emoji_theme['accent']} Хорошего дня! {emoji_theme['accent']}"
    )

    bot.send_photo(message.chat.id, icon_url, caption=msg, parse_mode="HTML", reply_markup=main_menu())

def send_forecast(message, data, theme):
    if "error" in data:
        bot.send_message(message.chat.id, "❌ Ошибка при получении прогноза.")
        return

    city = data["location"]["name"]
    forecast_days = data["forecast"]["forecastday"]
    emoji_theme = THEMES[theme]

    msg = f"{emoji_theme['header']} <b>Прогноз на 3 дня для {city}</b> {emoji_theme['header']}\n\n"
    for day in forecast_days:
        date = datetime.strptime(day["date"], "%Y-%m-%d").strftime("%d.%m")
        condition = day["day"]["condition"]["text"]
        temp_min = day["day"]["mintemp_c"]
        temp_max = day["day"]["maxtemp_c"]
        msg += f"{emoji_theme['body']}{emoji_theme['cloud']} {date}: {condition}, {temp_min}°C → {temp_max}°C\n"

    bot.send_message(message.chat.id, msg, parse_mode="HTML", reply_markup=main_menu())

def send_tomorrow_forecast(message, data, theme):
    if "error" in data:
        bot.send_message(message.chat.id, "❌ Ошибка при получении прогноза.")
        return

    tomorrow = data["forecast"]["forecastday"][1]
    date = datetime.strptime(tomorrow["date"], "%Y-%m-%d").strftime("%d.%m.%Y")
    condition = tomorrow["day"]["condition"]["text"]
    temp_min = tomorrow["day"]["mintemp_c"]
    temp_max = tomorrow["day"]["maxtemp_c"]
    icon = "https:" + tomorrow["day"]["condition"]["icon"]
    emoji_theme = THEMES[theme]

    msg = (
        f"{emoji_theme['header']} <b>Прогноз на завтра ({date})</b> {emoji_theme['header']}\n"
        f"{emoji_theme['body']}{emoji_theme['cloud']} {condition}\n"
        f"🌡 Мин: {temp_min}°C → Макс: {temp_max}°C\n"
        f"{emoji_theme['accent']} Будь готов к погоде! {emoji_theme['accent']}"
    )

    bot.send_photo(message.chat.id, icon, caption=msg, parse_mode="HTML", reply_markup=main_menu())

# === Функции для планировщика ===
def send_morning_forecast(user_id, prefs):
    city = prefs.get("city", "Москва")
    theme = prefs.get("theme", "light")
    data = get_forecast(city)
    
    if data.get("error") is None:
        day = data["forecast"]["forecastday"][0]["day"]
        condition = day["condition"]["text"]
        min_t = day["mintemp_c"]
        max_t = day["maxtemp_c"]
        icon = "https:" + day["condition"]["icon"]
        msg = (
            f"🌅 Доброе утро!\nСегодня в <b>{city}</b>:\n"
            f"{THEMES[theme]['cloud']} {condition}\n"
            f"🌡 {min_t}°C → {max_t}°C\nХорошего дня ☕"
        )
        try:
            bot.send_photo(user_id, icon, caption=msg, parse_mode="HTML")
        except:
            bot.send_message(user_id, msg, parse_mode="HTML")

def send_auto_update(user_id, prefs):
    city = prefs.get("city", "Москва")
    theme = prefs.get("theme", "light")
    data = get_weather(city)
    
    if data.get("error") is None:
        loc = data["location"]["name"]
        temp = data["current"]["temp_c"]
        feels = data["current"]["feelslike_c"]
        cond = data["current"]["condition"]["text"]
        icon = "https:" + data["current"]["condition"]["icon"]
        msg = (
            f"🔄 Обновление погоды для <b>{loc}</b>:\n"
            f"{THEMES[theme]['cloud']} {cond}\n"
            f"🌡 {temp}°C, ощущается как {feels}°C"
        )
        try:
            bot.send_photo(user_id, icon, caption=msg, parse_mode="HTML")
        except:
            bot.send_message(user_id, msg, parse_mode="HTML")

# === Планировщик с индивидуальным временем ===
def scheduled_updates():
    while True:
        now_utc = datetime.now(timezone.utc)
        processed_users = set()  # Чтобы избежать дублирования
        
        for user_id, prefs in user_prefs.items():
            if user_id in processed_users:
                continue
                
            try:
                tz_str = prefs.get("timezone", "Europe/Moscow")
                tz = pytz.timezone(tz_str)
                now_local = now_utc.astimezone(tz)

                # Утренняя рассылка
                morning_time = prefs.get("morning_time", "08:00")
                hour, minute = map(int, morning_time.split(":"))
                
                if now_local.hour == hour and now_local.minute == minute:
                    send_morning_forecast(user_id, prefs)
                    processed_users.add(user_id)

                # Авто-обновление каждые 3 часа (только в определенное время)
                elif now_local.minute == 0 and now_local.hour % 3 == 0:
                    send_auto_update(user_id, prefs)
                    processed_users.add(user_id)
                    
            except Exception as e:
                print(f"Ошибка для пользователя {user_id}: {e}")
                
        time.sleep(60)

if __name__ == "__main__":
    # Запускаем планировщик в отдельном потоке
    threading.Thread(target=scheduled_updates, daemon=True).start()
    
    # Запускаем бота
    print("Бот запущен...")

    bot.infinity_polling()
