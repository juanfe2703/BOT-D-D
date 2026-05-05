import discord
from discord.ext import commands
from database.db import init_db
import asyncio
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    print(f"   Servidores: {len(bot.guilds)}")


@bot.event
async def on_command_error(ctx, error):
    # Ignorar errores que ya manejó un handler local dentro de un cog
    if hasattr(ctx.command, "on_error"):
        return

    # Ignorar si el cog tiene su propio cog_command_error
    if ctx.cog and commands.Cog.cog_command_error is not type(ctx.cog).cog_command_error:
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Falta el argumento `{error.param.name}`. Usá `!ayuda` para ver cómo usar el comando.")

    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Argumento inválido. Revisá el comando con `!ayuda`.")

    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("🔒 No tenés permisos de administrador para usar ese comando.")

    elif isinstance(error, commands.CommandNotFound):
        pass  # No hacer nada si el comando no existe

    elif isinstance(error, commands.CommandInvokeError):
        # BUG CORREGIDO: antes mandaba el error al chat de Discord con ctx.send().
        # Los errores inesperados NUNCA deben mostrarse en el chat — solo en la terminal.
        # Así el jugador no ve stack traces y vos sí los ves donde corresponde.
        original = error.original
        print(f"\n[ERROR] Comando: !{ctx.command} | Usuario: {ctx.author}")
        print(f"[ERROR] {type(original).__name__}: {original}")
        traceback.print_exception(type(original), original, original.__traceback__)

    else:
        print(f"\n[ERROR] {type(error).__name__}: {error}")
        traceback.print_exception(type(error), error, error.__traceback__)


async def main():
    async with bot:
        await init_db()
        cogs = [
            "cogs.economia",
            "cogs.inventario",
            "cogs.personajes",
            "cogs.admin",
            "cogs.dados",
            "cogs.ayuda",
            "cogs.npcs",
            "cogs.admin_npcs",
        ]
        for cog in cogs:
            await bot.load_extension(cog)
            print(f"  ✔ {cog} cargado")

        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("No se encontró DISCORD_TOKEN en el archivo .env")
        await bot.start(token)


asyncio.run(main())