# 🎬 MovieBot - Your Telegram Movie Assistant  

A **Telegram bot** that helps you **manage your movie lists** in a simple and efficient way.  


https://github.com/user-attachments/assets/bda462fd-f26b-43c2-856d-95ce69d539a8


## Description 📃  

MovieBot allows users to **add, view, and remove movies** from three customizable lists:  
✅ **To Watch**  
📅 **Watched**  
⭐ **Favorites**  

The bot interacts with **The Movie Database (TMDb) API**, providing **real-time movie details**, including release dates, descriptions, and ratings.  

## Features ✨  

- 🔍 **Search Movies** → Find movies by title and get detailed information.  
- 📋 **Movie List Management** → Add, view, and remove movies from custom lists.  
- 🍿 **Upcoming Movies** → Stay updated on the latest releases.  
- 💛 **Most Popular Movies** → Discover the top-rated movies of the last six months.  
- ⚙️ **User Settings** → Customize language and region preferences for better search results.  

## API Setup 🔑  

To use this bot, you need to set up the following API keys:  

- **The Movie Database (TMDb) API** → Register on [TMDb](https://www.themoviedb.org/) and generate an API Key 🔑.  
- **Telegram Bot API** → Create a bot with [BotFather](https://t.me/BotFather) using the `/newbot` command and copy the API Token 🔑.  

## 🔧 Installation  
📂 **Clone the repository**:  
   ```bash
   git clone https://github.com/your-username/MovieBot.git
   ```

## Libraries to Import 📚  

Before running the bot, make sure to install the required libraries:  

```bash
pip install python-telegram-bot==13.15
pip install urllib3==1.26.15
