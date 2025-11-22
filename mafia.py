from telebot import TeleBot
import db
from dotenv import load_dotenv
import os
import time

load_dotenv()

TOKEN = os.getenv("TOKEN")
bot = TeleBot(TOKEN)

game = False
night = False

@bot.message_handler(commands=["start"])
def game_on(message):
    if not game:
        bot.send_message(message.chat.id, text="Если хотите играть напишите 'готов играть' в лс боту")

@bot.message_handler(func=lambda m: m.text.lower() == 'готов играть' and m.chat.type == "private")
def send_text(message):
    bot.send_message(message.chat.id, text=f"{message.from_user.first_name} играет")
    bot.send_message(message.from_user.id, text="Вы добавлены в игру")
    db.insert_player(message.from_user.id, message.from_user.first_name)

@bot.message_handler(commands=["game"])
def game_start(message):
    global game
    players = db.players_amount()
    if players >= 5 and not game:
        db.set_roles()
        players_roles = db.get_players_roles()
        mafia_usernames = db.get_mafia_usernames()
        for player_id, role in players_roles:
            role_text = get_role_description(role)
            bot.send_message(player_id, text=f"Ваша роль: {role}\n\n{role_text}")
            if role == "mafia":
                bot.send_message(player_id, text=f"Все игроки мафии:\n{', '.join(mafia_usernames)}")
        game = True
        bot.send_message(message.chat.id, text="Игра началась!")
        db.clear(dead=True)
        game_loop(message)
        return
    bot.send_message(message.chat.id, "Недостаточно!")

def get_role_description(role):
    descriptions = {
        "citizen": "Мирный гражданин - ваша задача найти и казнить мафию.",
        "mafia": "Мафия - ваша задача убивать мирных жителей ночью.",
        "sheriff": "Шериф - вы можете проверять игроков ночью.",
        "doctor": "Доктор - вы можете лечить игроков ночью.",
        "cat": "Кот - вы можете мешать другим игрокам выполнять их роли."
    }
    return descriptions.get(role, "Ваша роль в игре.")

@bot.message_handler(commands=["kick"])
def kick(message):
    username = ' '.join(message.text.split(' ')[1:])
    usernames = db.get_all_alive()
    if not night:
        if username not in usernames:
            bot.send_message(message.chat.id, 'Такого имени нет')
            return
        voted = db.vote("citizen_vote", username, message.from_user.id)
        if voted:
            bot.send_message(message.chat.id, 'Ваш голос учитан')
            return
        bot.send_message(message.chat.id, 'У вас больше нет права голосовать')
        return
    bot.send_message(message.chat.id, 'Сейчас ночь вы не можете никого выгнать')

@bot.message_handler(commands=["kill"])
def kill(message):
    username = ' '.join(message.text.split(' ')[1:])
    if not username:
        bot.send_message(message.chat.id, 'Укажите имя игрока: /kill username')
        return
    if not night:
        bot.send_message(message.chat.id, 'Сейчас день, вы не можете убивать')
        return
    alive_players = db.get_all_alive()
    if username not in alive_players:
        bot.send_message(message.chat.id, 'Этот игрок не в игре или уже мертв')
        return
    players_roles = db.get_players_roles()
    player_role = None
    for player_id, role in players_roles:
        if player_id == message.from_user.id:
            player_role = role
            break
    if player_role != 'mafia':
        bot.send_message(message.chat.id, 'Только мафия может убивать ночью')
        return
    voted = db.vote("mafia_vote", username, message.from_user.id)
    if voted:
        bot.send_message(message.chat.id, 'Ваш голос за убийство учтен')
    else:
        bot.send_message(message.chat.id, 'Вы не можете голосовать')

def get_killed(is_night):
    if not is_night:
        username_killed = db.citizens_kill()
        return f'Горожане выгнали: {username_killed}'
    else:
        username_killed = db.mafia_kill()
        return f'Мафия убила: {username_killed}'

def game_loop(message):
    global night, game
    bot.send_message(message.chat.id, "Добро пожаловать в игру! Вам 2 минуты на размышление")
    time.sleep(120)
    while True:
        msg = get_killed(night)
        bot.send_message(message.chat.id, msg)
        if night:
            bot.send_message(message.chat.id, "Город засыпает, просыпается мафия")
        else:
            bot.send_message(message.chat.id, "Город просыпается")
        win = db.check_winner()
        if win == "Мафия" or win == "Горожане":
            game = False
            bot.send_message(message.chat.id, f"Игра окончена, победитель: {win}")
            return
        db.clear()
        night = not night
        alive = db.get_all_alive()
        alive = "\n".join(alive)
        bot.send_message(message.chat.id, text=f"В игре остались: \n{alive}")
        time.sleep(60)

if __name__ == "__main__":
    bot.polling()
