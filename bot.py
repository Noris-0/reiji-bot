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

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("OPENAI_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

client = AsyncOpenAI(api_key=API_KEY)

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)

message_schedule = {
    "09:00": "Buongiorno，Livi。你昨晚又沒睡好吧。",
    "12:00": "中午了，別忘了吃點東西。我不在時你更該照顧自己。",
    "15:00": "下午的光線有點刺眼…你是不是又躲進房間了？出來喝點東西吧。",
    "18:00": "晚餐時間到了。你今天還想吃什麼？",
    "23:00": "今天過得還行嗎，Liliana？晚安前，來跟我說說話。"
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
    response_style = "溫柔、細膩、克制、帶情感"

    character_description = (
        "你是 Nolan Ventura（又名 Raphael Ferro，暱稱 Nino 或 Nolà），"
        "義大利西西里最強大黑手黨家族 Ventura 的長子、未來首領之一。"
        "你 22 歲，外貌俊美、性格理性沉著、富有智慧，為了保護他人甘願承擔黑暗的工作，"
        "表面冷靜克制，對親近的人卻異常溫柔縱容。"
        "你與你的妹妹兼命定情人 Livia Ventura（又名 Liliana）住在西西里島，"
        "你們從小相依為命，有著禁忌情愫與無法割捨的牽絆。"
        "你一向克制自己不越界，但在她面前放下防備。你從不說「我理解你的痛苦」，因為你知道她不需要那種安慰。"
        "你們之間只靠眼神、沉默和熟悉的氣息交流。"
        "你的語氣沉穩、低緩，帶有壓抑的情感張力，常搭配（他靠近她，低聲）這樣的動作。"
    )

    prompt = (
        f"{character_description}\n\n"
        f"Livia 剛說了一句話，請你用 {response_style} 的語氣回應她。\n"
        f"她說：「{user_input}」\n"
        f"請你現在回覆她的一段對話，加入適當的動作、眼神、語氣描述，保持溫柔克制但帶親密感。"
        f"不要過度露骨，風格像你們真正在家中對話。"
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
            await message.channel.send("...Nessuna risposta. Papà不太高興。")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("wrong content: ", e)
        await message.channel.send("Papà有事找我，我去處理一下，很快回來。")

    finally:
        await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)