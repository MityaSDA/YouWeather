Project: # YouWeather
introduction about the project:The weather forecast chatbot. Individual time for the morning newsletter. Auto-refresh every 3 hours. Buttons: Current weather, Forecast for 3 days, Forecast for tomorrow, Change theme, Change City, Time setting, Update forecast.	Dark and light theme with mini widgets (emojis, design). Beautiful cards with weather icons.  
Register for https://openweathermap.org/api
And get API-ключ.
Create a Telegram bot via @BotFather and → receive a Telegram Token.
Installation instructions: Install Python. Install VS Code. Install the Python extension (by Microsoft). Create a project (folder/path) for example: C:\Users\<твоё_имя>\Documents\weather_bot. Place the file in this folder bot3.py . Install VS libraries via the VS terminal: pip install pyTelegramBotAPI requests.  
To insert the bot code: Copy the entire code and paste your keys there (in a file bot3.py ): TELEGRAM_TOKEN = "your_token_boat_is_BotFather" WEATHER_API_KEY = "твой_API_ключ_с_weatherapi.com " and Save the file (Ctrl +S)
Launch the bot In VS Code: open the terminal, enter: python bot3.py
If everything is OK, the terminal will display: Polling started... (or just nothing — this is normal)
Now open Telegram, find your bot (by the name given by BotFather), and write to it: /start, Then the name of the city, and the bot should answer you with a beautiful weather forecast.
