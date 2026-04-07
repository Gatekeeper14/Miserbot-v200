import os
import random
import asyncio
import threading
from datetime import datetime
from io import BytesIO
import psycopg2
from flask import Flask, request
from telegram import (
Update,
ReplyKeyboardMarkup,
InlineKeyboardMarkup,
InlineKeyboardButton,
KeyboardButton
)
from telegram.ext import (
Application,
CommandHandler,
MessageHandler,
CallbackQueryHandler,
ContextTypes,
filters
)
from openai import OpenAI

BOT_TOKEN=os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL=os.environ.get("DATABASE_URL")
OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY")
OWNER_ID=int(os.environ.get("OWNER_ID","0"))

openai_client=OpenAI(api_key=OPENAI_API_KEY)

CASHAPP="https://cash.app/$BAZRAGOD"
PAYPAL="https://paypal.me/bazragod1"

app=Flask(__name__)
WEBHOOK_PATH="/webhook"

# =================================
# FULL MUSIC CATALOG
# =================================

SEED_SONGS=[

("Chibonge Remix Rap Version","CQACAgEAAxkBAAOtadMWVB7xX8ss7Nkp6neA0L7gbU0AAvQIAAI1Z5hGYMUV7Mozbyw7BA"),
("Natural Pussy (Tie Mi)","CQACAgEAAxkBAAO1adMZtjgiRqYxrOFbE3KOCNxVcxQAAvgIAAI1Z5hGm8QmWqNIojg7BA"),
("Fraid Ah Yuh","CQACAgEAAxkBAAO3adMZ_P5y2OoXlyY0XpO_fiPiahMAAvkIAAI1Z5hGgMZ1tOmyhjA7BA"),
("Mini 14 Raw","CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
("Boom Boom","CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
("Summertime","CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA"),
("Mini 14 HD Mix","CQACAgEAAxkBAAPBadMcgWIUbXd6lfNjIt8C_SMhpz8AAv4IAAI1Z5hGrA8jfr5073A7BA"),
("Carry Guh Bring Come","CQACAgEAAxkBAAPFadMdgVBA0MIwyLNyU8mO5-djfawAAgQJAAI1Z5hGYmzehzRMIZY7BA"),
("Trapp Master","CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA"),
("Gunman","CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA"),
("Impeccable","CQACAgEAAxkBAAPRadMgsX9xJh3boHp64jA1-sVPC80AAgsJAAI1Z5hGIlCi8cg5E_k7BA"),
("Fear","CQACAgEAAxkBAAPTadMhUx8wc0RTafeXlg63snEcu7sAAgwJAAI1Z5hG5VCl-ykMd8I7BA"),
("Bubble Fi Mi","CQACAgEAAxkBAAPPadMgBMh10TStncJQXpkyD0mJYM8AAgoJAAI1Z5hG10QJbSDmTyM7BA"),
("Big Fat Matic","CQACAgEAAxkBAAPNadMfiOZJNeE3Eihp-r-olvpfzWIAAgkJAAI1Z5hGaNvyiVRhwEw7BA"),
("Mi Alone","CQACAgEAAxkBAAPJadMeaMExYAvnDv8gswXyUgOMwpsAAgcJAAI1Z5hGxeKB46IBYZg7BA"),
("Real Gold","CQACAgEAAxkBAAO9adMbBDzajJrOcGNb6gVyZmjEXTYAAvwIAAI1Z5hGr3nvGz4AAYjbOwQ"),
("Facebook Lust","CQACAgEAAxkBAAOzadMY-pj_rWBB5wrRP6Nfymv4q6EAAvcIAAI1Z5hG4SGuftZqhPY7BA"),
("BAZRAGOD & Sara Charismata","CQACAgEAAxkBAAICWGnUbUMJb5_1Baajef0VQFq0HMCaAAIFBgACEbKpRluYDh3M8F57OwQ")

]

# =================================
# DATABASE
# =================================

def db():
 return psycopg2.connect(DATABASE_URL)

def init_db():

 conn=db()
 cur=conn.cursor()

 cur.execute("""
 CREATE TABLE IF NOT EXISTS songs(
 id SERIAL PRIMARY KEY,
 title TEXT,
 file_id TEXT)
 """)

 cur.execute("""
 CREATE TABLE IF NOT EXISTS purchases(
 id SERIAL PRIMARY KEY,
 telegram_id BIGINT,
 item TEXT,
 price INT,
 status TEXT DEFAULT 'pending')
 """)

 cur.execute("""
 CREATE TABLE IF NOT EXISTS fans(
 telegram_id BIGINT PRIMARY KEY,
 points INT DEFAULT 0,
 invites INT DEFAULT 0,
 referrer BIGINT)
 """)

 cur.execute("""
 CREATE TABLE IF NOT EXISTS fan_locations(
 telegram_id BIGINT PRIMARY KEY,
 latitude FLOAT,
 longitude FLOAT)
 """)

 cur.execute("SELECT COUNT(*) FROM songs")

 if cur.fetchone()[0]==0:
  cur.executemany("INSERT INTO songs(title,file_id) VALUES(%s,%s)",SEED_SONGS)

 conn.commit()
 conn.close()

# =================================
# AI RADIO DJ
# =================================

async def ai_dj(context,chat_id,text):

 try:

  response=openai_client.audio.speech.create(
  model="tts-1",
  voice="onyx",
  input=text
  )

  audio_file=BytesIO(response.content)
  audio_file.name="dj.ogg"

  await context.bot.send_voice(chat_id=chat_id,voice=audio_file)

 except:
  pass

# =================================
# MENU
# =================================

menu=ReplyKeyboardMarkup([
["🎵 Music","📻 Radio"],
["🛒 Music Store","👕 Merch"],
["⭐ My Points","👥 Refer"],
["🏆 Leaderboard","📡 Tour Radar"],
["📍 Share Location"]
],resize_keyboard=True)

# =================================
# START
# =================================

async def start(update,context):

 uid=update.effective_user.id
 args=context.args
 ref=None

 if args:
  try:
   ref=int(args[0])
  except:
   pass

 conn=db()
 cur=conn.cursor()

 cur.execute("INSERT INTO fans(telegram_id,referrer) VALUES(%s,%s) ON CONFLICT DO NOTHING",(uid,ref))

 if ref:
  cur.execute("UPDATE fans SET invites=invites+1 WHERE telegram_id=%s",(ref,))
  cur.execute("UPDATE fans SET points=points+10 WHERE telegram_id=%s",(ref,))

 conn.commit()
 conn.close()

 await update.message.reply_text("👑 Welcome to BAZRAGOD platform",reply_markup=menu)

# =================================
# MUSIC
# =================================

async def music(update,context):

 conn=db()
 cur=conn.cursor()

 cur.execute("SELECT id,title FROM songs ORDER BY id")
 songs=cur.fetchall()

 conn.close()

 keyboard=[]
 for s in songs:
  keyboard.append([InlineKeyboardButton(s[1],callback_data=f"song:{s[0]}")])

 await update.message.reply_text("🎧 BAZRAGOD MUSIC",reply_markup=InlineKeyboardMarkup(keyboard))

async def play_song(update,context):

 q=update.callback_query
 await q.answer()

 sid=int(q.data.split(":")[1])

 conn=db()
 cur=conn.cursor()

 cur.execute("SELECT title,file_id FROM songs WHERE id=%s",(sid,))
 song=cur.fetchone()

 conn.close()

 if song:
  await q.message.reply_audio(song[1],caption=song[0])

# =================================
# RADIO WITH AI DJ
# =================================

async def radio(update,context):

 conn=db()
 cur=conn.cursor()

 cur.execute("SELECT title,file_id FROM songs ORDER BY RANDOM() LIMIT 1")
 song=cur.fetchone()

 conn.close()

 if song:

  dj_line=f"You are now listening to BazraGod Radio. Next track {song[0]}"

  await ai_dj(context,update.effective_user.id,dj_line)

  await update.message.reply_audio(song[1],caption=f"📻 BazraGod Radio\n{song[0]}")

# =================================
# STORE
# =================================

async def store(update,context):

 keyboard=InlineKeyboardMarkup([
[InlineKeyboardButton("Single Track $5",callback_data="buy_single")],
[InlineKeyboardButton("Bundle 7 Songs $20",callback_data="buy_bundle")],
[InlineKeyboardButton("VIP Album $500",callback_data="buy_album")]
])

 await update.message.reply_text("🛒 Music Store",reply_markup=keyboard)

# =================================
# MERCH
# =================================

async def merch(update,context):

 keyboard=InlineKeyboardMarkup([
[InlineKeyboardButton("T-Shirt $50",callback_data="merch_shirt")],
[InlineKeyboardButton("Pullover $150",callback_data="merch_pull")]
])

 await update.message.reply_text("👕 Parish 14 Merch",reply_markup=keyboard)

# =================================
# PURCHASE
# =================================

async def purchase(update,context):

 q=update.callback_query
 await q.answer()

 items={
 "buy_single":("Single Song",5),
 "buy_bundle":("Bundle Pack",20),
 "buy_album":("VIP Album",500),
 "merch_shirt":("Parish 14 Shirt",50),
 "merch_pull":("Parish 14 Pullover",150)
 }

 item,price=items[q.data]

 conn=db()
 cur=conn.cursor()

 cur.execute("INSERT INTO purchases(telegram_id,item,price) VALUES(%s,%s,%s) RETURNING id",(q.from_user.id,item,price))

 pid=cur.fetchone()[0]

 conn.commit()
 conn.close()

 keyboard=InlineKeyboardMarkup([
[InlineKeyboardButton("Pay CashApp",url=CASHAPP)],
[InlineKeyboardButton("Pay PayPal",url=PAYPAL)]
])

 await q.message.reply_text(f"Order #{pid}\n{item}\nPrice ${price}",reply_markup=keyboard)

# =================================
# ADMIN CONFIRM + DOWNLOAD UNLOCK
# =================================

async def confirm(update,context):

 if update.effective_user.id!=OWNER_ID:
  return

 pid=context.args[0]

 conn=db()
 cur=conn.cursor()

 cur.execute("UPDATE purchases SET status='paid' WHERE id=%s RETURNING telegram_id,item",(pid,))
 row=cur.fetchone()

 conn.commit()
 conn.close()

 if row:

  uid,item=row

  await context.bot.send_message(uid,f"✅ Payment confirmed for {item}")

# =================================
# LEADERBOARD
# =================================

async def leaderboard(update,context):

 conn=db()
 cur=conn.cursor()

 cur.execute("SELECT telegram_id,points FROM fans ORDER BY points DESC LIMIT 10")
 rows=cur.fetchall()

 conn.close()

 text="🏆 Leaderboard\n\n"

 for i,r in enumerate(rows):
  text+=f"{i+1}. {r[0]} — {r[1]} pts\n"

 await update.message.reply_text(text)

# =================================
# TOUR RADAR
# =================================

async def radar(update,context):

 conn=db()
 cur=conn.cursor()

 cur.execute("SELECT COUNT(*) FROM fan_locations")
 total=cur.fetchone()[0]

 conn.close()

 await update.message.reply_text(f"📡 Tour Radar\nFans mapped: {total}")

# =================================
# LOCATION
# =================================

async def location_prompt(update,context):

 kb=ReplyKeyboardMarkup([[KeyboardButton("Send Location",request_location=True)]],resize_keyboard=True,one_time_keyboard=True)

 await update.message.reply_text("Share your location",reply_markup=kb)

async def location(update,context):

 loc=update.message.location

 conn=db()
 cur=conn.cursor()

 cur.execute("""
 INSERT INTO fan_locations(telegram_id,latitude,longitude)
 VALUES(%s,%s,%s)
 ON CONFLICT (telegram_id)
 DO UPDATE SET latitude=%s,longitude=%s
 """,(update.effective_user.id,loc.latitude,loc.longitude,loc.latitude,loc.longitude))

 conn.commit()
 conn.close()

 await update.message.reply_text("Location saved")

# =================================
# ROUTER
# =================================

async def router(update,context):

 t=update.message.text

 if t=="🎵 Music":
  await music(update,context)

 elif t=="📻 Radio":
  await radio(update,context)

 elif t=="🛒 Music Store":
  await store(update,context)

 elif t=="👕 Merch":
  await merch(update,context)

 elif t=="⭐ My Points":
  await points(update,context)

 elif t=="👥 Refer":
  await refer(update,context)

 elif t=="🏆 Leaderboard":
  await leaderboard(update,context)

 elif t=="📡 Tour Radar":
  await radar(update,context)

 elif t=="📍 Share Location":
  await location_prompt(update,context)

# =================================
# TELEGRAM APP
# =================================

telegram_app=Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start",start))
telegram_app.add_handler(CommandHandler("confirm",confirm))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,router))
telegram_app.add_handler(CallbackQueryHandler(play_song,pattern="song:"))
telegram_app.add_handler(CallbackQueryHandler(purchase))
telegram_app.add_handler(MessageHandler(filters.LOCATION,location))

# =================================
# LOOP
# =================================

loop=asyncio.new_event_loop()

def start_bot():
 asyncio.set_event_loop(loop)
 loop.run_until_complete(telegram_app.initialize())
 loop.run_until_complete(telegram_app.start())
 loop.run_forever()

threading.Thread(target=start_bot,daemon=True).start()

# =================================
# WEBHOOK
# =================================

@app.route(WEBHOOK_PATH,methods=["POST"])
def webhook():

 data=request.get_json(force=True)
 update=Update.de_json(data,telegram_app.bot)

 asyncio.run_coroutine_threadsafe(
 telegram_app.process_update(update),
 loop
 )

 return "ok"

@app.route("/")
def health():
 return "MISERBOT ONLINE"

# =================================
# MAIN
# =================================

if __name__=="__main__":

 init_db()

 app.run(
 host="0.0.0.0",
 port=int(os.environ.get("PORT",8080))
 )
