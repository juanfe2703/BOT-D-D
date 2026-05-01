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

El sistema maneja tres denominaciones:

| Moneda | Emoji | Equivalencia |
|--------|-------|-------------|
| Cobre  | 🟤    | base         |
| Plata  | 🥈    | 1 plata = 100 cobres |
| Oro    | 🥇    | 1 oro = 100 platas = 10.000 cobres |

**Formato de montos en comandos:** `5o 3p 10c` (oro/plata/cobre, puedes omitir los que no uses)

---

## 🎲 Dados

| Comando | Descripción |
|---------|-------------|
| `!tirar 1d20` | Tira un d20 |
| `!tirar 2d6+3` | Tira 2d6 y suma 3 |
| `!tirar d4 d6 d8` | Varias tiradas a la vez (máx. 5) |
| `!ventaja [+mod]` | 2d20, toma el mayor |
| `!desventaja [+mod]` | 2d20, toma el menor |

Los críticos (20) y pifias (1) en d20 se marcan con ✨ y 💀.

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
| `!tienda` | Ver productos disponibles |
| `!comprar [cantidad] <item>` | Comprar de la tienda |

---

## ⚔️ Personajes

Cada jugador puede tener **múltiples personajes** y alternar entre ellos.

| Comando | Descripción |
|---------|-------------|
| `!crear_personaje` | Crea un nuevo personaje (modal) |
| `!personaje [@u]` | Ver ficha del personaje activo |
| `!mis_personajes` | Listar todos tus personajes |
| `!jugar_como <nombre>` | Cambiar personaje activo |
| `!actualizar_personaje` | Editar personaje activo (modal) |
| `!ficha <url>` | Vincular ficha de Nivel20 |
| `!hp +10` / `!hp -5` | Modificar HP del personaje activo |
| `!condicion <estado>` | Agregar condición (envenenado, etc.) |
| `!quitar_condicion <estado>` | Eliminar condición |

---

## 🔐 Admin

| Comando | Descripción |
|---------|-------------|
| `!admin_dar @u 5o 2p` | Dar monedas |
| `!admin_quitar @u 5o` | Quitar monedas |
| `!admin_agregar_item @u N item` | Agregar ítem al inventario |
| `!admin_quitar_item @u N item` | Quitar ítem del inventario |
| `!tienda_agregar precio \| nombre \| desc \| stock` | Agregar producto |
| `!tienda_quitar <nombre>` | Quitar producto |
| `!admin_nivel @u N` | Cambiar nivel de personaje |
| `!admin_set_hp @u max [actual]` | Configurar HP |
| `!admin_xp @u cantidad` | Dar/quitar XP |
| `!admin_condicion @u estado` | Aplicar condición |
| `!admin_quitar_condicion @u estado` | Quitar condición |

**Ejemplo tienda:**
```
!tienda_agregar 5o | Espada Larga | Una espada de acero bien afilada | 10
!tienda_agregar 2p 50c | Poción de Curación | Restaura 2d4+2 HP
```
