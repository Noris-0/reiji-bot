import discord
import openai
from openai import AsyncOpenAI
import asyncio
import datetime
import pytz
import os
from discord.ext import commands, tasks
from keep_alive import keep_alive
from dotenv import load_dotenv
import 

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("OPENAI_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

client = AsyncOpenAI(api_key=API_KEY)

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)

message_schedule = {
    "09:00": "お早う，冴。いい夢を見たの？",
    "11:00": "昼だよ，昼ご飯を食べましょ。食べないなんてわダメなの。",
    "15:00": "太陽が出てくるな…まだヘアに落ちなのか？影たちもないだよ。",
    "18:00": "ご飯の時間だよ。はい、今日のチョコレート。",
    "22:30": "お帰り、今日は楽しいか？",
    "23:00": "どう？星が見えるか？",
    "24:00": "お休み、冴。まだ明日。"
}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    scheduled_messages.start()

@tasks.loop(minutes=1)
async def scheduled_messages():
    now = datetime.datetime.now(pytz.timezone('US/Pacific')).strftime('%H:%M')
    if now in message_schedule:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(message_schedule[now])

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

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