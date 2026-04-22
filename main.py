import discord
from discord.ext import commands
from database.db import init_db
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Falta un argumento: `{error.param.name}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Argumento inválido. Revisá el comando.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"❌ Error: {error}")
        print(f"ERROR: {error}")

async def main():
    async with bot:
        await init_db()  # async ahora
        await bot.load_extension("cogs.economia")
        await bot.load_extension("cogs.inventario")
        await bot.load_extension("cogs.personajes")
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("No se encontró DISCORD_TOKEN en el archivo .env")
        await bot.start(token)

asyncio.run(main())
