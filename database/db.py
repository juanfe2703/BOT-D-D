import asyncpg
import os

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("No se encontró DATABASE_URL en el archivo .env")
        _pool = await asyncpg.create_pool(database_url)
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            -- ── Jugadores y economía ─────────────────────────────────────────
            CREATE TABLE IF NOT EXISTS jugadores (
                id     TEXT    PRIMARY KEY,
                cobre  INTEGER DEFAULT 0,
                plata  INTEGER DEFAULT 0,
                oro    INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS inventario (
                id         SERIAL  PRIMARY KEY,
                jugador_id TEXT    NOT NULL REFERENCES jugadores(id),
                item       TEXT    NOT NULL,
                cantidad   INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS personajes (
                id         SERIAL  PRIMARY KEY,
                jugador_id TEXT    NOT NULL REFERENCES jugadores(id),
                nombre     TEXT    NOT NULL,
                nick       TEXT,
                nivel      INTEGER DEFAULT 1,
                clase      TEXT,
                raza       TEXT,
                link_ficha TEXT,
                hp_max     INTEGER DEFAULT 0,
                hp_actual  INTEGER DEFAULT 0,
                xp         INTEGER DEFAULT 0,
                activo     BOOLEAN DEFAULT TRUE,
                UNIQUE (jugador_id, nombre)
            );

            CREATE TABLE IF NOT EXISTS transacciones (
                id          SERIAL    PRIMARY KEY,
                emisor_id   TEXT,
                receptor_id TEXT,
                tipo        TEXT      NOT NULL,
                cobre       INTEGER   DEFAULT 0,
                plata       INTEGER   DEFAULT 0,
                oro         INTEGER   DEFAULT 0,
                detalle     TEXT,
                creado_en   TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS tienda (
                id           SERIAL  PRIMARY KEY,
                nombre       TEXT    NOT NULL UNIQUE,
                descripcion  TEXT,
                precio_cobre INTEGER DEFAULT 0,
                precio_plata INTEGER DEFAULT 0,
                precio_oro   INTEGER DEFAULT 0,
                stock        INTEGER DEFAULT -1,
                activo       BOOLEAN DEFAULT TRUE
            );

            CREATE TABLE IF NOT EXISTS condiciones (
                id           SERIAL    PRIMARY KEY,
                personaje_id INTEGER   NOT NULL REFERENCES personajes(id),
                condicion    TEXT      NOT NULL,
                creado_en    TIMESTAMP DEFAULT NOW()
            );

            -- ── NPCs ─────────────────────────────────────────────────────────
            CREATE TABLE IF NOT EXISTS npcs (
                id                  SERIAL    PRIMARY KEY,
                nombre              TEXT      NOT NULL UNIQUE,
                descripcion         TEXT      DEFAULT '',
                imagen_url          TEXT      DEFAULT '',
                dialogo_bienvenida  TEXT      DEFAULT '',
                dialogo_venta       TEXT      DEFAULT '',
                dialogo_sin_stock   TEXT      DEFAULT '',
                activo              BOOLEAN   DEFAULT TRUE,
                creado_en           TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS npc_inventario (
                id            SERIAL   PRIMARY KEY,
                npc_id        INTEGER  NOT NULL REFERENCES npcs(id) ON DELETE CASCADE,
                item          TEXT     NOT NULL,
                descripcion   TEXT     DEFAULT '',
                precio_cobre  INTEGER  DEFAULT 0,
                precio_plata  INTEGER  DEFAULT 0,
                precio_oro    INTEGER  DEFAULT 0,
                stock         INTEGER  DEFAULT -1,
                activo        BOOLEAN  DEFAULT TRUE,
                UNIQUE (npc_id, item)
            );
        """)
    print("✅ Base de datos inicializada")