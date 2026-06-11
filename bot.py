import os
import random
import sqlite3
import asyncio
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Su Railway il token deve arrivare via Environment Variables/Secrets.
# Manteniamo .env solo per sviluppo locale.
try:
    load_dotenv()
except Exception:
    pass

# Preferisci DISCORD_TOKEN (Railway). Fallback per compatibilità.
TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
PREFIX = os.getenv("PREFIX", "!")


DB_PATH = os.path.join(os.path.dirname(__file__), "economy.sqlite3")

# -----------------------------
# Database helpers (economy unica)
# -----------------------------

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            coins INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cooldowns (
            user_id TEXT NOT NULL,
            command TEXT NOT NULL,
            cooldown_until INTEGER NOT NULL,
            PRIMARY KEY (user_id, command)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory (
            user_id TEXT NOT NULL,
            item_key TEXT NOT NULL,
            qty INTEGER NOT NULL,
            PRIMARY KEY (user_id, item_key)
        )
        """
    )

    conn.commit()
    conn.close()


def ensure_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (str(user_id),))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO users(user_id, coins, created_at) VALUES(?, 0, strftime('%s','now'))",
            (str(user_id),),
        )
        conn.commit()
    conn.close()


def get_coins(user_id: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT coins FROM users WHERE user_id=?", (str(user_id),))
    row = cur.fetchone()
    conn.close()
    return int(row["coins"]) if row else 0


def add_coins(user_id: int, amount: int):
    ensure_user(user_id)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET coins = coins + ? WHERE user_id=?",
        (amount, str(user_id)),
    )
    conn.commit()
    conn.close()


def set_coins(user_id: int, amount: int):
    ensure_user(user_id)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET coins=? WHERE user_id=?",
        (amount, str(user_id)),
    )
    conn.commit()
    conn.close()


def get_inventory(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT item_key, qty FROM inventory WHERE user_id=?", (str(user_id),))
    rows = cur.fetchall()
    conn.close()
    return {r["item_key"]: int(r["qty"]) for r in rows}


def add_item(user_id: int, item_key: str, qty: int):
    ensure_user(user_id)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT qty FROM inventory WHERE user_id=? AND item_key=?",
        (str(user_id), item_key),
    )
    row = cur.fetchone()
    if row is None:
        cur.execute(
            "INSERT INTO inventory(user_id, item_key, qty) VALUES(?,?,?)",
            (str(user_id), item_key, qty),
        )
    else:
        cur.execute(
            "UPDATE inventory SET qty = qty + ? WHERE user_id=? AND item_key=?",
            (qty, str(user_id), item_key),
        )
    conn.commit()
    conn.close()


def remove_item(user_id: int, item_key: str, qty: int) -> bool:
    inv = get_inventory(user_id)
    cur_qty = inv.get(item_key, 0)
    if cur_qty < qty:
        return False

    conn = get_conn()
    cur = conn.cursor()
    new_qty = cur_qty - qty
    if new_qty <= 0:
        cur.execute(
            "DELETE FROM inventory WHERE user_id=? AND item_key=?",
            (str(user_id), item_key),
        )
    else:
        cur.execute(
            "UPDATE inventory SET qty=? WHERE user_id=? AND item_key=?",
            (new_qty, str(user_id), item_key),
        )
    conn.commit()
    conn.close()
    return True


def now_epoch() -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT strftime('%s','now') AS t")
    t = int(cur.fetchone()["t"])
    conn.close()
    return t


def set_cooldown(user_id: int, command: str, seconds: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO cooldowns(user_id, command, cooldown_until) VALUES(?,?,?) "
        "ON CONFLICT(user_id, command) DO UPDATE SET cooldown_until=excluded.cooldown_until",
        (str(user_id), command, now_epoch() + int(seconds)),
    )
    conn.commit()
    conn.close()


def get_cooldown_until(user_id: int, command: str) -> Optional[int]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT cooldown_until FROM cooldowns WHERE user_id=? AND command=?",
        (str(user_id), command),
    )
    row = cur.fetchone()
    conn.close()
    return int(row["cooldown_until"]) if row else None


def format_seconds(secs: int) -> str:
    secs = max(0, int(secs))
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


# -----------------------------
# Dank Memer style helpers
# -----------------------------

def meme_title(what: str) -> str:
    return f"🧾 {what}" if what else "🧾"


def dank_emote() -> str:
    return random.choice(["🤑", "💸", "😈", "🔥", "✨", "💅", "🧠"])


def coin_emoji(amount: int) -> str:
    return "🪙" if amount < 10000 else "💰"


# -----------------------------
# Shop config
# -----------------------------

SHOP_ITEMS = {
    "coders_cola": {
        "name": "Coders Cola",
        "price": 250,
        "description": "Ricarica la mente. (Non chiedere come.)",
        "icon": "🥤",
    },
    "memes_scroll": {
        "name": "Scroll of Dank",
        "price": 1200,
        "description": "Leggerlo aumenta la probabilità di meme migliori. +luck (finto).",
        "icon": "📜",
    },
    "golden_sandwich": {
        "name": "Golden Sandwich",
        "price": 3500,
        "description": "Per gli affamati di coins. (Omaggio calorico.)",
        "icon": "🥪",
    },
}


# -----------------------------
# Bot
# -----------------------------

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


def make_embed(title: str, description: str, *, color: discord.Color = discord.Color.blurple()):
    return discord.Embed(title=title, description=description, color=color)


async def send_ctx_reply(ctx: commands.Context, embed: discord.Embed | None = None, content: str | None = None):
    if embed is not None:
        await ctx.reply(content=content, embed=embed, mention_author=False)
    else:
        await ctx.reply(content=content, mention_author=False)


# -----------------------------
# Event
# -----------------------------

@bot.event
async def on_ready():
    init_db()
    try:
        synced = await bot.tree.sync()
        print(f"[OK] Slash commands synced: {len(synced)}")
    except Exception as e:
        print(f"[WARN] Slash sync failed: {e}")
    print(f"Logged in as {bot.user} (prefix={PREFIX})")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.reply(f"❌ Errore: {type(error).__name__}: {error}", mention_author=False)


# -----------------------------
# Economy prefixed (dal bot.py originale)
# -----------------------------

@bot.command(name="balance", aliases=["bal", "coins", "wallet"])
async def balance_pref(ctx: commands.Context, member: Optional[discord.Member] = None):
    target = member or ctx.author
    ensure_user(target.id)
    coins = get_coins(target.id)
    inv = get_inventory(target.id)
    items_count = sum(inv.values())

    desc = (
        f"{coin_emoji(coins)} **{coins:,}** coins\n"
        f"🎒 Inventory items: **{items_count}**\n"
        f"{dank_emote()} stay dank."
    )
    await send_ctx_reply(ctx, embed=make_embed(meme_title("B A L A N C E"), desc, color=discord.Color.gold()))


@bot.command(name="profile", aliases=["inv", "inventory"])
async def profile_pref(ctx: commands.Context, member: Optional[discord.Member] = None):
    target = member or ctx.author
    ensure_user(target.id)
    inv = get_inventory(target.id)
    coins = get_coins(target.id)

    if not inv:
        desc = f"{coin_emoji(coins)} **{coins:,}** coins\n\n🎒 Nessun item ancora. Vai al **shop** e compra qualcosa."
        await send_ctx_reply(ctx, embed=make_embed("🎭 PROFILO", desc))
        return

    lines = [
        f"{SHOP_ITEMS.get(k, {'name': k, 'icon': '🎁'})['icon']} **{SHOP_ITEMS.get(k, {'name': k})['name']}** x{q}"
        for k, q in inv.items()
    ]
    desc = f"{coin_emoji(coins)} **{coins:,}** coins\n\n" + "\n".join(lines)
    await send_ctx_reply(ctx, embed=make_embed("🎭 PROFILO", desc))


@bot.command(name="daily")
async def daily_pref(ctx: commands.Context):
    user_id = ctx.author.id
    ensure_user(user_id)

    on_cd, remaining = (lambda uid: (False, 0)) (0,)
    on_cd, remaining = (lambda: (False, 0))()
    on_cd, remaining = (lambda uid: (get_cooldown_until(uid, "daily") is not None and (get_cooldown_until(uid, "daily") - now_epoch() > 0), max(0, (get_cooldown_until(uid, "daily") or 0) - now_epoch()))) (user_id)

    if on_cd:
        await send_ctx_reply(ctx, content=f"⏳ Aspetta ancora **{format_seconds(remaining)}** per il daily {ctx.author.mention}.")
        return

    reward = random.randint(150, 600)
    add_coins(user_id, reward)
    set_cooldown(user_id, "daily", 24 * 60 * 60)

    desc = (
        f"{ctx.author.mention} ha appena claimato il **daily**.\n"
        f"{dank_emote()} +{coin_emoji(reward)} **{reward:,}** coins!\n"
        f"Non sprecare tutto in un singolo shop. (spoiler: lo farai.)"
    )
    await send_ctx_reply(ctx, embed=make_embed("📅 DAILY", desc, color=discord.Color.green()))


@bot.command(name="work", aliases=["lavoro"])
async def work_pref(ctx: commands.Context):
    user_id = ctx.author.id
    ensure_user(user_id)

    on_cd, remaining = (lambda: (False, 0))()
    on_cd, remaining = (lambda uid: ((get_cooldown_until(uid, "work") or 0) - now_epoch() > 0, max(0, (get_cooldown_until(uid, "work") or 0) - now_epoch()))) (user_id)

    if on_cd:
        await send_ctx_reply(
            ctx,
            content=f"🛠️ Sei in cooldown. **{format_seconds(remaining)}** ancora e poi puoi lavorare di nuovo, {ctx.author.mention}.",
        )
        return

    reward = random.randint(50, 200)
    bonus = 0
    if random.random() < 0.12:
        bonus = random.randint(80, 260)

    total = reward + bonus
    add_coins(user_id, total)
    set_cooldown(user_id, "work", 25 * 60)

    bonus_line = f"\n🎉 BONUS: +**{bonus:,}** coins" if bonus else ""
    desc = (
        f"🧱 {ctx.author.mention} ha lavorato duramente...\n"
        f"💸 Guadagno: +{coin_emoji(total)} **{total:,}** coins"
        f"{bonus_line}\n\n"
        f"Meno chiacchiere, più grind."
    )
    await send_ctx_reply(ctx, embed=make_embed("💼 WORK", desc, color=discord.Color.orange()))


@bot.command(name="shop")
async def shop_pref(ctx: commands.Context):
    lines = [f"{v['icon']} **{v['name']}** — {coin_emoji(v['price'])} **{v['price']:,}**" for v in SHOP_ITEMS.values()]
    await send_ctx_reply(ctx, embed=make_embed("🛒 SHOP", "\n".join(lines), color=discord.Color.blurple()))


@bot.command(name="buy")
async def buy_pref(ctx: commands.Context, item_key: str):
    user_id = ctx.author.id
    ensure_user(user_id)

    key = item_key.lower().replace(" ", "_")
    if key not in SHOP_ITEMS:
        await send_ctx_reply(ctx, content=f"❌ Item non trovato: **{item_key}**. Usa `!shop`.")
        return

    price = int(SHOP_ITEMS[key]["price"])
    coins = get_coins(user_id)

    if coins < price:
        await send_ctx_reply(ctx, content=f"💸 Fondi insufficienti. Hai **{coins:,}** ma costa **{price:,}**. Vai a fare un `!work`.")
        return

    add_coins(user_id, -price)
    add_item(user_id, key, 1)

    item = SHOP_ITEMS[key]
    desc = (
        f"{dank_emote()} {ctx.author.mention} ha comprato **{item['name']}**\n"
        f"- {coin_emoji(price)} **{price:,}** coins\n"
        f"🎒 In inventario: +1"
    )
    await send_ctx_reply(ctx, embed=make_embed("✅ ACQUISTO", desc, color=discord.Color.green()))


@bot.command(name="leaderboard", aliases=["lb", "top"])
async def leaderboard_pref(ctx: commands.Context):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, coins FROM users ORDER BY coins DESC LIMIT 10")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await send_ctx_reply(ctx, content="Leaderboard vuota. Fai daily/work e riempi il server.")
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for idx, r in enumerate(rows, start=1):
        uid = int(r["user_id"])
        coins = int(r["coins"])
        user = ctx.guild.get_member(uid) if ctx.guild else None
        name = user.display_name if user else str(uid)
        medal = medals[idx - 1] if idx <= 3 else "#"
        lines.append(f"{medal} **{idx}. {name}** — {coins:,} coins")

    await send_ctx_reply(ctx, embed=make_embed("🏆 LEADERBOARD", "\n".join(lines), color=discord.Color.gold()))


# -----------------------------
# Slash commands (economy)
# -----------------------------

class EconomyGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="economy", description="Economia Dank Memer-style")

eco = EconomyGroup()


@eco.command(name="balance", description="Mostra i tuoi coins")
async def balance_slash(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    target = member or interaction.user
    ensure_user(target.id)
    coins = get_coins(target.id)
    await interaction.response.send_message(
        embed=make_embed("🧾 BALANCE", f"{coin_emoji(coins)} **{coins:,}** coins", color=discord.Color.gold()),
        ephemeral=False,
    )


@eco.command(name="daily", description="Claim daily (24h cooldown)")
async def daily_slash(interaction: discord.Interaction):
    user_id = interaction.user.id
    ensure_user(user_id)

    until = get_cooldown_until(user_id, "daily")
    remaining = 0 if until is None else until - now_epoch()
    if remaining > 0:
        await interaction.response.send_message(
            content=f"⏳ Daily in cooldown: **{format_seconds(remaining)}**.",
            ephemeral=True,
        )
        return

    reward = random.randint(150, 600)
    add_coins(user_id, reward)
    set_cooldown(user_id, "daily", 24 * 60 * 60)

    await interaction.response.send_message(
        embed=make_embed(
            "📅 DAILY",
            f"{interaction.user.mention} ha claimato il **daily**.\n{dank_emote()} +{coin_emoji(reward)} **{reward:,}** coins!",
            color=discord.Color.green(),
        )
    )


@eco.command(name="work", description="Lavora e guadagna coins (cooldown breve)")
async def work_slash(interaction: discord.Interaction):
    user_id = interaction.user.id
    ensure_user(user_id)

    until = get_cooldown_until(user_id, "work")
    remaining = 0 if until is None else until - now_epoch()
    if remaining > 0:
        await interaction.response.send_message(
            content=f"🛠️ In cooldown: **{format_seconds(remaining)}**.",
            ephemeral=True,
        )
        return

    reward = random.randint(50, 200)
    bonus = 0
    if random.random() < 0.12:
        bonus = random.randint(80, 260)

    total = reward + bonus
    add_coins(user_id, total)
    set_cooldown(user_id, "work", 25 * 60)

    bonus_line = f"\n🎉 BONUS: +**{bonus:,}** coins" if bonus else ""
    desc = f"💼 Guadagno: +{coin_emoji(total)} **{total:,}** coins{bonus_line}"

    await interaction.response.send_message(embed=make_embed("💼 WORK", desc, color=discord.Color.orange()))

@eco.command(name="addcoins", description="Aggiunge o rimuove coins")
async def addcoins(
    interaction: discord.Interaction,
    user: discord.Member,
    amount: int
):
    if interaction.user.id != MIO_ID:
        await interaction.response.send_message(
            "❌ Non hai il permesso di usare questo comando.",
            ephemeral=True
        )
        return

    add_coins(user.id, amount)

    new_balance = get_coins(user.id)

    await interaction.response.send_message(
        f"✅ Modificate **{amount:,}** coins a {user.mention}\n"
        f"💰 Nuovo saldo: **{new_balance:,}**"
    )

@eco.command(name="setcoins", description="Imposta le coins di un utente")
async def setcoins(
    interaction: discord.Interaction,
    user: discord.Member,
    amount: int
):
    if interaction.user.id != MIO_ID:
        await interaction.response.send_message(
            "❌ Non hai il permesso di usare questo comando.",
            ephemeral=True
        )
        return

    set_coins(user.id, amount)

    await interaction.response.send_message(
        f"💰 Coins di {user.mention} impostate a **{amount:,}**."
    )

@eco.command(name="shop", description="Mostra gli item in shop")
async def shop_slash(interaction: discord.Interaction):
    lines = [f"{v['icon']} **{v['name']}** — {coin_emoji(v['price'])} **{v['price']:,}**" for v in SHOP_ITEMS.values()]
    await interaction.response.send_message(
        embed=make_embed("🛒 SHOP", "\n".join(lines), color=discord.Color.blurple())
    )


@eco.command(name="buy", description="Compra un item dallo shop")
async def buy_slash(interaction: discord.Interaction, item_key: str):
    user_id = interaction.user.id
    ensure_user(user_id)

    key = item_key.lower().replace(" ", "_")
    if key not in SHOP_ITEMS:
        await interaction.response.send_message(
            content=f"❌ Item non trovato: **{item_key}**. Usa `/economy shop`.",
            ephemeral=True,
        )
        return

    item = SHOP_ITEMS[key]
    price = int(item["price"])
    coins = get_coins(user_id)

    if coins < price:
        await interaction.response.send_message(
            content=f"💸 Fondi insufficienti. Hai **{coins:,}**, serve **{price:,}**.",
            ephemeral=True,
        )
        return

    add_coins(user_id, -price)
    add_item(user_id, key, 1)

    await interaction.response.send_message(
        embed=make_embed("🧾 ACQUISTO", f"✅ Comprare: **{item['name']}**\n- {coin_emoji(price)} **{price:,}** coins", color=discord.Color.green())
    )


@eco.command(name="profile", description="Mostra coins e inventario")
async def profile_slash(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    target = member or interaction.user
    ensure_user(target.id)

    coins = get_coins(target.id)
    inv = get_inventory(target.id)
    if not inv:
        await interaction.response.send_message(
            embed=make_embed("🎭 PROFILO", f"{coin_emoji(coins)} **{coins:,}** coins\n\nNessun item ancora. `/economy shop`!"),
        )
        return

    lines = [
        f"{SHOP_ITEMS.get(k, {'icon': '🎁', 'name': k})['icon']} **{SHOP_ITEMS.get(k, {'name': k})['name']}** x{q}"
        for k, q in inv.items()
    ]
    desc = f"{coin_emoji(coins)} **{coins:,}** coins\n\n" + "\n".join(lines)
    await interaction.response.send_message(embed=make_embed("🎭 PROFILO", desc))


@eco.command(name="leaderboard", description="Top coins")
async def leaderboard_slash(interaction: discord.Interaction):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, coins FROM users ORDER BY coins DESC LIMIT 10")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await interaction.response.send_message("Leaderboard vuota.")
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for idx, r in enumerate(rows, start=1):
        uid = int(r["user_id"])
        coins = int(r["coins"])
        user = interaction.guild.get_member(uid) if interaction.guild else None
        name = user.display_name if user else str(uid)
        medal = medals[idx - 1] if idx <= 3 else "#"
        lines.append(f"{medal} **{idx}. {name}** — {coins:,} coins")

    await interaction.response.send_message(
        embed=make_embed("🏆 LEADERBOARD", "\n".join(lines), color=discord.Color.gold())
    )


bot.tree.add_command(eco)


# -----------------------------
# Comandi di bot1.py (unificati) - senza collisions su daily/balance
# -----------------------------

# CONFIG bot1 (hardcoded legacy). Se vuoi, posso metterli in .env.
CANALE_ID = 1510742175347114004
MIO_ID = 949015242871029820


@bot.event
async def on_guild_join(guild: discord.Guild):
    channel = guild.system_channel or (guild.text_channels[0] if guild.text_channels else None)
    if channel is not None:
        await channel.send(
            "Ciao! Sono B(ot)LL, il bot di samu. Scrivi `!aiuto` per vedere tutti i comandi!"
        )


@bot.command()
async def spegni(ctx: commands.Context):
    if ctx.author.id != MIO_ID:
        await ctx.send("Non hai i permessi per farlo! ❌")
        return
    channel = bot.get_channel(CANALE_ID)
    if channel:
        await channel.send("Bot offline! 🔴")
    await bot.close()


@bot.command()
async def ciao(ctx: commands.Context):
    await ctx.send(f"ciao {ctx.message.author}, sono il bot di samu.")


@bot.command(aliases=["cancella", "pulisci", "delete"])
@commands.has_permissions(administrator=True)
async def clear(ctx: commands.Context, amount: int = 1):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"ho cancellato {amount} messaggi.")


# Inside jokes
@bot.command()
async def sandro(ctx: commands.Context):
    await ctx.send("boom")
    await ctx.send("https://cdn.pixabay.com/photo/2024/05/03/16/59/nuclear-8737457_640.jpg")


@bot.command()
async def samu(ctx: commands.Context):
    await ctx.send("my glorious king")
    await ctx.send("https://images.steamusercontent.com/ugc/966474717666994289/9B1983B8752F554FD7A932226DF55F9988A3E644/")


@bot.command()
async def y(ctx: commands.Context):
    percorso = "imgprova.jpeg"
    await ctx.send(file=discord.File(percorso))


# Giochi
@bot.command()
async def dado(ctx: commands.Context, facce: int = 6):
    risultato = random.randint(1, facce)
    await ctx.send(f"🎲 Hai tirato un dado a {facce} facce... **{risultato}**!")


@bot.command()
async def coinflip(ctx: commands.Context):
    risultato = random.choice(["Testa 🪙", "Croce 🪙"])
    await ctx.send(f"La moneta dice... **{risultato}**!")


@bot.command(aliases=["8ball", "palla"])
async def ball(ctx: commands.Context, *, domanda: str):
    risposte = [
        "Assolutamente sì! ✅",
        "Decisamente sì! ✅",
        "Sì, senza dubbio! ✅",
        "Le prospettive sono buone 🟡",
        "Forse... 🟡",
        "Non sono sicuro 🟡",
        "Non ci contare ❌",
        "Le prospettive sono fosche ❌",
        "Assolutamente no ❌",
    ]
    await ctx.send(f"🎱 **{domanda}**\n> {random.choice(risposte)}")


@bot.command()
async def rps(ctx: commands.Context, scelta: str):
    scelte = ["sasso", "carta", "forbice"]
    scelta = scelta.lower()
    if scelta not in scelte:
        await ctx.send("Scegli tra sasso, carta o forbice! ❌")
        return

    bot_scelta = random.choice(scelte)
    if scelta == bot_scelta:
        esito = "Pareggio! 🤝"
    elif (scelta == "sasso" and bot_scelta == "forbice") or (scelta == "carta" and bot_scelta == "sasso") or (
        scelta == "forbice" and bot_scelta == "carta"
    ):
        esito = "Hai vinto! 🎉"
    else:
        esito = "Hai perso! 💀"

    await ctx.send(f"Tu: **{scelta}** | Io: **{bot_scelta}** → {esito}")


@bot.command()
async def crime(ctx: commands.Context):
    success = random.choice([True, False])
    if success:
        money = random.randint(100, 500)
        ensure_user(ctx.author.id)
        add_coins(ctx.author.id, money)
        await ctx.send(f"💰 Colpo riuscito. Hai ottenuto {money} monete.")
    else:
        await ctx.send("🚔 Ti hanno beccato. Skill issue.")


# Reputation (in-memory)
user_rep: dict[int, int] = {}


@bot.command()
async def rep(ctx: commands.Context, member: discord.Member):
    if member.id == ctx.author.id:
        return await ctx.send("bro 😭")

    user_rep[member.id] = user_rep.get(member.id, 0) + 1
    await ctx.send(f"{member.mention} ora ha {user_rep[member.id]} reputazione ⭐")


roasts = [
    "ha meno RAM di una calcolatrice",
    "clicca 'Accetto' senza leggere",
    "cerca Google su Bing",
    "usa la modalità chiara alle 3 di notte",
]


@bot.command()
async def roast(ctx: commands.Context, member: discord.Member):
    await ctx.send(f"{member.mention} {random.choice(roasts)} 💀")


@bot.command()
async def quote(ctx: commands.Context):
    messages = []
    async for message in ctx.channel.history(limit=200):
        if not message.author.bot:
            messages.append(message)

    if not messages:
        return await ctx.send("Nessun messaggio trovato.")

    chosen = random.choice(messages)
    await ctx.send(f"💬 {chosen.author}: {chosen.content}")


@bot.command()
async def hack(ctx: commands.Context, member: discord.Member):
    msg = await ctx.send(f"Hack di {member.name} in corso...")
    await asyncio.sleep(2)
    await msg.edit(content="📂 Recupero dati...")
    await asyncio.sleep(2)
    await msg.edit(content="🔑 Password trovata: ********")
    await asyncio.sleep(2)
    await msg.edit(content=f"✅ {member.name} hackerato con successo.")


@bot.command()
async def ship(ctx: commands.Context, user1: discord.Member, user2: discord.Member):
    score = random.randint(0, 100)
    if score < 30:
        msg = "disastro totale 💀"
    elif score < 70:
        msg = "potrebbe funzionare 👀"
    else:
        msg = "matrimonio domani 💍"

    await ctx.send(f"{user1.mention} ❤️ {user2.mention}\nCompatibilità: **{score}%**\n{msg}")


@bot.command()
async def reverse(ctx: commands.Context, *, text: str):
    await ctx.send(text[::-1])


@bot.command()
async def stalk(ctx: commands.Context, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"Profilo segreto di {member.name}")
    embed.add_field(name="Account creato", value=f"<t:{int(member.created_at.timestamp())}:R>")
    embed.add_field(name="Entrato nel server", value=f"<t:{int(member.joined_at.timestamp())}:R>")
    embed.add_field(name="Ruoli", value=", ".join(role.name for role in member.roles[1:]) or "Nessuno")
    await ctx.send(embed=embed)


# NOTE: in bot1.py esistono anche `balance` e `daily` che collidono.
# Li eliminiamo e usiamo solo quelli di economy unica (quindi !balance / !daily restano quelli di bot.py).


# Utility
@bot.command()
async def avatar(ctx: commands.Context, utente: discord.Member = None):
    utente = utente or ctx.author
    embed = discord.Embed(title=f"Avatar di {utente.display_name}", color=discord.Color.blue())
    embed.set_image(url=utente.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command()
async def info(ctx: commands.Context, utente: discord.Member = None):
    utente = utente or ctx.author
    embed = discord.Embed(title=f"Info su {utente.display_name}", color=discord.Color.green())
    embed.set_thumbnail(url=utente.display_avatar.url)
    embed.add_field(name="Nome", value=utente.name, inline=True)
    embed.add_field(name="ID", value=utente.id, inline=True)
    embed.add_field(name="Iscritto a Discord", value=utente.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="Entrato nel server", value=utente.joined_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="Ruoli", value=", ".join([r.name for r in utente.roles[1:]]) or "Nessuno", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def poll(ctx: commands.Context, *, domanda: str):
    embed = discord.Embed(title=f"📊 {domanda}", color=discord.Color.gold())
    embed.set_footer(text=f"Sondaggio creato da {ctx.author.display_name}")
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")


@bot.command()
async def countdown(ctx: commands.Context, secondi: int = 10):
    if secondi > 300:
        await ctx.send("Massimo 300 secondi! ❌")
        return
    for i in range(secondi, 0, -1):
        await ctx.send(f"⏳ {i}...")
        await asyncio.sleep(1)
    await ctx.send("🎉 **TEMPO SCADUTO!**")


# Moderazione
@bot.command()
@commands.has_permissions(administrator=True)
async def elimina(ctx: commands.Context, *, parola: str):
    await ctx.message.delete()

    def contiene_parola(msg: discord.Message):
        return parola.lower() in msg.content.lower()

    eliminati = await ctx.channel.purge(check=contiene_parola)
    await ctx.send(f"Ho eliminato {len(eliminati)} messaggi contenenti **{parola}**.")


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx: commands.Context, utente: discord.Member, *, motivo: str = "Nessun motivo specificato"):
    await utente.ban(reason=motivo)
    await ctx.send(f"🔨 **{utente.display_name}** è stato bannato. Motivo: {motivo}")


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx: commands.Context, utente: discord.Member, *, motivo: str = "Nessun motivo specificato"):
    await utente.kick(reason=motivo)
    await ctx.send(f"👢 **{utente.display_name}** è stato kickato. Motivo: {motivo}")


@bot.command()
@commands.has_permissions(manage_roles=True)
async def muta(ctx: commands.Context, utente: discord.Member):
    ruolo_muto = discord.utils.get(ctx.guild.roles, name="Muto")
    if not ruolo_muto:
        ruolo_muto = await ctx.guild.create_role(name="Muto")
        for canale in ctx.guild.channels:
            await canale.set_permissions(ruolo_muto, send_messages=False, speak=False)
    await utente.add_roles(ruolo_muto)
    await ctx.send(f"🔇 **{utente.display_name}** è stato mutato.")


@bot.command()
async def annuncio(ctx: commands.Context, *, testo: str):
    if ctx.author.id != MIO_ID:
        await ctx.send("Non hai i permessi per farlo! ❌")
        return
    embed = discord.Embed(title="📢 ANNUNCIO", description=f"**{testo}**", color=discord.Color.red())
    embed.set_footer(text=f"Annuncio di {ctx.author.display_name}")
    await ctx.send(embed=embed)


# Help
@bot.command(aliases=["comandi", "guide", "help"])
async def aiuto(ctx: commands.Context):
    embed = discord.Embed(title="📋 Lista comandi", color=discord.Color.blurple())

    embed.add_field(
        name="🎮 Giochi",
        value=(
            "`dado <facce>` — tira un dado (default 6)\n"
            "`coinflip` — testa o croce\n"
            "`ball <domanda>` — magic 8-ball\n"
            "`rps <sasso/carta/forbice>` — morra cinese\n"
            "`ship @utente1 @utente2` — calcola la compatibilità ❤️\n"
            "`crime` — tenta un colpo 🚔"
        ),
        inline=False,
    )

    embed.add_field(
        name="🔧 Utility",
        value=(
            "`avatar @utente` — mostra l\'avatar\n"
            "`info @utente` — info sull\'utente\n"
            "`poll <domanda>` — crea un sondaggio\n"
            "`countdown <n>` — conto alla rovescia (max 300)\n"
            "`annuncio <testo>` — manda un annuncio\n"
            "`reverse <testo>` — scrive il testo al contrario 🔄\n"
            "`quote` — mostra un messaggio casuale 💬\n"
            "`stalk @utente` — statistiche dettagliate 🔍"
        ),
        inline=False,
    )

    embed.add_field(
        name="🛡️ Moderazione",
        value=(
            "`clear <n>` — cancella n messaggi\n"
            "`elimina <parola>` — cancella messaggi con \"parola\"\n"
            "`ban @utente` — banna un utente\n"
            "`kick @utente` — kicka un utente\n"
            "`muta @utente` — muta un utente"
        ),
        inline=False,
    )

    embed.add_field(
        name="💰 Economia",
        value=(
            "`daily` — ritira la ricompensa giornaliera 💰\n"
            "`work` — lavora per guadagnare 💼\n"
            "`shop` — mostra gli item\n"
            "`buy <item>` — compra un item\n"
            "`balance` — mostra coins\n"
            "`profile` — inventario & items"
        ),
        inline=False,
    )

    embed.add_field(
        name="💀 Meme",
        value=(
            "`hack @utente` — hackeraggio totalmente finto\n"
            "`roast @utente` — insulto casuale\n"
            "`samu` / `sandro` / `y` — inside jokes"
        ),
        inline=False,
    )

    embed.set_footer(text=f"Richiesto da {ctx.author.display_name}")
    await ctx.send(embed=embed)


def main():
    if not TOKEN or TOKEN == "PASTE_YOUR_TOKEN_HERE":
        raise RuntimeError("DISCORD_TOKEN non impostato. Impostalo su Railway come Environment Variable/Secret.")
    bot.run(TOKEN)



if __name__ == "__main__":
    main()
