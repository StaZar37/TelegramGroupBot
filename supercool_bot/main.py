from aiogram import Bot, Dispatcher, executor, types
import asyncio
import json

from aiogram.types import chat

adm_file  = "admins.json"
admin_id  = json.load(open(adm_file, "r", encoding="utf8"))["admins"]
conf_file = "config.json"
bot_token = "" 
config    = json.load(open(conf_file, "r", encoding="utf8"))
bot       = Bot(token=bot_token, parse_mode="html")
dp        = Dispatcher(bot)


if not bool(admin_id):
    exit("Нужно зазначить айди админа!")


if bot_token == "":
    exit("Нужно зазначить токен бота!")


def get_config():
    global config
    msg = ""
    for setting in config:
        if msg != "":
            msg += "\n"
        
        if setting == "chats_id":
            to_add  = ""
            for i in range(0, len(config[setting])):
                to_add += "{} ".format(config[setting][i])
            msg    += "{}: {}".format(setting, to_add)
        else:
            msg += "{}: {}".format(setting, config[setting])
    
    return msg


# Проверка на админа в боте чтобы можно было менять
@dp.message_handler(commands=["start"])
async def hi_admin(message: types.Message):
    try:
        global config
        # Проверка на то, админ ли написал комманду и лс ли это с админом
        chat_id = message["chat"]["id"]
        if int(message["from"]["id"]) in admin_id and int(chat_id) in admin_id:
            msg = "Здравствуй, админ!\nТекущие настройки:"
            await bot.send_message(chat_id=chat_id, text=msg)
            
            msg = get_config()
            await bot.send_message(chat_id=chat_id, text=msg)
    except:
        pass


# Проверка на админа в боте чтобы можно было менять
@dp.message_handler(commands=["add_admin"])
async def add_admin(message: types.Message):
    try:
        global admin_id
        # Проверка на то, админ ли написал комманду и лс ли это с админом
        chat_id = message["chat"]["id"]
        if int(message["from"]["id"]) in admin_id and int(chat_id) in admin_id:
            id = int(message["text"].split(" ")[1])
            admin_id.append(id)
            data = {"admins": admin_id}
            json.dump(data, open(adm_file, "w", encoding="utf8"), indent=4)
            admin_id = json.load(open(adm_file, "r", encoding="utf8"))["admins"]

            msg = f"Новый администратор ({id}) добавлен!"
            await bot.send_message(chat_id=chat_id, text=msg)
    except:
        pass


# Добавление чата в список чатов
@dp.message_handler(commands=["add_chat_to_list"])
async def add_chat_to_list(message: types.Message):
    try:
        global config
        # Проверка на то, админ ли написал комманду
        if int(message["from"]["id"]) in admin_id:
            chat_id = message["chat"]["id"]
            if chat_id not in config["chats_id"] and chat_id not in admin_id:
                config["chats_id"].append(chat_id)
                json.dump(config, open(conf_file, "w", encoding="utf8"), indent=4)
                config = json.load(open(conf_file, "r", encoding="utf8"))
    except:
        pass


# Принятие коммнады от админа на смену настройки
@dp.message_handler(content_types=["text"])
async def command_handler(message: types.Message):
    try:
        global config
        if "/change " in message["text"]:
            # Проверка на то, админ ли написал комманду и лс ли это с админом
            chat_id = message["chat"]["id"]
            if int(message["from"]["id"]) in admin_id and int(chat_id) in admin_id:
                s = message["text"].replace("/change ", "")
                setting = s.split(" ")[0]
                value   = s.replace(setting, "").strip()

                if setting != "chats_id":
                    config[setting] = value
                    json.dump(config, open(conf_file, "w", encoding="utf8"), indent=4)
                    config = json.load(open(conf_file, "r", encoding="utf8"))

                    await bot.send_message(chat_id=chat_id, text="Настройка {} изменена!".format(setting))
                else:
                    await bot.send_message(chat_id=chat_id, text="Настройку chats_id менять нельзя!")
    except:
        pass


# Обработчик системных сообщений
to_del = ["new_chat_members", "left_chat_member", "new_chat_photo", "new_chat_title", "pinned_message", "delete_chat_photo", "group_chat_created", "supergroup_chat_created", "channel_chat_created", "migrate_to_chat_id", "migrate_from_chat_id"]
@dp.message_handler(content_types = to_del) #
async def handler(message: types.Message):
    chat_id = message["chat"]["id"]
    if chat_id in config["chats_id"]:
        await bot.delete_message(chat_id, message.message_id)


# Функция рассылки сообщений
async def send():
    try:
        global config
        pre = json.load(open("pre.json", "r", encoding="utf8"))
        new = {}
        for chat in config["chats_id"]:
            temp = await bot.send_message(chat_id=chat, text=config["text1"])
            await bot.send_message(chat_id=chat, text=config["text2"])
            await bot.pin_chat_message(chat_id=chat, message_id=temp["message_id"])
            new[chat] = temp["message_id"]
            del(temp)
            try:
                check = bool(pre[str(chat)])
            except:
                check = False
            if check:
                try:
                    await bot.delete_message(chat_id=chat, message_id=pre[str(chat)])
                    await bot.delete_message(chat_id=chat, message_id=pre[str(chat)]+1)
                    if "pinned_message" not in to_del:
                        await bot.delete_message(chat_id=chat, message_id=pre[str(chat)]+2)
                except:
                    pass
        json.dump(new, open("pre.json", "w", encoding="utf8"), indent=4)
    except:
        pass


# Функция которая будет зацикливать отправку сообщений
def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(60 * (int(config["interval"])), repeat, coro, loop)


# Старт
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.call_later(5, repeat, send, loop)
    executor.start_polling(dp, skip_updates=True)