import discord
from discord.ext import commands


# BUG CORREGIDO: faltaban todos los comandos de NPCs en la ayuda.
# También se corrigió el footer de !tienda que decía el orden de argumentos viejo.

COMANDOS = {
    "🎲 Dados": [
        ("`!tirar 1d20`",         "Tira un d20"),
        ("`!tirar 2d6+3`",        "Tira 2d6 y suma 3"),
        ("`!tirar d4 d6 d8`",     "Varias tiradas a la vez"),
        ("`!ventaja [+mod]`",     "2d20, toma el mayor"),
        ("`!desventaja [+mod]`",  "2d20, toma el menor"),
    ],
    "💰 Economía": [
        ("`!monedas [@u]`",               "Ver tus monedas (o las de otro)"),
        ("`!dar @u 5o 3p 10c`",           "Enviar oro/plata/cobre"),
        ("`!historial`",                  "Ver tus últimas transacciones"),
        ("`!ranking`",                    "Top jugadores más ricos"),
    ],
    "🎒 Inventario": [
        ("`!inventario [@u]`",            "Ver inventario"),
        ("`!dar_item @u cantidad ítem`",  "Dar ítem a otro jugador"),
    ],
    "🧙 NPCs": [
        ("`!npcs`",                              "Ver todos los NPCs disponibles"),
        ("`!npc <nombre>`",                      "Hablar con un NPC y ver su inventario"),
        ("`!comprar_npc <NPC> <ítem>`",          "Comprarle a un NPC"),
        ("`!comprar_npc <NPC> <cantidad> <ítem>`", "Comprar varias unidades"),
    ],
    "⚔️ Personajes": [
        ("`!crear_personaje`",            "Crear un nuevo personaje (abre formulario)"),
        ("`!personaje [@u]`",             "Ver ficha del personaje activo"),
        ("`!mis_personajes`",             "Listar todos tus personajes"),
        ("`!jugar_como <nombre>`",        "Cambiar personaje activo"),
        ("`!actualizar_personaje`",       "Editar tu personaje activo"),
        ("`!ficha <url>`",                "Vincular ficha de Nivel20"),
        ("`!hp +10` / `!hp -5`",         "Curar o recibir daño"),
        ("`!hp_temp 8`",                  "Agregar HP temporales (absorben daño primero)"),
        ("`!mana +5` / `!mana -3`",      "Recuperar o gastar maná"),
        ("`!condicion <estado>`",         "Agregar condición (ej: envenenado)"),
        ("`!quitar_condicion <estado>`",  "Eliminar condición"),
    ],
    "🔐 Admin": [
        ("`!admin_dar @u 5o 2p`",                      "Dar monedas"),
        ("`!admin_quitar @u 5o`",                      "Quitar monedas"),
        ("`!admin_agregar_item @u N ítem`",            "Agregar ítem a jugador"),
        ("`!admin_quitar_item @u N ítem`",             "Quitar ítem de jugador"),
        ("`!admin_nivel @u N`",                        "Cambiar nivel"),
        ("`!admin_set_hp @u max [actual] [mana_max]`", "Configurar HP y maná"),
        ("`!admin_hp_temp @u N`",                      "Dar HP temporales a un jugador"),
        ("`!admin_xp @u cantidad`",                    "Dar XP"),
        ("`!admin_condicion @u estado`",               "Aplicar condición"),
        ("`!admin_quitar_condicion @u estado`",        "Quitar condición"),
    ],
    "🔐 Admin NPCs": [
        ("`!npc_crear nombre | desc | img_url`",                        "Crear NPC"),
        ("`!npc_editar <NPC> <campo> | <valor>`",                       "Editar campo del NPC"),
        ("`!npc_eliminar <nombre>`",                                    "Eliminar NPC"),
        ("`!npc_inv <nombre>`",                                         "Ver inventario del NPC"),
        ("`!npc_item_agregar NPC | precio | ítem | desc | stock`",      "Agregar ítem a NPC"),
        ("`!npc_items_agregar <NPC>` + líneas",                         "Carga masiva de ítems"),
        ("`!npc_item_quitar NPC | ítem`",                               "Quitar ítem de NPC"),
        ("`!npc_lista`",                                                "Listar todos los NPCs"),
    ],
}


class Ayuda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.remove_command("help")

    @commands.command(name="ayuda", aliases=["help", "h"],
                      help="Muestra esta guía de comandos.")
    async def ayuda(self, ctx, categoria: str = None):
        if categoria:
            cat_lower = categoria.lower()
            for titulo, cmds in COMANDOS.items():
                if cat_lower in titulo.lower():
                    embed = discord.Embed(title=titulo, color=discord.Color.blurple())
                    for cmd, desc in cmds:
                        embed.add_field(name=cmd, value=desc, inline=False)
                    await ctx.send(embed=embed)
                    return
            await ctx.send(f"❌ Categoría `{categoria}` no encontrada.")
            return

        embed = discord.Embed(
            title="📖 Guía de comandos — Bot D&D",
            description="Usá `!ayuda <categoría>` para ver detalles.\nPrefijo: **`!`**",
            color=discord.Color.dark_gold()
        )
        for titulo, cmds in COMANDOS.items():
            resumen = "\n".join(f"{cmd}" for cmd, _ in cmds[:3])
            if len(cmds) > 3:
                resumen += f"\n*…y {len(cmds)-3} más*"
            embed.add_field(name=titulo, value=resumen, inline=False)

        embed.set_footer(text="¡A rolear! 🐉")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Ayuda(bot)) 