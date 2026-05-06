# 🎲 Bot D&D — Guía de Comandos

## ⚙️ Instalación local

1. Instalá las dependencias:
   ```
   pip install -r requirements.txt
   ```
2. Copiá `.env.example` como `.env` y completá:
   ```
   DISCORD_TOKEN=tu_token_aqui
   DATABASE_URL=postgresql://usuario:contraseña@host:puerto/nombre_db
   ```
3. Corré el bot:
   ```
   python main.py
   ```

---

## 🚀 Deploy en Railway (24/7 gratis)

1. Subir el proyecto a GitHub (sin el `.env`)
2. Entrar a [railway.app](https://railway.app) → nuevo proyecto
3. **Deploy from GitHub repo** → seleccionar el repo
4. **New → Database → PostgreSQL**
5. En Variables del servicio agregar:
   - `DISCORD_TOKEN` → tu token de Discord
   - `DATABASE_URL` → copiarlo desde PostgreSQL → Connect
6. ¡Railway despliega solo con cada push!

---

## 💰 Sistema monetario

| Moneda | Emoji | Equivalencia |
|--------|-------|-------------|
| Cobre  | 🟤    | base         |
| Plata  | 🥈    | 1 plata = 100 cobres |
| Oro    | 🥇    | 1 oro = 100 platas = 10.000 cobres |

**Formato de montos:** `5o 3p 10c` (podés omitir los que no uses)

---

## 🎲 Dados

| Comando | Descripción |
|---------|-------------|
| `!tirar 1d20` | Tira un d20 |
| `!tirar 2d6+3` | Tira 2d6 y suma 3 |
| `!tirar d4 d6 d8` | Varias tiradas a la vez (máx. 5) |
| `!ventaja [+mod]` | 2d20, toma el mayor |
| `!desventaja [+mod]` | 2d20, toma el menor |

---

## 💰 Economía

| Comando | Descripción |
|---------|-------------|
| `!monedas [@u]` | Ver tus monedas (o las de otro) |
| `!dar @u 5o 3p 10c` | Enviar monedas a otro jugador |
| `!historial` | Ver tus últimas 8 transacciones |
| `!ranking` | Top 10 jugadores más ricos |

---

## 🎒 Inventario

| Comando | Descripción |
|---------|-------------|
| `!inventario [@u]` | Ver inventario |
| `!dar_item @u cantidad item` | Dar ítem a otro jugador |

> La tienda global fue reemplazada por el inventario de NPCs. Usá `!npc <nombre>` para ver qué vende cada NPC y `!comprar_npc <NPC> <ítem>` para comprar.

---

## 🧙 NPCs

| Comando | Descripción |
|---------|-------------|
| `!npcs` | Ver todos los NPCs disponibles |
| `!npc <nombre>` | Hablar con un NPC y ver su inventario |
| `!comprar_npc <NPC> <ítem>` | Comprarle a un NPC |
| `!comprar_npc <NPC> <cantidad> <ítem>` | Comprar varias unidades |

---

## ⚔️ Personajes

Cada jugador puede tener **múltiples personajes** y alternar entre ellos.

| Comando | Descripción |
|---------|-------------|
| `!crear_personaje` | Abre formulario de creación (pide HP, maná y ficha en segundo paso) |
| `!personaje [@u]` | Ver ficha del personaje activo |
| `!mis_personajes` | Listar todos tus personajes |
| `!jugar_como <nombre>` | Cambiar personaje activo |
| `!actualizar_personaje` | Editar datos del personaje activo |
| `!ficha <url>` | Vincular ficha de Nivel20 |
| `!hp +10` / `!hp -5` | Curar o recibir daño |
| `!hp_temp 8` | Agregar HP temporales (absorben daño antes que el HP real) |
| `!mana +5` / `!mana -3` | Recuperar o gastar maná |
| `!condicion <estado>` | Agregar condición (envenenado, paralizado, etc.) |
| `!quitar_condicion <estado>` | Eliminar condición |

### HP Temporales
Los HP temporales funcionan como un escudo: el daño los consume primero. Si tenés 20/20 HP y recibís +8 temp, queda `20/20 (+8 temp)`. Al recibir 12 de daño, los 8 temp se absorben y solo bajás 4 de HP real → `16/20`.

---

## 🔐 Admin

| Comando | Descripción |
|---------|-------------|
| `!admin_dar @u 5o 2p` | Dar monedas |
| `!admin_quitar @u 5o` | Quitar monedas |
| `!admin_agregar_item @u N item` | Agregar ítem al inventario |
| `!admin_quitar_item @u N item` | Quitar ítem del inventario |
| `!admin_nivel @u N` | Cambiar nivel de personaje |
| `!admin_set_hp @u max [actual] [mana_max] [mana_actual]` | Configurar HP y maná |
| `!admin_hp_temp @u N` | Dar HP temporales a un jugador |
| `!admin_xp @u cantidad` | Dar/quitar XP |
| `!admin_condicion @u estado` | Aplicar condición |
| `!admin_quitar_condicion @u estado` | Quitar condición |

---

## 🔐 Admin NPCs

| Comando | Descripción |
|---------|-------------|
| `!npc_crear nombre \| desc \| img_url` | Crear NPC |
| `!npc_editar <NPC> <campo> \| <valor>` | Editar campo del NPC |
| `!npc_eliminar <nombre>` | Eliminar NPC |
| `!npc_inv <nombre>` | Ver inventario completo del NPC |
| `!npc_item_agregar NPC \| precio \| ítem \| [desc] \| [stock]` | Agregar ítem al NPC |
| `!npc_items_agregar <NPC>` + líneas | Carga masiva de ítems |
| `!npc_item_quitar NPC \| ítem` | Quitar ítem del NPC |
| `!npc_lista` | Listar todos los NPCs con IDs internos |

**Ejemplo crear NPC con inventario:**
```
!npc_crear Gausto | El mejor cocinero del reino | https://i.imgur.com/xxx.png
!npc_items_agregar Gausto
3o | Estofado Real | Delicioso guiso de la casa | 20
1o 5p | Pan de Centeno | Crujiente y esponjoso |
2o | Vino Élfico || 10
```
