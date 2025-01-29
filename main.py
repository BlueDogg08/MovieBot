import requests
from datetime import datetime, timedelta
import json
import sys
from functools import partial

from telebot import TeleBot

from os.path import basename
from telegram import *
from telegram.ext import *
from requests import *

import sqlite3


# Imposta la codifica dell'output su UTF-8
sys.stdout.reconfigure(encoding='utf-8')


TelegramTOKEN = "YOUR_TELEGRAM_API_TOKEN"

TMDB_TOKEN = "YOUR_TMDB_API"


# Funzione iniziale per accogliere l'utente o aggiungerlo al database se non esiste
def start(update: Update, context: CallbackContext):

    if not user_exists(update, context):
        try:
            create_user(update, context)

        except Exception as e:
            print("problemi nella creazione di un utente... ", e)

    try:
        inline_keyboard = [[InlineKeyboardButton("👉  Clicca qui per iniziare  👈", callback_data='home_page')]]

        caption = f"Benveuto in MovieBot <a href='tg://user?id={update.effective_user.id}'>@{update.effective_user.first_name}</a>!\nTi mostrerò informazioni riguardo tutti i film che cercherai, incluse le ultime uscite in sala.\nHo un database aggiornato che consente di salvare film nella lista <i><b>da guardare 👀</b></i>, in quella dei <i><b>guardati 📅</b></i> e in quella dei <i><b>preferiti ⭐</b></i>"
        context.bot.send_message(chat_id=update.effective_chat.id, text=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard))
        context.user_data['current_message_id'] = None

    except Exception as e:
        print("problemi nella ricerca di un utente creato... ", e)
        context.bot.send_message(chat_id=update.effective_chat.id, text=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard))


# Mostra la home page con le statistiche personali e le opzioni principali
def home_page(update: Update, context: CallbackContext):
    try:
        delete_last_message(update, context)

        n_fav_movies = num_fav_movies(update, context)
        n_seen_movies = num_seen_movies(update, context)
        n_to_see_movies = num_to_see_movies(update, context)

        inline_keyboard = [[InlineKeyboardButton("Cerca  🔎", callback_data='help_search'), InlineKeyboardButton("Preferiti  ⭐", callback_data='fav_movies')],
            [InlineKeyboardButton("Cronologia  📅", callback_data='seen_movies'), InlineKeyboardButton("Da guardare  👀", callback_data='tosee_movies')],
            [InlineKeyboardButton("Impostazioni  ⚙", callback_data='settings'), InlineKeyboardButton("In uscita  🍿", callback_data='upcoming_movies_search')],
            [InlineKeyboardButton("I più amati degli ultimi 6 mesi 💛", callback_data='latest_top_rated_movies')]
        ]

        caption = f"<a href='tg://user?id={update.effective_user.id}'>@{update.effective_user.first_name}</a>\n\nFilm preferiti: {n_fav_movies}\nFilm guardati: {n_seen_movies}\nFilm da guardare: {n_to_see_movies}"
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard))
        context.user_data['current_message_id'] = message.message_id

    except Exception as e:
        print("problemi nella visualizzazione dell'home page... ", e)


# Mostra il menu delle impostazioni per modificare le preferenze dell'utente
def settings(update: Update, context: CallbackContext):

    try:
        delete_last_message(update, context)

        inline_keyboard = [[InlineKeyboardButton("Film guardati  📅", callback_data='edit_seen_movies'), InlineKeyboardButton("Film preferiti  ⭐️", callback_data='edit_fav_movies')],
            [InlineKeyboardButton("Film da guardare  👀", callback_data='edit_tosee_movies'), InlineKeyboardButton("Lingua e paese  🇮🇹", callback_data='change_lang_region')],
            [InlineKeyboardButton("Elimina utente  🚫👤", callback_data='ask_delete_user')],
            [InlineKeyboardButton("⬅️  Indietro", callback_data=f"home_page")]
        ]

        caption = f"Impostazioni utente\n\nModifica le seguenti informazioni:"
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard))
        context.user_data['current_message_id'] = message.message_id

    except Exception as e:
        print("problemi nell'accesso all'area impostazioni... ", e)


# Elimina l'ultimo messaggio inviato dal bot e, se esiste, anche quello dell'utente
def delete_last_message(update: Update, context: CallbackContext):

    try:
        # Elimina il messaggio precedente del bot
        if context.user_data.get('current_message_id'):
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['current_message_id'])

            context.user_data['current_message_id'] = None

        #elimina il mesasggio dell'utente se presente
        if update.message:
            update.message.delete()

    except Exception as e:
        print("Errore nell'eliminazione del messaggio precedente: ", str(e))


# Verifica l'esistenza dell'utente nel database
def user_exists(update: Update, context: CallbackContext):
    
    try:
        user_id = update.effective_user.id

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM User WHERE user_id = ?", (user_id,))
        
        result = cursor.fetchone()
        conn.close()

        return result
    except Exception as e:
        print("problemi nella ricerca dell'utente... ", e)


# Crea un nuovo utente nel database
def create_user(update: Update, context: CallbackContext):
    
    try:
        user_id = update.effective_user.id

        try:
            user_name = update.effective_user.first_name + " " + update.effective_user.last_name
        except:
            user_name = update.effective_user.first_name

        lang= "it"   #italiano default
        region = "IT"   #italia default

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()

        cursor.execute("INSERT INTO User (user_id, name, lang, region) VALUES (?, ?, ?, ?)",
                    (user_id, user_name, lang, region))

        conn.commit()
        conn.close()

    except Exception as e:
        print("problemi nella creazione dell'utente... ", e)


# Richiede conferma per eliminare l'account utente e i relativi dati
def ask_delete_user(update: Update, context: CallbackContext):

    try:
        delete_last_message(update, context)

        inline_keyboard = [
            [InlineKeyboardButton("❌  Annulla", callback_data="settings"), InlineKeyboardButton("✅  Sì, elimina", callback_data="delete_user")],
        ]

        caption = "Vuoi davvero procedere con l'eliminazione dell'utente?\n\n<i>(Perderai tutti i tuoi dati, compresi i film preferiti, da guardare e già guardati)</i>"
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard))
        context.user_data['current_message_id'] = message.message_id

    except Exception as e:
        print("Errore nella richiesta di conferma sull'eliminazione dell'utente: ", str(e))


# Elimina l'account utente e i relativi dati dal database
def delete_user(update: Update, context: CallbackContext):

    try:
        delete_last_message(update, context)

        user_id = update.effective_user.id

        conn = sqlite3.connect("MovieDataBase.db")
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute("DELETE FROM User WHERE user_id = ?", (user_id,))

        conn.commit()
        conn.close()

        inline_keyboard = [
            [InlineKeyboardButton("⬅️  Indietro", callback_data="start")]
        ]


        caption = "Utente eliminato con successo  ✅"
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard))
        context.user_data['current_message_id'] = message.message_id

    except Exception as e:

        inline_keyboard = [
            [InlineKeyboardButton("⬅️  Indietro", callback_data="home_page")]
        ]

        caption = "Utente non eliminato...  ❌"
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard))
        context.user_data['current_message_id'] = message.message_id

        print("problemi nell'eliminazione dell'utente... ", e)


# Recupera la lingua dell'utente dal database
def get_user_language(update: Update, context: CallbackContext):
    try:
        user_id = update.effective_user.id

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()

        cursor.execute("SELECT lang FROM User WHERE user_id = ?", (user_id,))
        
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
        else:
            return False
        
    except Exception as e:
        print("problemi nell'ottenimento della lingua dell'utente... ", e)


# Recupera la regione dell'utente dal database
def get_user_region(update: Update, context: CallbackContext):
    try:
        user_id = update.effective_user.id

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()

        cursor.execute("SELECT region FROM User WHERE user_id = ?", (user_id,))
        
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
        else:
            return False
    
    except Exception as e:
        print("problemi nell'ottenimento della regione dell'utente... ", e)


# Mostra il menu per cambiare lingua o regione dell'utente
def change_lang_region(update: Update, context: CallbackContext):

    try:
        delete_last_message(update, context)

        inline_keyboard = [
            [InlineKeyboardButton("🇮🇹  Cambia lingua", callback_data="change_lang_setting"), InlineKeyboardButton("🌎  Cambia regione", callback_data="change_region_setting")],
            [InlineKeyboardButton("⬅️  Indietro", callback_data="settings")]]


        caption = "Scegli quale impostazione cambiare:"
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard))
        context.user_data['current_message_id'] = message.message_id
    
    except Exception as e:
        print("problemi nell'entrata in change_lang_region()... ", e)


# Guida l'utente a cercare un film tramite un messaggio di testo
def help_search(update: Update, context: CallbackContext):

    try:
        delete_last_message(update, context)

        inline_keyboard = [[InlineKeyboardButton("⬅️  Indietro", callback_data="home_page")]]

        caption = "Scrivi in chat il film che stai cercando..."
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard))
        context.user_data['current_message_id'] = message.message_id

    except Exception as e:
        print("Problemi nell'invio di help_search()... ", e)


# Mostra il menu per modificare la lingua
def change_lang_setting(update: Update, context: CallbackContext):

    try:
        delete_last_message(update, context)
        
        lang = get_user_language(update, context)

        inline_keyboard = [
            [InlineKeyboardButton(f"🇬🇧  English{'  ✅' if lang == 'en' else ''}", callback_data="change_lang_en"), InlineKeyboardButton(f"🇺🇦  Український{'  ✅' if lang == 'uk' else ''}", callback_data="change_lang_uk")],
            [InlineKeyboardButton(f"🇬🇷  ελληνικά{'  ✅' if lang == 'el' else ''}", callback_data="change_lang_el"), InlineKeyboardButton(f"🇮🇹  Italiano{'  ✅' if lang == 'it' else ''}", callback_data="change_lang_it")],
            [InlineKeyboardButton(f"🇯🇵  日本語{'  ✅' if lang == 'ja' else ''}", callback_data="change_lang_ja"), InlineKeyboardButton(f"🇪🇸  Español{'  ✅' if lang == 'es' else ''}", callback_data="change_lang_es")],
            [InlineKeyboardButton(f"🇮🇳  हिन्दी{'  ✅' if lang == 'hi' else ''}", callback_data="change_lang_hi"), InlineKeyboardButton(f"🇫🇷  Français{'  ✅' if lang == 'fr' else ''}", callback_data="change_lang_fr")],
            [InlineKeyboardButton("⬅️  Indietro", callback_data="change_lang_region")]]


        caption = "Seleziona la tua lingua:"
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard))
        context.user_data['current_message_id'] = message.message_id

    except Exception as e:
        print("problemi in change_lang()... ", e)


# Mostra il menu per modificare la regione
def change_region_setting(update: Update, context: CallbackContext):

    try:
        delete_last_message(update, context)

        region = get_user_region(update, context)

        inline_keyboard = [
            [InlineKeyboardButton(f"🇮🇹  Italy{'  ✅' if region == 'IT' else ''}", callback_data="change_region_IT"), InlineKeyboardButton(f"🇺🇸  United States of America{'  ✅' if region == 'US' else ''}", callback_data="change_region_US")],
            [InlineKeyboardButton(f"🇧🇷  Brazil{'  ✅' if region == 'BR' else ''}", callback_data="change_region_BR"), InlineKeyboardButton(f"🇩🇴  Dominican Republic{'  ✅' if region == 'DO' else ''}", callback_data="change_region_DO")],
            [InlineKeyboardButton(f"🇪🇬  Egitto{'  ✅' if region == 'EG' else ''}", callback_data="change_region_EG"), InlineKeyboardButton(f"🇭🇰  Hong Kong{'  ✅' if region == 'HK' else ''}", callback_data="change_region_HK")],
            [InlineKeyboardButton("⬅️  Indietro", callback_data="change_lang_region")]]


        caption = "Seleziona la tua regione:"
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard))
        context.user_data['current_message_id'] = message.message_id

    except Exception as e:
        print("problemi in change_region()... ", e)


# Aggiorna la lingua dell'utente nel database
def change_lang_db(update: Update, context: CallbackContext):
    try:

        lang = update.callback_query.data.split('_')[-1]
        user_id = update.effective_user.id

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()

        cursor.execute("UPDATE User SET lang = ? WHERE user_id = ?", (lang, user_id))

        conn.commit()
        conn.close()

        change_lang_setting(update, context)
    
    except Exception as e:
        print("problemi nel cambiamento della lingua nel DB... ", e)


# Aggiorna la regione dell'utente nel database
def change_region_db(update: Update, context: CallbackContext):
    try:

        region = update.callback_query.data.split('_')[-1]
        user_id = update.effective_user.id

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()

        cursor.execute("UPDATE User SET region = ? WHERE user_id = ?", (region, user_id))

        conn.commit()
        conn.close()

        change_region_setting(update, context)
    
    except Exception as e:
        print("problemi nel cambiamento della regione nel DB... ", e)


# Verifica se il film è già presente nella lista dei film "preferiti" dell'utente
def is_fav_movie(update: Update, context: CallbackContext, movie_id):
    try:
        user_id = update.effective_user.id

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Fav_movie WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))

        result = cursor.fetchone()
        conn.close()

        # Se il risultato è None, il film non è presente nei preferiti
        return result

    except Exception as e:
        print("Errore nella verifica del film preferito: ", e)
        return False
    

# Verifica se il film è già presente nella lista dei film "visti" dall'utente
def is_seen_movie(update: Update, context: CallbackContext, movie_id):
    try:
        user_id = update.effective_user.id

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Seen_movie WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))
        
        result = cursor.fetchone()
        conn.close()

        return result

    except Exception as e:
        print("Errore nella verifica del film visto: ", e)
        return False
    

# Verifica se il film è già presente nella lista dei film "da vedere" dell'utente
def is_to_see_movie(update: Update, context: CallbackContext, movie_id):
    try:
        user_id = update.effective_user.id

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM To_see_movie WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))
        
        result = cursor.fetchone()
        conn.close()

        return result

    except Exception as e:
        print("Errore nella verifica del film da guardare: ", e)
        return False


# Ritorna il numero di film "preferiti" dell'utente
def num_fav_movies(update: Update, context: CallbackContext):

    try:
        user_id = update.effective_user.id

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Fav_movie WHERE user_id = ?", (user_id,))

        num_fav_movies = cursor.fetchone()[0]
        conn.close()

        return num_fav_movies
    
    except Exception as e:
        print("problemi nella ricerca del numero di film preferiti... ", e)


# Ritorna il numero di film "visti" dall'utente
def num_seen_movies(update: Update, context: CallbackContext):

    try:
        user_id = update.effective_user.id

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Seen_movie WHERE user_id = ?", (user_id,))
        
        num_seen_movies = cursor.fetchone()[0]
        conn.close()

        return num_seen_movies
    
    except Exception as e:
        print("problemi nella ricerca del numero di film guardati... ", e)


# Ritorna il numero di film "da vedere" dell'utente
def num_to_see_movies(update: Update, context: CallbackContext):

    try:
        user_id = update.effective_user.id

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM To_see_movie WHERE user_id = ?", (user_id,))
        
        num_to_see_movies = cursor.fetchone()[0]
        conn.close()

        return num_to_see_movies
    
    except Exception as e:
        print("problemi nella ricerca del numero di film da guardare... ", e)


# Aggiunge un film al database in base all'azione specificata (visto, preferito, da guardare)
# Verifica la presenza del film nella lista corrispondente e lo aggiunge se non presente
def add_movies_db(update: Update, context: CallbackContext):

    try:
        query = update.callback_query
        user_id = update.effective_user.id

        action, movie_id, movie_name = query.data.split('_')[1:]

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()
        
        if action == "seen":
            result = is_seen_movie(update, context, movie_id)
            if result is False:            # la verifica ha risultato un errore
                query_text = "Errore nella verifica del film visto..."
            elif result is not None:       # il film è già presente nella lista dei guardati
                query_text = "E' già presente nella lista dei film guardati..."
            else:                          # se restituisce None allora il film non è presente nella lista e lo aggiunge
                query_text = "Aggiunto con successo ai film guardati!"
                cursor.execute("INSERT INTO Seen_movie (user_id, movie_id, movie_name) VALUES (?, ?, ?)",
                    (user_id, movie_id, movie_name))
                        
        elif action == "fav":
            result = is_fav_movie(update, context, movie_id)
            if result is False:            # la verifica ha risultato un errore
                query_text = "Errore nella verifica del film preferito..."
            elif result is not None:       # il film è già presente nella lista dei preferiti
                query_text = "E' già presente nella lista dei film preferiti..."
            else:                          # se restituisce None allora il film non è presente nella lista e lo aggiunge
                query_text = "Aggiunto con successo ai film preferiti!"
                cursor.execute("INSERT INTO Fav_movie (user_id, movie_id, movie_name) VALUES (?, ?, ?)",
                    (user_id, movie_id, movie_name))
            
        elif action == "tosee":
            result = is_to_see_movie(update, context, movie_id)
            if result is False:            # la verifica ha risultato un errore
                query_text = "Errore nella verifica del film da guardare..."
            elif result is not None:       # il film è già presente nella lista dei film da guardare
                query_text = "E' già presente nella lista dei film da guardare..."
            else:                          # se restituisce None allora il film non è presente nella lista e lo aggiunge
                query_text = "Aggiunto con successo ai film da guardare!"
                cursor.execute("INSERT INTO To_see_movie (user_id, movie_id, movie_name) VALUES (?, ?, ?)",
                    (user_id, movie_id, movie_name))
            
        conn.commit()
        conn.close()

        query.answer(query_text) # Mostra il messaggio di conferma su schermo

        send_list_of_movies(update, context)

    except Exception as e:
        print("Errore nell'aggiunta di film in fav/seen/to_see: ", str(e))


# Rimuove un film dal database in base all'azione specificata (visto, preferito, da guardare)
# Controlla se il film è nella lista corrispondente e lo rimuove se presente
def rem_movies_db(update: Update, context: CallbackContext):

    try:
        query = update.callback_query
        user_id = update.effective_user.id

        data = query.data.split('_')
        action, movie_id, movie_name = data[1:4]
        is_settings = len(data) > 4 and data[4] == "settings"  # se data[4] è 'settings' allora si sta modificando dalle impostazioni

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()
        
        if action == "seen":
            result = is_seen_movie(update, context, movie_id)
            if result is False:            # la verifica ha risultato un errore
                query_text = "Errore nella verifica del film visto..."
            elif result is None:           # se restituisce None allora il film non è presente nella lista
                query_text = "Non è presente nella lista dei film guardati..."
            else:                          # il film è già presente nella lista dei guardati e lo rimuove
                query_text = "Rimosso con successo ai film guardati!"
                cursor.execute("DELETE FROM Seen_movie WHERE user_id = ? AND movie_id = ?",
                    (user_id, movie_id))
                        
        elif action == "fav":
            result = is_fav_movie(update, context, movie_id)
            if result is False:            # la verifica ha risultato un errore
                query_text = "Errore nella verifica del film preferito..."
            elif result is None:           # se restituisce None allora il film non è presente nella lista
                query_text = "Non è presente nella lista dei film preferiti..."
            else:                          # il film è già presente nella lista dei preferiti e lo rimuove
                query_text = "Rimosso con successo ai film preferiti!"
                cursor.execute("DELETE FROM Fav_movie WHERE user_id = ? AND movie_id = ?",
                    (user_id, movie_id))  
            
        elif action == "tosee":
            result = is_to_see_movie(update, context, movie_id)
            if result is False:            # la verifica ha risultato un errore
                query_text = "Errore nella verifica del film da guardare..."
            elif result is None:           # se restituisce None allora il film non è presente nella lista e lo aggiunge
                query_text = "Non è presente nella lista dei film da guardare..."
            else:                          # il film è già presente nella lista dei film da guardare e lo rimuove
                query_text = "Rimosso con successo ai film da guardare!"
                cursor.execute("DELETE FROM To_see_movie WHERE user_id = ? AND movie_id = ?",
                    (user_id, movie_id))
                

        conn.commit()
        conn.close()

        if is_settings:

            delete_last_message(update, context)

            inline_keyboard = [
                [InlineKeyboardButton("⬅️  Indietro", callback_data=f"edit_{action}_movies")]
            ]

            caption = f"Film rimosso con successo  ✅  <b>({movie_name}</b>)"
            message = context.bot.send_message(chat_id=update.effective_chat.id, text=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard))
            context.user_data['current_message_id'] = message.message_id

        else:
            query.answer(query_text) # Mostra il messaggio di conferma su schermo
            send_list_of_movies(update, context)

    except Exception as e:
        print("Errore nella rimozione di film in fav/seen/to_see: ", str(e))


# Visualizza la lista dei film (visti, preferiti o da guardare) di un utente
# Supporta sia la modalità di visualizzazione che la modifica (rimozione)
def display_movies(update: Update, context: CallbackContext):
    try:
        delete_last_message(update, context)
        
        query = update.callback_query
        user_id = update.effective_user.id

        data = query.data.split('_')
        
        if data[0] == "edit":
            is_edit = True
            movie_type = data[1]
        
        else:   # il primo elemento è il tipo di film (seen, fav, tosee)
            is_edit = False
            movie_type = data[0]

        conn = sqlite3.connect("MovieDataBase.db")
        cursor = conn.cursor()

        # Query in base al tipo di film (preferito|da guardare|visto)
        if movie_type == "fav":
            table = "Fav_movie"
            list_title = "preferiti  ⭐"
            edit_caption = "Clicca il film che vuoi rimuovere da <b><i>preferiti  ⭐</i></b>:"
            view_caption = "Ecco la lista dei tuoi film <b><i>preferiti ⭐</i></b>:"
        elif movie_type == "tosee":
            table = "To_see_movie"
            list_title = "da guardare  👀"
            edit_caption = "Clicca il film che vuoi rimuovere da <b><i>da guardare  👀</i></b>:"
            view_caption = "Ecco la lista dei tuoi film <b><i>da guardare 👀</i></b>:"
        else:
            table = "Seen_movie"
            list_title = "guardati  📅"
            edit_caption = "Clicca il film che vuoi rimuovere dalla <b><i>cronologia  📅</i></b>"
            view_caption = "Ecco la lista dei film che <b><i>hai guardato 📅</i></b>:"

        cursor.execute(f"SELECT movie_id, movie_name FROM {table} WHERE user_id = ?", (user_id,))
        
        movies = cursor.fetchall()
        conn.close()

        inline_keyboard = []
        if movies:
            for movie in movies:
                if is_edit:
                    callback_action = f"rem_{movie_type}_{movie[0]}_{movie[1]}_settings"
                
                else:     # Usa il pattern "id_(seen|fav|tosee)_id_name" in modalità normale (non modifica)
                    
                    callback_action = f"id_{movie[0]}"
                
                row = [InlineKeyboardButton(movie[1], callback_data=callback_action)]
                inline_keyboard.append(row)

            inline_keyboard.append([InlineKeyboardButton("⬅️  Indietro", callback_data="settings" if is_edit else "home_page")])

            caption = edit_caption if is_edit else view_caption
        else:
            inline_keyboard.append([InlineKeyboardButton("⬅️  Indietro", callback_data="home_page")])
            caption = f"Nessun film è ancora nella lista  <b><i>{list_title}</i></b>"

        message = context.bot.send_message(chat_id=update.effective_chat.id, text=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard))
        context.user_data['current_message_id'] = message.message_id

    except Exception as e:
        print(f"Errore durante la visualizzazione dei film {movie_type}: {str(e)}")


# Cerca informazioni su un singolo film
def one_film_search(update: Update, context: CallbackContext):
    try:
        delete_last_message(update, context)

        query = update.callback_query
        data = query.data.split('_')
        id_film = data[1]

        lang = get_user_language(update, context)
        region = get_user_region(update, context)

        context.user_data['current_message_id'] = None

        url = f"https://api.themoviedb.org/3/movie/{id_film}?language={lang}-{region}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {TMDB_TOKEN}"
        }

        response = requests.get(url, headers=headers)
        data = response.json()

        if response.status_code == 200:

            context.user_data['movies_list'] = [data]
            context.user_data['current_movie_index'] = 0

            context.user_data['extended_movie_description'] = False

            send_list_of_movies(update, context)
        else:

            message = update.message.reply_text("Nessun film trovato")
            context.user_data['current_message_id'] = message.message_id

    except Exception as e:
        print("problemi nella ricerca del film... ", e)


# Cerca informazioni su più film in base all'input dell'utente (titolo o parola chiave)
# Ordina i risultati per popolarità
def more_film_search(update: Update, context: CallbackContext):

    try:
        delete_last_message(update, context)

        user_input = update.message.text.lower()

        lang = get_user_language(update, context)
        region = get_user_region(update, context)

        context.user_data['current_message_id'] = None

        url = f"https://api.themoviedb.org/3/search/movie?query={user_input}&include_adult=false&language={lang}-{region}&page=1"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {TMDB_TOKEN}"
        }

        response = requests.get(url, headers=headers)
        data = response.json()

        if data['results']:
            # Ordina i risultati in base a 'popularity' in ordine decrescente
            sorted_results = sorted(data['results'], key=lambda x: x['popularity'], reverse=True)

            context.user_data['movies_list'] = sorted_results
            context.user_data['current_movie_index'] = 0

            context.user_data['extended_movie_description'] = False
            

            send_list_of_movies(update, context)
        else:


            message = update.message.reply_text("Nessun film trovato")
            context.user_data['current_message_id'] = message.message_id

    except Exception as e:
        print("problemi nella ricerca dei film... ", e)


# Cerca i film in uscita nelle sale cinematografiche
# Ordina i risultati per popolarità
def upcoming_movies_search(update: Update, context: CallbackContext):
    try:

        delete_last_message(update, context)

        url = f"https://api.themoviedb.org/3/movie/upcoming?language=it-IT&page=1&region=IT"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {TMDB_TOKEN}"
        }

        response = requests.get(url, headers=headers)
        data = response.json()

        if response.status_code == 200:

            # Ordina i risultati in base a 'popularity' in ordine decrescente
            sorted_results = sorted(data['results'], key=lambda x: x['popularity'], reverse=True)

            context.user_data['movies_list'] = sorted_results
            context.user_data['current_movie_index'] = 0
            context.user_data['extended_movie_description'] = False
            
            send_list_of_movies(update, context)
        else:

            message = update.message.reply_text("Nessun film trovato")
            context.user_data['current_message_id'] = message.message_id

    except Exception as e:
        print("problemi nella ricerca dei film in uscita... ", e)


# Cercare i film con la valutazione più alta negli ultimi 6 mesi
# Filtra i risultati in base a valutazione media
def latest_top_rated_movies(update: Update, context: CallbackContext):
    try:
        delete_last_message(update, context)

        today = datetime.today()
        six_months_ago = today - timedelta(180) # 6 mesi fa
        
        today_str = today.strftime('%Y-%m-%d')
        six_months_ago_str = six_months_ago.strftime('%Y-%m-%d')

        lang = get_user_language(update, context)
        region = get_user_region(update, context)
        
        url = f"https://api.themoviedb.org/3/discover/movie?language={lang}-{region}&sort_by=vote_average.desc&vote_count.gte=50&primary_release_date.gte={six_months_ago_str}&primary_release_date.lte={today_str}&page=1"
        
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {TMDB_TOKEN}"
        }
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if response.status_code == 200:
            
            # Ordina i film per valutazione più alta
            movies = sorted(data['results'], key=lambda x: x['vote_average'], reverse=True)
        
            context.user_data['movies_list'] = movies
            context.user_data['current_movie_index'] = 0
            context.user_data['extended_movie_description'] = False
        
            send_list_of_movies(update, context)

        else:
            message = update.message.reply_text("Nessun film trovato")
            context.user_data['current_message_id'] = message.message_id

    except Exception as e:
        print("Problema nella ricerca dei film con la valutazione più alta degli ultimi 6 mesi ... ", e)


# Invia all'utente la lista di film passati nel context
# Supporta la visualizzazione di descrizioni dettagliate e immagini dei film
def send_list_of_movies(update: Update, context: CallbackContext):

    try:
        
        movie_list = context.user_data['movies_list']
        current_index = context.user_data['current_movie_index']
        max_index = len(movie_list) - 1

        current_movie = movie_list[current_index]

        if current_movie['backdrop_path']:
            image_url = f"https://image.tmdb.org/t/p/w500/"+current_movie['backdrop_path']
            headers = {
                        "accept": "application/json",
                        "Authorization": f"Bearer {TMDB_TOKEN}"
            }
            
            image_content = requests.get(image_url, headers=headers).content
        else:
            stock_image_path = "stock_photos/no_image.jpg"
            with open(stock_image_path, "rb") as stock_image:
                image_content = stock_image.read()

        #di base è false, cioè la descrizione sarà accorciata
        movie_desc_status = context.user_data['extended_movie_description']

        
        movie_name = current_movie['title']

        # Limita la lunghezza del nome per evitare problemi all'invio del messaggio
        if len(movie_name) > 30:
            movie_name = movie_name[:30-3] + "..."

        # Usa un valore predefinito se il nome è vuoto
        if not movie_name.strip():
            movie_name = "film sconoscito"

        if current_movie['release_date']:
            parsed_date = datetime.strptime(current_movie['release_date'], "%Y-%m-%d")

            movie_date = parsed_date.strftime("%d-%m-%Y") #formatted date
        else:
            movie_date = ""

        inline_keyboard = []

        # controlla se movie_desc_status è stata creata e se esiste la descrizione del film nel DB
        if movie_desc_status is not None:

            description = current_movie['overview']  #ottengo la descrizione del film

            if len(description) <= 200:  # la descrizione contiene al massimo 200 caratteri e rientra tranquillamente nel messaggio
                caption = f"<b>{movie_name}</b>\n\n{description}\n\n<i>{movie_date}</i>"
            else:
                if movie_desc_status == True: # se la descrizione è >200 ed è estesa
                    caption = f"<b>{movie_name}</b>\n\n{description}\n\n<i>{movie_date}</i>"
                    inline_keyboard.append([InlineKeyboardButton("Accorcia Descrizione  📝", callback_data='shorten_description')])
                elif movie_desc_status == False: # se la desrizione è >200 ed è accorciata
                    short_description = description[:200] 
                    inline_keyboard.append([InlineKeyboardButton("Estendi Descrizione  📝", callback_data='extend_description')])
                    
                    caption = f"<b>{movie_name}</b>\n\n{short_description}...\n\n<i>{movie_date}</i>"
                else:
                    return False

        else: # non esiste una descrizione
            caption = f"<b>{movie_name}</b>\n\n<i>{movie_date}</i>"

        movie_id = current_movie['id']

        
        if is_fav_movie(update, context, movie_id):
            fav_text = "❌⭐"
            fav_call_back = f"rem_fav_{movie_id}_{movie_name}"
        else:
            fav_text = "⭐"
            fav_call_back = f"add_fav_{movie_id}_{movie_name}"
        
        if is_seen_movie(update, context, movie_id):
            seen_text = "❌📅"
            seen_call_back = f"rem_seen_{movie_id}_{movie_name}"
        else:
            seen_text = "📅"
            seen_call_back = f"add_seen_{movie_id}_{movie_name}"
        
        if is_to_see_movie(update, context, movie_id):
            to_see_text = "❌👀"
            to_see_call_back = f"rem_tosee_{movie_id}_{movie_name}"
        else:
            to_see_text = "👀"
            to_see_call_back = f"add_tosee_{movie_id}_{movie_name}"


        inline_keyboard.append([InlineKeyboardButton(seen_text, callback_data=seen_call_back),
                                   InlineKeyboardButton(fav_text, callback_data=fav_call_back),
                                   InlineKeyboardButton(to_see_text, callback_data=to_see_call_back)
                                   ])

        # nel caso ci sia più di un film nella lista
        if len(movie_list) > 1:
            if current_index == 0:
                inline_keyboard.append([InlineKeyboardButton("Successivo  ⏩", callback_data='next_movie')])
            elif current_index == max_index:
                inline_keyboard.append([InlineKeyboardButton("⏪  Precedente", callback_data='prev_movie')])
            else:
                inline_keyboard.append([InlineKeyboardButton("⏪  Precedente", callback_data='prev_movie'),
                                   InlineKeyboardButton("Successivo  ⏩", callback_data='next_movie')])
        

        inline_keyboard.append([InlineKeyboardButton("Home 🏠", callback_data=f"home_page")])

        if current_movie['vote_count'] != 0:

            vote = round(current_movie['vote_average'], 1)

            if current_movie['vote_average'] <= 3:
                rating_string = f"{vote}/10 ☆☆☆☆☆"
            elif 3 < current_movie['vote_average'] <= 4.8:
                rating_string = f"{vote}/10 ★☆☆☆☆"
            elif 4.8 < current_movie['vote_average'] <= 6:
                rating_string = f"{vote}/10 ★★☆☆☆"
            elif 6 < current_movie['vote_average'] <= 7.4:
                rating_string = f"{vote}/10 ★★★☆☆"
            elif 7.4 < current_movie['vote_average'] <= 8.7:
                rating_string = f"{vote}/10 ★★★★☆"
            elif current_movie['vote_average'] > 8.7:
                rating_string = f"{vote}/10 ★★★★★"

            caption += f"\n\nValutazione: {rating_string}"


        # al primo film inviato si crea l'id del messaggio
        if context.user_data.get('current_message_id'):
            message_id = context.user_data.get('current_message_id')
        else:
            message_id = None

        if message_id is not None:
            try:
                message = context.bot.edit_message_media(chat_id=update.effective_chat.id, message_id=message_id, media=InputMediaPhoto(media=image_content, caption=caption, parse_mode=ParseMode.HTML), reply_markup=InlineKeyboardMarkup(inline_keyboard))
                context.user_data['current_message_id'] = message.message_id
            except Exception as e:
                print("Errore nell'aggiornamento del messaggio: ",  e)
        else:
            try:    # spesso i film sono allegati ad una foto perciò si usa "send_photo"
                message = context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_content, caption=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard))
                context.user_data['current_message_id'] = message.message_id
            except Exception as e:
                print("Errore nell'invio del messaggio con foto: ", e)

    except Exception as e:
        print("Errore nell'ottenimento del film: ", e)


# Gestisce la navigazione tra i film (precedente e successivo)
def handle_movie_navigation(update: Update, context: CallbackContext):
    try:
        query = update.callback_query

        if query.data == 'next_movie':
            context.user_data['current_movie_index'] += 1
        elif query.data == 'prev_movie':
            context.user_data['current_movie_index'] -= 1

        context.user_data['extended_movie_description'] = False

        send_list_of_movies(update, context)
    except Exception as e:
        print("Errore nel handle_movie_navigation(): ", e)


# Gestisce la visualizzazione della descrizione del film (estesa o ridotta).
def handle_movie_desc(update: Update, context: CallbackContext):
    try:
        query = update.callback_query

        if query.data == 'extend_description':
            context.user_data['extended_movie_description'] = True
        elif query.data == 'shorten_description':
            context.user_data['extended_movie_description'] = False

        send_list_of_movies(update, context)
    except Exception as e:
        print("Errore nel handle_movie_desc(): ", e)


# Crea un oggetto Updater per gestire il bot e il dispatcher per le funzioni
updater = Updater(TelegramTOKEN, use_context=True)
dispatcher = updater.dispatcher


# Comandi e callback per gestire varie azioni del bot

# Gestisce il comando /start e il pulsante di avvio
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(start, pattern='^start$'))

# Gestisce la navigazione verso la home page
dispatcher.add_handler(CallbackQueryHandler(home_page, pattern='^home_page$'))

# Gestisce l'apertura della pagina delle impostazioni
dispatcher.add_handler(CallbackQueryHandler(settings, pattern='^settings$'))

# Filtra i messaggi testuali non associati a comandi per la ricerca di film
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, more_film_search))

# Navigazione tra i film (precedente/successivo)
dispatcher.add_handler(CallbackQueryHandler(handle_movie_navigation, pattern='^(next_movie|prev_movie)$'))

# Guida l'utente a cercare un film tramite testo
dispatcher.add_handler(CallbackQueryHandler(help_search, pattern='^help_search$'))

# Ricerca di film in uscita e più votati
dispatcher.add_handler(CallbackQueryHandler(upcoming_movies_search, pattern='^upcoming_movies_search$'))
dispatcher.add_handler(CallbackQueryHandler(latest_top_rated_movies, pattern='^latest_top_rated_movies$'))

# Gestione della richiesta di eliminazione dell'utente e conferma eliminazione
dispatcher.add_handler(CallbackQueryHandler(ask_delete_user, pattern='^ask_delete_user$'))
dispatcher.add_handler(CallbackQueryHandler(delete_user, pattern='^delete_user$'))

# Estensione o riduzione della descrizione del film
dispatcher.add_handler(CallbackQueryHandler(handle_movie_desc, pattern='^(extend_description|shorten_description)$'))

# Aggiunta o rimozione di film dal database (visti, preferiti, da vedere)
dispatcher.add_handler(CallbackQueryHandler(add_movies_db, pattern='^add_(seen|fav|tosee)_\\d+_.+'))
dispatcher.add_handler(CallbackQueryHandler(rem_movies_db, pattern='^rem_(seen|fav|tosee)_\\d+_.+(_settings)?$')) # puo contere "settings" o no

# Ricerca dettagliata per ID di un film
dispatcher.add_handler(CallbackQueryHandler(one_film_search, pattern='^id_\\d+$'))

# Visualizzazione o modifica dei film nelle liste (visti, preferiti, da vedere)
dispatcher.add_handler(CallbackQueryHandler(display_movies, pattern='^(edit_)?(seen|fav|tosee)_movies$'))

# Cambiamento della lingua o della regione del bot e del database
dispatcher.add_handler(CallbackQueryHandler(change_lang_region, pattern='^change_lang_region$'))
dispatcher.add_handler(CallbackQueryHandler(change_lang_setting, pattern='^change_lang_setting$'))
dispatcher.add_handler(CallbackQueryHandler(change_region_setting, pattern='^change_region_setting$'))
dispatcher.add_handler(CallbackQueryHandler(change_lang_db, pattern='^change_lang_[a-zA-Z_]+$'))
dispatcher.add_handler(CallbackQueryHandler(change_region_db, pattern='^change_region_[a-zA-Z_]+$'))


# Avvia il bot in modalità polling
print("Bot in ascolto...")
updater.start_polling()