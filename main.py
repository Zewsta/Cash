# -*- coding: utf-8 -*-

__updated__ = "2024-07-15 02:19:39"


import logging
import asyncio
from random import choice
from pyrogram import Client, filters
from pymongo import MongoClient
import random
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
    User,
    ChatMemberUpdated,
    ChatMember,
)
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User,
    CallbackQuery,
    ChatMember,
    ChatMemberUpdated,
)

from pyrogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats


import time
import sqlite3
from datetime import datetime, timedelta



#-------------------------------------------------------------------#

BOT_ID = 7475250022
OWNER_ID = 5800604871
WINNERS = [7366076494, 7396502046] #Sürekli Kazanan
LOG_GROUP_ID = -1002230319301


#-------------------------------------------------------------------#



initial_balance = 30000


user_balances = {}


richest_users = []


start_message = """
**❤️‍🩹 Merhaba {} **

**Ben Bir Oyun Botuyum! Hemen Oynamaya Başlamak İçin Aşağıdaki Butonları Kullanarak Grubunuza Ekleyebilirsiniz.** 🌹

"""

komutlar = """
★ **Komutlar** ★

➔ **/c - Cash oyununu oynamak için.** 🎮
   Örnek: `/c 50` veya `/c 50 2x`
   ✅ NOT: `/w 50 3x` yaptığınızda, çarpan kadar paranız gider.

➔ **/cf - Futbol oyununu oynamak için.** ⚽️
   Örnek: `/cf 100` veya `/cf 100 3x`

➔ **/cs - Slot oyununu oynamak için.** 🎰
   Örnek: `/cs 50` veya `/cs 50 2x`

➔ **/bonus - Günlük alacağınız bonus.** 🤩

➔ **/bakiye - Bakiyenizi kontrol etmek için.** 💰

➔ **/borc - Birine borç göndermek için.** 💸
   Örnek: `/borc [Miktar] [Kullanıcı İD]` veya Mesajı Yanıtla.

➔ **/top10 - En zengin kullanıcıları görmek için.** 🤑

🔮 NOT: `/c`, `/cf` ve `/cs` komutları sadece gruplarda çalışır.

**Destek -** t.me/Reduxon
"""

#-------------------------------------------------------------------#
API_ID = 28480994
API_HASH = "eddbf24f0a04c848f80e9c697796ad55"
BOT_TOKEN = "7475250022:AAFLAbeYvzAvwFp87fbCJLEwMh_qEiAmFNU"

#-------------------------------------------------------------------#

mongo_client = MongoClient("mongodb+srv://blayzenx:BEPSMKcYQWadGdOQ@rose.w1ytknr.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["slot_bot_db"]
balances_collection = db["balances"]
richest_collection = db["richest"]
blocked_collection = db["blocked"] 
collection = db['user_bonus_times']  
groups_collection = db["groups"]
users_collection = db["users"]


#-------------------------------------------------------------------#

logging.basicConfig(filename='bot.log', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Client("slot_bot", 
             api_id=API_ID, 
             api_hash=API_HASH, 
             bot_token=BOT_TOKEN
        )


#-------------------------------------------------------------------#
slot_bot = {}

users = []

reloadStatus = []

async def set_commands(client):
    private_commands = [
        BotCommand("start", "Botu başlatır"),
        BotCommand("yardim", "Yardım menüsünü açar"),
    ]

    
    group_commands = [
        BotCommand("c", "🎮 Cash Oyununu Oynatır"),
        BotCommand("cs", "🎰 Slot Oyununu Oynatır"),
        BotCommand("cf", "⚽ Futbol Oyununu Oynatır"),
        BotCommand("zenginler", "🏆 Zenginler Listesini Gösterir"),
        BotCommand("bakiye", "💵 Bakiyenizi Gösterir"),
        BotCommand("borc", "💸 Bir Kişiye Borç Gönderirsiniz"),
        BotCommand("bonus", "🚀 Günlük Bonus Verir"),
    
    ]
    
    
    await client.set_bot_commands(private_commands, scope=BotCommandScopeAllPrivateChats())
    
    await client.set_bot_commands(group_commands, scope=BotCommandScopeAllGroupChats())

 

def is_user_blocked(user_id):
    return blocked_collection.find_one({"user_id": user_id}) is not None


def block_user(user_id):
    blocked_collection.update_one({"user_id": user_id}, {"$set": {"blocked": True}}, upsert=True)


def unblock_user(user_id):
    blocked_collection.delete_one({"user_id": user_id})

def load_balances():
    global user_balances
    user_balances = {doc["user_id"]: doc["balance"] for doc in balances_collection.find()}


def save_balance(user_id, balance):
    balances_collection.update_one({"user_id": user_id}, {"$set": {"balance": balance}}, upsert=True)


def load_richest_users():
    global richest_users
    richest_users = [doc["user_id"] for doc in richest_collection.find().sort("balance", -1).limit(15)]


def save_richest_users():
    richest_collection.delete_many({})
    for user_id in richest_users:
        richest_collection.insert_one({"user_id": user_id, "balance": user_balances[user_id]})


def is_user_blocked(user_id):
    return blocked_collection.find_one({"user_id": user_id}) is not None


def block_user(user_id):
    blocked_collection.update_one({"user_id": user_id}, {"$set": {"blocked": True}}, upsert=True)


def unblock_user(user_id):
    blocked_collection.delete_one({"user_id": user_id})

#-------------------------------------------------------------------#


def connect_to_database(db_path):
    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            conn = sqlite3.connect(db_path)
            return conn
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print("Veritabanı kilitli. Bekleniyor...")
                time.sleep(1)  
                retry_count += 1
            else:
                raise e

    raise Exception("Veritabanına bağlanırken hata oluştu: Veritabanı kilitli.")

#-------------------------------------------------------------------#

bonus_interval_hours = 3  

user_last_bonus_time = {}

user_last_cash_time = {}

load_balances()
load_richest_users()

#-------------------------------------------------------------------#



@app.on_message(filters.command("start") & filters.private)
async def start(bot: Client, message: Message):
    chat_id = message.chat.id
    first_name = message.from_user.mention
    user_id = message.from_user.id

    
    if user_id not in user_balances:
        user_balances[user_id] = initial_balance
        save_balance(user_id, initial_balance)

    
    users_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "first_name": first_name,
                "username": message.from_user.username
            }
        },
        upsert=True
    )

    await bot.send_message(LOG_GROUP_ID, f"""
#ÖZELDEN START VERDİ#

🤖 **Kullanıcı:** {first_name}
📛 **Kullanıcı Adı:** @{message.from_user.username}
🆔 **Kullanıcı ID:** `{message.from_user.id}`
""")
    msg = await message.reply_text("🔮")
    await asyncio.sleep(2)
    await msg.delete()
    await bot.send_message(
        chat_id,
        start_message.format(message.from_user.mention),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📚 Komutlar", callback_data="cvv"),
                ],
                [
                    InlineKeyboardButton("🗯 Destek", url=f"https://t.me/Reduxon"),
                    InlineKeyboardButton("✚ Beni Grubuna Ekle", url=f"https://t.me/LostCashBot?startgroup=a"),
                ],
                [
                    InlineKeyboardButton("❤️‍🔥 Developer", user_id=OWNER_ID),
                ]
            ]
        ),
        disable_web_page_preview=True,
    )



@app.on_callback_query(filters.regex("cvv"))
async def handler(bot: Client, query: CallbackQuery):
    await query.edit_message_text(
        komutlar,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅ Geri", 
                        callback_data="goktug"),                                            
                ],
            ],
        ),
        disable_web_page_preview=True,
    )


# Başlanğıc Button
@app.on_callback_query(filters.regex(r'^goktug$'))
async def _start(bot: Client, query: CallbackQuery):
    await query.edit_message_text(
        start_message.format(query.from_user.mention),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📚 Komutlar", callback_data="cvv"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🗯 Destek", url=f"https://t.me/Reduxon"
                    ),

                    InlineKeyboardButton(
                        "✚ Beni Grubuna Ekle" , url=f"https://t.me/LostCashBot?startgroup=a"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "❤️‍🔥 Developer", user_id=OWNER_ID
                    ),
                ]
            ],
        ),
        disable_web_page_preview=True,
    )   






@app.on_message(filters.command(["zenginler", "top10"]))
async def get_richest(client: Client, message: Message):
    user_id = message.from_user.id
    is_group = message.chat.type in ["supergroup", "group"]
    text = ""

    try:
        if is_group:
            users = await client.get_chat_members(message.chat.id)
            user_ids = [user.user.id for user in users]
            eligible_users = {uid: balance for uid, balance in user_balances.items() if uid in user_ids}
        else:
            eligible_users = user_balances

        richest_users_list = sorted(eligible_users.items(), key=lambda x: x[1], reverse=True)
        final_richest_users_list = []

        for user_id, balance in richest_users_list:
            if len(final_richest_users_list) >= 10:
                break
            try:
                user = await client.get_users(user_id)
                final_richest_users_list.append((user, balance))
            except:
                continue

        if is_group:
            text = "🏆 **Bu grup için En Zengin Kullanıcıları:**\n\n"
        else:
            text = "**🏆 Tüm Zamanların en zengin kullanıcıları:**\n\n"

        for i, (user, balance) in enumerate(final_richest_users_list[:3], start=1):
            if i == 1:
                text += f"▫️ **1.** {user.first_name} » `{balance}` **₺**\n"
            elif i == 2:
                text += f"▫️ **2.** {user.first_name} » `{balance}` **₺**\n"
            elif i == 3:
                text += f"▫️ **3.** {user.first_name} » `{balance}` **₺**\n"

        for i, (user, balance) in enumerate(final_richest_users_list[3:], start=4):
            text += f"▫️ **{i}.** {user.first_name} » `{balance}` **₺**\n"

    except Exception as e:
        text = f"Bir hata oluştu: {e}"

    await message.reply_text(text)









@app.on_message(filters.command("ebonus") & filters.user(OWNER_ID))
async def daily_bonus_to_all(client: Client, message: Message):
    try:
        for user_id in user_balances:
            user_balances[user_id] += 25000
            save_balance(user_id, user_balances[user_id])
        await message.reply("**Tüm kullanıcılara bonus başarıyla eklendi.** 🌹")
    except Exception as e:
        await message.reply(f"**Günlük bonus eklenirken bir hata oluştu:** {e}")







@app.on_message(filters.command("cs") & filters.group)
async def play_basket(client: Client, message: Message):
    if is_user_blocked(message.from_user.id):
        await message.reply("**Üzgünüm, bu komutu kullanma yetkiniz engellendi.** 🚫")
        return

    user_id = message.from_user.id

    if user_id not in user_balances:
        await message.reply("**Slot oyununu oynamak için önce özelden start verin. 🎉")
        return

    current_time = datetime.now()
    last_cash_time = user_last_cash_time.get(user_id)

    if last_cash_time and current_time - last_cash_time < timedelta(seconds=3):
        await message.reply(f"**Lütfen 3 saniye bekleyin. ⏳**")
        return

    try:
        amount_str = message.command[1]
        if not amount_str.isdigit() or len(amount_str) > 17:
            await message.reply("**Lütfen sadece maksimum 17 rakam içeren bir miktar girin. 💵**")
            return
        
        amount = int(amount_str)

        multiplier = 1
        if len(message.command) > 2:
            multiplier_str = message.command[2]
            if multiplier_str[-1] == 'x' and multiplier_str[:-1].isdigit():
                multiplier = int(multiplier_str[:-1])
            else:
                raise ValueError()
            if multiplier < 1 or multiplier > 10:
                await message.reply("**Çarpan 1x ile 10x arasında olmalıdır. Örnek: /cs 45 2x 🎰**")
                return

    except (IndexError, ValueError):
        await message.reply("**Lütfen geçerli bir miktar ve çarpan girin. Örnek: /cs 45 veya /cs 45 2x 🎰**")
        return

    if amount <= 0:
        await message.reply("**Lütfen pozitif bir miktar girin.** 💵")
        return

    user_balance = user_balances.get(user_id, 0)

    if amount > user_balance:
        await message.reply("**Yeterli bakiyeniz yok.** 😢")
        return

    
    dice_message = await client.send_dice(message.chat.id, emoji="🎰")

    
    await asyncio.sleep(3)

    
    dice_value = dice_message.dice.value

    
    if dice_value >= 4:  
        win_amount = amount * multiplier
        user_balances[user_id] = max(user_balance + win_amount, 0)
        result_message = f"**Tebrikler 🥳 Şansın Yaver Gitti Braavooo!** `{win_amount}` ₺ **Kazandınız.**\n**Güncel Bakiyeniz: `{user_balances[user_id]}` ₺ 💵**"
    else:
        win_amount = -amount * multiplier
        user_balances[user_id] = max(user_balance + win_amount, 0)
        result_message = f"**Üzgünüm 🥹 Şansınız Yokmuş Başka Sefere** `{amount * multiplier}` ₺ **Kaybettiniz.**\n**Güncel Bakiyeniz: `{user_balances[user_id]}` ₺ 💵**"


    save_balance(user_id, user_balances[user_id])

    if user_id not in richest_users and len(richest_users) < 10:
        richest_users.append(user_id)
    richest_users.sort(key=lambda x: user_balances[x], reverse=True)
    save_richest_users()

    user_last_cash_time[user_id] = current_time

    
    
    chat = message.chat
    user = message.from_user

    user_name = user.username if user.username else "None"
    group_name = chat.title
    group_link = f"@{chat.username}" if chat.username else "None"

    await client.send_message(LOG_GROUP_ID, f"""
**KOMUT KULLANILDI**

👤 **Kullanıcı:** {user.mention}
📛 **Kullanıcı Adı:** @{user_name}
🆔 **Kullanıcı İD:** `{user.id}`
🏘️ **Grup Adı:** {group_name}
🤖 **Grup İD:** `{chat.id}`
🔗 **Grup Linki:** {group_link}
🈷️ **Miktar:** {message.text} ₺
🔰 **Sonuç:** {'kazandı' if win_amount > 0 else 'kaybetti'}
💵 **Güncel Bakiye:** `{user_balances[user_id]}` ₺
""")

    
    
    await message.reply(result_message)






@app.on_message(filters.command("cf") & filters.group)
async def play_basket(client: Client, message: Message):
    if is_user_blocked(message.from_user.id):
        await message.reply("Üzgünüm, bu komutu kullanma yetkiniz engellendi. 🚫")
        return

    user_id = message.from_user.id

    if user_id not in user_balances:
        await message.reply("**Futbol oyununu oynamak için önce özelden start verin.** 🌹")
        return

    current_time = datetime.now()
    last_cash_time = user_last_cash_time.get(user_id)

    if last_cash_time and current_time - last_cash_time < timedelta(seconds=3):
        await message.reply(f"**Lütfen 3 saniye bekleyin. ⏳**")
        return

    try:
        amount_str = message.command[1]
        if not amount_str.isdigit() or len(amount_str) > 17:
            await message.reply("**Lütfen sadece maksimum 17 rakam içeren bir miktar girin. 💵**")
            return
        
        amount = int(amount_str)

        multiplier = 1
        if len(message.command) > 2:
            multiplier_str = message.command[2]
            if multiplier_str[-1] == 'x' and multiplier_str[:-1].isdigit():
                multiplier = int(multiplier_str[:-1])
            else:
                raise ValueError()
            if multiplier < 1 or multiplier > 10:
                await message.reply("**Çarpan 1x ile 10x arasında olmalıdır. Örnek: /cf 45 2x ⚽️**")
                return

    except (IndexError, ValueError):
        await message.reply("**Lütfen geçerli bir miktar ve çarpan girin. Örnek: /cf 45 veya /cf 45 2x ⚽️**")
        return

    if amount <= 0:
        await message.reply("**Lütfen pozitif bir miktar girin.** 💵")
        return

    user_balance = user_balances.get(user_id, 0)

    if amount > user_balance:
        await message.reply("**Yeterli bakiyeniz yok.** 😢")
        return

    
    dice_message = await client.send_dice(message.chat.id, emoji="⚽️")

    
    await asyncio.sleep(3)

    
    dice_value = dice_message.dice.value

    
    if dice_value >= 3:  
        win_amount = amount * multiplier
        user_balances[user_id] = max(user_balance + win_amount, 0)
        result_message = f"**Tebrikler 🥳 Muhteşem Bir Goolll** `{win_amount}` ₺ **Kazandınız.**\n**Güncel Bakiyeniz: `{user_balances[user_id]}` ₺ 💵**"
    else:
        win_amount = -amount * multiplier
        user_balances[user_id] = max(user_balance + win_amount, 0)
        result_message = f"**Üzgünüm 🥹 Sabriiii** `{amount * multiplier}` ₺ **Kaybettiniz.**\n**Güncel Bakiyeniz: `{user_balances[user_id]}` ₺ 💵**"
    

    save_balance(user_id, user_balances[user_id])

    if user_id not in richest_users and len(richest_users) < 10:
        richest_users.append(user_id)
    richest_users.sort(key=lambda x: user_balances[x], reverse=True)
    save_richest_users()

    user_last_cash_time[user_id] = current_time

    
    chat = message.chat
    user = message.from_user

    user_name = user.username if user.username else "None"
    group_name = chat.title
    group_link = f"@{chat.username}" if chat.username else "None"

    await client.send_message(LOG_GROUP_ID, f"""
**KOMUT KULLANILDI**

👤 **Kullanıcı:** {user.mention}
📛 **Kullanıcı Adı:** @{user_name}
🆔 **Kullanıcı İD:** `{user.id}`
🏘️ **Grup Adı:** {group_name}
🤖 **Grup İD:** `{chat.id}`
🔗 **Grup Linki:** {group_link}
🈷️ **Miktar:** {message.text} ₺
🔰 **Sonuç:** {'kazandı' if win_amount > 0 else 'kaybetti'}
💵 **Güncel Bakiye:** `{user_balances[user_id]}` ₺
""")

    # Sonucu kullanıcıya bildir
    await message.reply(result_message)









@app.on_message(filters.command("w") & filters.group)
async def play_slot(client: Client, message: Message):
    if is_user_blocked(message.from_user.id):
        await message.reply("Üzgünüm, bu komutu kullanma yetkiniz engellendi. 🚫")
        return

    user_id = message.from_user.id

    
    if user_id not in user_balances:
        await message.reply("**Cash oyununu oynamak için önce özelden start verin.** 🌹")
        return

    
    current_time = datetime.now()
    last_cash_time = user_last_cash_time.get(user_id)

    if last_cash_time and current_time - last_cash_time < timedelta(seconds=3):
        remaining_time = timedelta(seconds=3) - (current_time - last_cash_time)
        await message.reply(f"**Lütfen 3 saniye bekleyin. ⏳**")
        return

    try:
        amount_str = message.command[1]

        
        
        if not amount_str.isdigit() or len(amount_str) > 17:
            await message.reply("**Lütfen sadece maksimum 17 rakam içeren bir miktar girin. 💵**")
            return
        
        amount = int(amount_str)

        
        multiplier = 1

        
        if len(message.command) > 2:
            multiplier_str = message.command[2]
            if multiplier_str[-1] == 'x' and multiplier_str[:-1].isdigit():
                multiplier = int(multiplier_str[:-1])
            else:
                raise ValueError()

            # Çarpanın 1 ile 3 arasında olmasını kontrol et
            if multiplier < 1 or multiplier > 10:
                await message.reply("**Çarpan 1x ile 10x arasında olmalıdır. Örnek: /c 45 2x 🎮**")
                return

    except (IndexError, ValueError):
        await message.reply("**Lütfen geçerli bir miktar ve çarpan girin. Örnek: /c 45 veya /c 45 2x 🎮**")
        return

    if amount <= 0:
        await message.reply("**Lütfen pozitif bir miktar girin.** 💵")
        return

    user_balance = user_balances.get(user_id, 0)

    if amount > user_balance:
        await message.reply("**Yeterli bakiyeniz yok.** 😢")
        return

    
    win_chance = 0.30 # %45 kazanma şansı
    if user_id in WINNERS or random.random() < win_chance:
        win_amount = amount * multiplier
    else:
        win_amount = -amount * multiplier  # Çarpan kadar miktarı bakiyeden düş

    
    user_balances[user_id] = max(user_balance + win_amount, 0)
    save_balance(user_id, user_balances[user_id])

    
    if user_id not in richest_users and len(richest_users) < 10:
        richest_users.append(user_id)
    richest_users.sort(key=lambda x: user_balances[x], reverse=True)
    save_richest_users()

    
    user_last_cash_time[user_id] = current_time

    
    result = "Kazandınız" if win_amount > 0 else "Kaybettiniz"
    await message.reply(f"**Tebrikler 🥳 `{win_amount}` ₺ {result}.**\n**Güncel Bakiyeniz: `{user_balances[user_id]}` ₺ 💵**" if win_amount > 0 else f"**Üzgünüm 🥹 `{amount * multiplier}` ₺ {result}.**\n**Güncel Bakiyeniz: `{user_balances[user_id]}` ₺ 💵**")

    
    chat = message.chat
    user = message.from_user

    user_name = user.username if user.username else "None"
    group_name = chat.title
    group_link = f"@{chat.username}" if chat.username else "None"

    await client.send_message(LOG_GROUP_ID, f"""
**KOMUT KULLANILDI**

👤 **Kullanıcı:** {user.mention}
📛 **Kullanıcı Adı:** @{user_name}
🆔 **Kullanıcı İD:** `{user.id}`
🏘️ **Grup Adı:** {group_name}
🤖 **Grup İD:** `{chat.id}`
🔗 **Grup Linki:** {group_link}
🈷️ **Miktar:** {message.text} ₺
🔰 **Sonuç:** {result}
💵 **Güncel Bakiye:** `{user_balances[user_id]}` ₺
""")





@app.on_message(filters.command("ebakiye") & filters.user(OWNER_ID))
async def add_balance(client: Client, message: Message):
    try:
        amount = int(message.command[1])
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        else:
            user_id = int(message.command[2])
    except (IndexError, ValueError):
        await message.reply("**Lütfen geçerli bir miktar ve kullanıcı kimliği girin. Örnek: /ebakiye [Miktar] * [Kullanıcı İD] veya yanıtla.** 💵")
        return
    if amount <= 0:
        await message.reply("**Lütfen pozitif bir miktar girin.** 💵")
        return
    user_balances[user_id] = user_balances.get(user_id, initial_balance) + amount
    save_balance(user_id, user_balances[user_id])
    # Zenginler listesini güncelle
    if user_id not in richest_users and len(richest_users) < 15:
        richest_users.append(user_id)
    richest_users.sort(key=lambda x: user_balances[x], reverse=True)
    save_richest_users()
    user = await client.get_users(user_id)
    await message.reply(f"**`{amount}` ₺ Başarıyla `{user.first_name}` Adlı Kullanıcıya Eklendi.** ✅\n**Güncel Bakiyesi: `{user_balances[user_id]}` ₺ 💵**")
    




# Borç komutu
@app.on_message(filters.command(["borc", "borç"]) & filters.group)
async def lend_money(client: Client, message: Message):   
    if is_user_blocked(message.from_user.id):
        await message.reply("**Üzgünüm, bu komutu kullanma yetkiniz engellendi.** 🚫")
        return

    try:
        amount = int(message.command[1])
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        else:
            user_id = int(message.command[2])
    except (IndexError, ValueError):
        await message.reply("**Geçersiz komut kullanımı. 🌹 Örnek: /borc [yanıtla] [miktar]** 💸")
        return

    from_user_id = message.from_user.id
    from_user_balance = user_balances.get(from_user_id, 0)
    to_user_balance = user_balances.get(user_id, 0)

    if amount <= 0 or amount > from_user_balance:
        await message.reply("**Yetersiz bakiye.** 💸")
        return

    user_balances[from_user_id] -= amount
    user_balances[user_id] += amount
    save_balance(from_user_id, user_balances[from_user_id])
    save_balance(user_id, user_balances[user_id])

    to_user = await client.get_users(user_id)
    await message.reply(f"**{message.from_user.first_name}, {to_user.first_name} Adlı Kullanıcıya `{amount}` ₺ Borç Verdi. ✅**\n\n**Güncel Bakiyeniz: `{user_balances[from_user_id]}` ₺ 💵**")





@app.on_message(filters.command("bakiye"))
async def check_balance(client: Client, message: Message):
    if is_user_blocked(message.from_user.id):
        await message.reply("**Üzgünüm, bu komutu kullanma yetkiniz engellendi.** 🚫")
        return
    
    
    if message.reply_to_message and message.reply_to_message.from_user:
        replied_user = message.reply_to_message.from_user
        user_balance = user_balances.get(replied_user.id, initial_balance)
        await message.reply(f"**{replied_user.mention} Kullanıcısının Güncel Bakiyesi: `{user_balance}` ₺** 💵")
    else:
        
        user_id = message.from_user.id
        user_balance = user_balances.get(user_id, initial_balance)
        await message.reply(f"**Güncel Bakiyeniz: `{user_balance}` ₺** 💵")





# Bakiyeyi sıfırlama komutu
@app.on_message(filters.command("sifirla") & filters.user(OWNER_ID))
async def reset_balance(client: Client, message: Message):
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        else:
            user_id = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply("**Geçersiz komut kullanımı. Örnek: /sifirla [Kullanıcı İD] veya yanıtla.**")
        return

    if user_id not in user_balances:
        await message.reply("**Belirtilen kullanıcının bakiyesi bulunamadı.**")
        return

    
    user_balances[user_id] = 0
    save_balance(user_id, 0)

    
    if user_id in richest_users:
        richest_users.remove(user_id)
        save_richest_users()

    await message.reply("**Kullanıcının bakiyesi sıfırlandı ve zenginler listesinden kaldırıldı.** 🔥")





# Kullanıcıyı engelleme komutu
@app.on_message(filters.command("block") & filters.user(OWNER_ID))
async def block_user_cmd(client: Client, message: Message):
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        else:
            user_id = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply("**Geçersiz komut kullanımı. Örnek: /block [Kullanıcı İD] veya yanıtla.**")
        return

    block_user(user_id)
    await message.reply(f"**Kullanıcı `{user_id}` başarıyla engellendi. 🚫**")







# Kullanıcının engelini kaldırma komutu
@app.on_message(filters.command("unblock") & filters.user(OWNER_ID))
async def unblock_user_cmd(client: Client, message: Message):
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        else:
            user_id = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply("**Geçersiz komut kullanımı. Örnek: /unblock [Kullanıcı İD] veya yanıtla.**")
        return

    unblock_user(user_id)
    await message.reply(f"**Kullanıcı `{user_id}` başarıyla engeli kaldırıldı. ✅**")





# Günlük bonus
@app.on_message(filters.command(["bonus", "günlük"]) & filters.group)
async def daily_bonus(client: Client, message: Message):
    if is_user_blocked(message.from_user.id):
        await message.reply("**Üzgünüm, bu komutu kullanma yetkiniz engellendi.** 🚫")
        return
        
    try:
        current_time = datetime.now()
        
        
        user_bonus_data = collection.find_one({'user_id': message.from_user.id})
        if user_bonus_data:
            last_bonus_time = user_bonus_data['last_bonus_time']
            last_bonus_time = datetime.fromisoformat(last_bonus_time)
        else:
            last_bonus_time = None
        
        if last_bonus_time:
            
            elapsed_time = current_time - last_bonus_time
            remaining_time = bonus_interval_hours * 3600 - elapsed_time.total_seconds()
            
            if remaining_time > 0:
                minutes_remaining = int(remaining_time // 60)
                hours_remaining = int(minutes_remaining // 60)
                await message.reply(f"**Bu komutu tekrar kullanabilmek için {hours_remaining} saat {minutes_remaining % 60} dakika beklemeniz gerekmektedir.** ⌛")
                return

        
        user_id = message.from_user.id
        user_balances[user_id] += 40000
        save_balance(user_id, user_balances[user_id])

        
        if last_bonus_time:
            collection.update_one({'user_id': user_id}, {'$set': {'last_bonus_time': current_time.isoformat()}})
        else:
            collection.insert_one({'user_id': user_id, 'last_bonus_time': current_time.isoformat()})
            
        
        load_richest_users()
        save_richest_users()

        
        user_last_bonus_time[message.from_user.id] = current_time.timestamp()

        
        await message.reply(f"**Günlük bonus aldınız! 🚀 40.000 ₺ eklendi.**😎\n**Güncel bakiyeniz: `{user_balances[message.from_user.id]}` 💰**")
    except Exception as e:
        await message.reply(f"💰 **Günlük bonus verilirken bir hata oluştu.**\n🌹 **Bot'a start çektiğinizden emin olun.**")






@app.on_message(filters.new_chat_members)
async def welcome(client: Client, message: Message):
    for member in message.new_chat_members:
        if member.is_self:
            
            groups_collection.update_one(
                {"chat_id": message.chat.id},
                {
                    "$set": {
                        "chat_id": message.chat.id,
                        "chat_name": message.chat.title
                    }
                },
                upsert=True
            )

            
            await client.send_message(LOG_GROUP_ID, f"""
#YENİ GRUBA KATILDIM#

🤖 **Grup Adı:** {message.chat.title}
🆔 **Grup ID:** `{message.chat.id}`
""")






@app.on_message(filters.command("stat") & filters.user(OWNER_ID))
async def stat(client: Client, message: Message):
    user_count = users_collection.count_documents({})
    group_count = groups_collection.count_documents({})
    await message.reply(f"📊 **İstatistikler**\n\n👤 **Kullanıcı Sayısı:** `{user_count}`\n👥 **Grup Sayısı:** `{group_count}`")






@app.on_message(filters.command("duyuru") & filters.user(OWNER_ID))
async def duyuru(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply("Lütfen bir mesajı yanıtlayarak komutu kullanın.")
        return

    duyuru_mesaji = message.reply_to_message
    gruplar = groups_collection.find({})
    kullanicilar = users_collection.find({})
    
    basarili_grup = 0
    basarisiz_grup = 0
    basarili_kullanici = 0
    basarisiz_kullanici = 0

    
    for grup in gruplar:
        try:
            await client.forward_messages(grup["chat_id"], duyuru_mesaji.chat.id, duyuru_mesaji.id)
            basarili_grup += 1
        except Exception as e:
            basarisiz_grup += 1

    
    for kullanici in kullanicilar:
        try:
            await client.forward_messages(kullanici["user_id"], duyuru_mesaji.chat.id, duyuru_mesaji.id)
            basarili_kullanici += 1
        except Exception as e:
            basarisiz_kullanici += 1

    
    await message.reply(f"""**Duyuru başarıyla iletildi:** 📢
    
**Toplam Başarılı Grup:** `{basarili_grup}` - ✅
**Toplam Başarısız Grup:** `{basarisiz_grup}` - ❌
    
**Başarılı Kullanıcılar:** `{basarili_kullanici}` - ✅
**Başarısız Kullanıcılar:** `{basarisiz_kullanici}` - ❌
    """)






@app.on_message(filters.command("blockgrup") & filters.user(OWNER_ID))
async def block_group(client: Client, message: Message):
    if len(message.command) != 2:
        await message.reply_text("__Kullanım: /blockgrup <grup_id>__")
        return

    try:
        chat_id = int(message.command[1])
    except ValueError:
        await message.reply_text("__Geçerli bir grup ID'si girin.__")
        return

    # Grubu banla
    groups_collection.update_one({"group_id": chat_id}, {"$set": {"blocked": True}}, upsert=True)
    await message.reply_text(f"__Grup `{chat_id}` banlandı.__")
    
    try:
        await client.leave_chat(chat_id)
    except Exception as e:
        await message.reply_text(f"__Grubu terk ederken hata: {str(e)}__")





@app.on_message(filters.command("unblockgrup") & filters.user(OWNER_ID))
async def unblock_group(client: Client, message: Message):
    if len(message.command) != 2:
        await message.reply_text("__Kullanım: /unblockgrup <grup_id>__")
        return

    try:
        chat_id = int(message.command[1])
    except ValueError:
        await message.reply_text("__Geçerli bir grup ID'si girin.__")
        return

    # Grubun banını kaldır
    groups_collection.update_one({"group_id": chat_id}, {"$set": {"blocked": False}}, upsert=True)
    await message.reply_text(f"__Grup `{chat_id}` banı kaldırıldı.__")


@app.on_message(filters.new_chat_members)
async def welcome_new_group(client: Client, message: Message):
    chat_id = message.chat.id
    if groups_collection.find_one({"group_id": chat_id, "blocked": True}):
        await message.reply_text("Bu grup banlandı. Bot gruptan ayrılıyor.")
        await client.leave_chat(chat_id)
    else:
        await message.reply_text("__Merhaba! Slot botunu grubunuza eklediğiniz için teşekkürler. Komutlar için /komutlar yazabilirsiniz.__ 💫")


@app.on_message(filters.command("komutlar") & filters.group)
async def send_commands(client: Client, message: Message):
    await message.reply_text(komutlar)

@app.on_chat_member_updated()
async def monitor_group(client: Client, chat_member_updated: ChatMemberUpdated):
    if chat_member_updated.new_chat_member and chat_member_updated.new_chat_member.user.id == client.me.id:
        chat_id = chat_member_updated.chat.id
        if groups_collection.find_one({"group_id": chat_id, "blocked": True}):
            await client.send_message(chat_id, "__ℹ️ Bu grup banlandı. Eğer bunun bir hata olduğunu düşünüyorsanız t.me/goktuResmi 'ye bildirin.__")
            await client.leave_chat(chat_id)
            


# Gruba giriş mesajı `~~


@app.on_message(filters.new_chat_members, group=1)
async def hg(bot: Client, msg: Message):
    for new_user in msg.new_chat_members:
        if str(new_user.id) == str(BOT_ID):
            await msg.reply(
                f"""**📖 Hey , {msg.from_user.mention}\nMerhaba! Slot botunu grubunuza eklediğiniz için teşekkürler. Komutlar için /komutlar yazabilirsiniz**""",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⚙️ Daha Fazla Bilgi",
                                url=f"https://t.me/{app.me.username}?start",
                            )
                        ]
                    ]
                ),
            )
        elif str(new_user.id) == str(OWNER_ID):
            await msg.reply(f"{new_user.mention} ⚡️🫡\n\n🇹🇷 ʙᴏᴛᴜɴ sᴀʜɪʙɪ ɢʀᴜʙᴜɴᴜᴢᴀ ᴋᴀᴛɪʟᴅɪ !")
        

# Günlük bonus
async def daily_bonus():
    while True:
        try:
            for user_id in user_balances:
                user_balances[user_id] += 10000
            await asyncio.sleep(24 * 3600)  # 24 saat bekle
        except Exception as e:
            print(f"Günlük bonus alınırken hata oluştu: {e}")



# Günlük bonusu başlat
asyncio.ensure_future(daily_bonus())

# Botu başlat
app.run()
print("Bot Çalışıyor :)!")
