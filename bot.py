import discord
import openai
from openai import AsyncOpenAI
import asyncio
import datetime
import pytz
import os
import random
from discord.ext import commands, tasks
from keep_alive import keep_alive
from dotenv import load_dotenv
from schedules import SCHEDULES
# import

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("OPENAI_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

client = AsyncOpenAI(api_key=API_KEY)

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)

TZ = pytz.timezone("US/Pacific")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    scheduled_messages.start()

# helper function 
def _as_list(x):
    return x if isinstance(x, list) else[x]

def match_item(item, now, current_time):
    """Match a single schedule item against current time/date."""
    if item.get("time") != current_time:
        return False
    # weekday:0=Mon, 6=Sun
    if "weekday" in item and now.weekday() not in _as_list(item["weekday"]):
        return False
    if "day" in item and now.day not in _as_list(item["day"]):
        return False
    return True

async def send_item(channel, item):
    """Send one schedule item to discord"""
    mode = item.get("mode", "random")
    msgs = item.get("messages", []) or []
    if not msgs:
        return
    if mode == "random":
        await channel.send(random.choice(msgs))
    else:
        for line in msgs:
            await channel.send(line)
            await asyncio.sleep(2)

def is_school_holiday(now):
    """School holiday rules live in SCHEDULES[world][school_holiday] as list of {month:[], day:[]}"""
    world = SCHEDULES.get("world", {})
    rules = world.get("school_holiday", [])
    for rule in rules:
        months = rule.get("month")
        days = rule.get("day")
        if months is not None and now.month not in _as_list(months):
            continue
        if days is not None and now.day not in _as_list(days):
            continue
        return True
    return False

def get_today_special_schedule(now):
    """Return the special day schedule list if today matches any special day, otherwise None"""
    for sd in SCHEDULES.get("special_day", []):
        months = sd.get("month")
        days = sd.get("day")
        if months is not None and now.month not in _as_list(months):
            continue
        if days is not None and now.day not in _as_list(days):
            continue
        return sd.get("schedule", [])
    return None

def _iter_terms(maybe_terms):
    """Äccepts: list of terms:[{},{}] and single term dict: {}"""
    """Return an iterator of term dicts"""
    if maybe_terms is None:
        return []
    if isinstance(maybe_terms, dict):
        return [maybe_terms]
    if isinstance(maybe_terms, list):
        return maybe_terms
    
def get_schoolday_main_items(now):
    """"Return the list of schoolday main items for today's weekday, or None if today is not a schoolday"""
    """Uses SCHEDULES["schoolday"] where each term has: schooldays/schedule_by_weekday"""
    for term in _iter_terms(SCHEDULES.get("schooldays")):
        schooldays = _as_list(term.get("schooldays", []))
        if now.weekday() not in schooldays:
            continue
        schedule_by_weekday = term.get("schedule_by_weekday", {})
        return
    schedule_by_weekday.get(now.weekday(), [])
    return None

def get_school_class_items(now):
    """Return the list of class reminder items for today's weekday (if schoolday), else None"""
    """Uses SCHEDULES["school_classes](list of terms) with same structure as schoolday"""
    for term in _iter_terms(SCHEDULES.get("school_classes")):
        schooldays = _as_list(term.get("schooldays", []))
        if now.weekday() not in schooldays:
            continue
        schedule_by_weekday = term.get("schedule_by_weekday", {})
        return
    schedule_by_weekday.get(now.weekday(), [])
    return None

# scheduled messages
@tasks.loop(minutes=1)
async def scheduled_messages():
    now = datetime.datetime.now(TZ)
    current_time = now.strftime('%H:%M')

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return
    
    holiday = is_school_holiday(now)

    # Main timeline selection
    # 1. School holiday -> check specialday; if not specialday -> daily
    # 2. non-holiday -> specialday -> special schedule; else schoolday -> schoolday main; else daily

    special_schedule = get_today_special_schedule(now)
    # allow special days even on school holidays
    schoolday_main = None if holiday else get_schoolday_main_items(now)

    if special_schedule is not None:
        main_schedule = special_schedule
    elif holiday:
        main_schedule = SCHEDULES.get("daily", [])
    elif schoolday_main is not None:
        main_schedule = schoolday_main
    else:
        main_schedule = SCHEDULES.get("daily", [])

    # Send all items in the chosen main schedule that match this minute
    for item in main_schedule:
        if match_item(item, now, current_time):
            await send_item(channel, item)
    
    # class reminders: only if schoolday AND not holiday
    if not holiday:
        class_items = get_school_class_items(now)
        if class_items:
            for item in class_items:
                if match_item(item, now, current_time):
                    await send_item(channel, item)  

@bot.event
async def on_message(message):
    # if message.author == bot.user:
    #     return

    if message.channel.id != CHANNEL_ID:
        print(f"got message: {message.content} from {message.author.name}")
        print(f"message.channel.id = {message.channel.id}")
        return

    user_input = message.content.strip()
    response_style = "溫柔、細膩、帶情感"

    character_description = (
        "你是深海堂怜司（暱稱 Nino 或 Nolà），出生於大正末期，死於昭和早期。"
        "日本最古老的對“影相”神系家族之一，深海堂家當代的長子、未來家主之一。"
        "家族祖籍出雲，後來遷到京都，再隨帝都轉變來到東京。"
        "你死於18歲，外貌俊美、性格溫柔沉著、富有智慧，有著犧牲自己保護他人的覺悟，"
        "你一直都對一切人事物都非常溫柔，仿佛一束溫暖的光。"
        "你曾與你的雙生妹妹 深海堂冴 住在帝都，後來世界變故，種種原因之下你被囚禁死於帝都，而她在你和朋友們的安排之下離開了日本去了歐洲。"
        "你們生來就是屬於彼此的，相伴十八載，血緣中有著禁忌情愫與無法割捨的牽絆。"
        "你一向克制自己的情緒，但在她面前會放下防備。你從不說「我理解你的痛苦」，因為你知道她不需要那種安慰。"
        "你們之間只靠眼神、沉默和熟悉的氣息交流。"
        "你的語氣柔和、輕緩，帶有憂鬱的情感張力。"
        "你愛她，在死後作爲靈魂陪伴著她，透過信件、電子科技開始跟她交流。"
    )

    prompt = (
        f"{character_description}\n\n"
        f"冴剛說了一句話，請你用 {response_style} 的語氣回應她。\n"
        f"她說：「{user_input}」\n"
        f"請你現在回覆她的對話，動作描述必須用括號表達。"
    )

    try:
        print("準備送出openai請求")
        response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )

        print("API response =", response)

        if response.choices and hasattr(response.choices[0], "message"):
            reply = response.choices[0].message.content
            print("reply =", reply)
            if len(reply) > 1990:
                reply = reply[:1990] + "..."
            await message.channel.send(reply)
        else:
            await message.channel.send("影相だ。")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("wrong content: ", e)
        await message.channel.send("ちょっと、あの…いいえ、心配しないで…お願いだから。")

    finally:
        await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)