import discord
from discord import channel
from discord.ext import commands
import asyncio
import random

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix='<', intents=intents, case_insensitive=True, help_command=None)

CANALE_ID = 1510742175347114004
MIO_ID = 949015242871029820

print('il tuo bot si sta avviando...')

# -------------------- EVENTI --------------------

@client.event
async def on_ready():
    print(f'{client.user} è ora ONLINE', f'ID {client.user.id}')
    channel = client.get_channel(CANALE_ID)
    if channel:
        await channel.send('Bot online! 🟢')

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Comando non riconosciuto! ❌')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Manca un argomento! ❌')
    elif isinstance(error, commands.BadArgument):
        await ctx.send('Argomento non valido! ❌')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send('Non hai i permessi per farlo! ❌')

@client.event
async def on_guild_join(guild):
    channel = guild.system_channel or guild.text_channels[0]
    await channel.send('Ciao! Sono B(ot)LL, il bot di samu. Scrivi `<aiuto` per vedere tutti i comandi!')



# -------------------- BASE --------------------

@client.command()
async def spegni(ctx):
    if ctx.author.id != MIO_ID:
        await ctx.send('Non hai i permessi per farlo! ❌')
        return
    channel = client.get_channel(CANALE_ID)
    await channel.send('Bot offline! 🔴')
    await client.close()

@client.command()
async def ciao(ctx):
    await ctx.send(f'ciao {ctx.message.author}, sono il bot di samu.')

@client.command(aliases=['cancella', 'pulisci', 'delete'])
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int = 1):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'ho cancellato {amount} messaggi.')

# -------------------- INSIDE JOKES --------------------

@client.command()
async def sandro(ctx):
    await ctx.send('boom')
    await ctx.send('https://cdn.pixabay.com/photo/2024/05/03/16/59/nuclear-8737457_640.jpg')

@client.command()
async def samu(ctx):
    await ctx.send('my glorious king')
    await ctx.send('https://images.steamusercontent.com/ugc/966474717666994289/9B1983B8752F554FD7A932226DF55F9988A3E644/')

import os

@client.command()
async def yana(ctx):
    percorso = "imgprova.jpeg"
    await ctx.send(file=discord.File(percorso))

@client.command()
async def striunizzo(ctx):
    await ctx.send('https://i.ytimg.com/vi/NUdK1hfDYuA/hq720.jpg?sqp=-oaymwE7CK4FEIIDSFryq4qpAy0IARUAAAAAGAElAADIQj0AgKJD8AEB-AH-CYAC0AWKAgwIABABGHIgXig4MA8=&rs=AOn4CLDoaOkzyhYqM2fEWUtTE2rV_q1v6w')

# -------------------- GIOCHI --------------------

@client.command()
async def dado(ctx, facce: int = 6):
    risultato = random.randint(1, facce)
    await ctx.send(f'🎲 Hai tirato un dado a {facce} facce... **{risultato}**!')

@client.command()
async def coinflip(ctx):
    risultato = random.choice(['Testa 🪙', 'Croce 🪙'])
    await ctx.send(f'La moneta dice... **{risultato}**!')

@client.command(aliases=['8ball', 'palla'])
async def ball(ctx, *, domanda: str):
    risposte = [
        'Assolutamente sì! ✅', 'Decisamente sì! ✅', 'Sì, senza dubbio! ✅',
        'Le prospettive sono buone 🟡', 'Forse... 🟡', 'Non sono sicuro 🟡',
        'Non ci contare ❌', 'Le prospettive sono fosche ❌', 'Assolutamente no ❌'
    ]
    await ctx.send(f'🎱 **{domanda}**\n> {random.choice(risposte)}')

@client.command()
async def rps(ctx, scelta: str):
    scelte = ['sasso', 'carta', 'forbice']
    scelta = scelta.lower()
    if scelta not in scelte:
        await ctx.send('Scegli tra sasso, carta o forbice! ❌')
        return
    bot_scelta = random.choice(scelte)
    if scelta == bot_scelta:
        esito = 'Pareggio! 🤝'
    elif (scelta == 'sasso' and bot_scelta == 'forbice') or \
         (scelta == 'carta' and bot_scelta == 'sasso') or \
         (scelta == 'forbice' and bot_scelta == 'carta'):
        esito = 'Hai vinto! 🎉'
    else:
        esito = 'Hai perso! 💀'
    await ctx.send(f'Tu: **{scelta}** | Io: **{bot_scelta}** → {esito}')

# -------------------- UTILITY --------------------

@client.command()
async def avatar(ctx, utente: discord.Member = None):
    utente = utente or ctx.author
    embed = discord.Embed(title=f'Avatar di {utente.display_name}', color=discord.Color.blue())
    embed.set_image(url=utente.display_avatar.url)
    await ctx.send(embed=embed)

@client.command()
async def info(ctx, utente: discord.Member = None):
    utente = utente or ctx.author
    embed = discord.Embed(title=f'Info su {utente.display_name}', color=discord.Color.green())
    embed.set_thumbnail(url=utente.display_avatar.url)
    embed.add_field(name='Nome', value=utente.name, inline=True)
    embed.add_field(name='ID', value=utente.id, inline=True)
    embed.add_field(name='Iscritto a Discord', value=utente.created_at.strftime('%d/%m/%Y'), inline=True)
    embed.add_field(name='Entrato nel server', value=utente.joined_at.strftime('%d/%m/%Y'), inline=True)
    embed.add_field(name='Ruoli', value=', '.join([r.name for r in utente.roles[1:]]) or 'Nessuno', inline=False)
    await ctx.send(embed=embed)

@client.command()
async def poll(ctx, *, domanda: str):
    embed = discord.Embed(title=f'📊 {domanda}', color=discord.Color.gold())
    embed.set_footer(text=f'Sondaggio creato da {ctx.author.display_name}')
    msg = await ctx.send(embed=embed)
    await msg.add_reaction('👍')
    await msg.add_reaction('👎')

@client.command()
async def countdown(ctx, secondi: int = 10):
    if secondi > 300:
        await ctx.send('Massimo 300 secondi! ❌')
        return
    for i in range(secondi, 0, -1):
        await ctx.send(f'⏳ {i}...')
        await asyncio.sleep(1)
    await ctx.send('🎉 **TEMPO SCADUTO!**')

# -------------------- MODERAZIONE --------------------

@client.command()
@commands.has_permissions(administrator=True)
async def elimina(ctx, *, parola: str):
    await ctx.message.delete()
    def contiene_parola(msg):
        return parola.lower() in msg.content.lower()
    eliminati = await ctx.channel.purge(check=contiene_parola)
    await ctx.send(f'Ho eliminato {len(eliminati)} messaggi contenenti **{parola}**.')

@client.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, utente: discord.Member, *, motivo: str = 'Nessun motivo specificato'):
    await utente.ban(reason=motivo)
    await ctx.send(f'🔨 **{utente.display_name}** è stato bannato. Motivo: {motivo}')

@client.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, utente: discord.Member, *, motivo: str = 'Nessun motivo specificato'):
    await utente.kick(reason=motivo)
    await ctx.send(f'👢 **{utente.display_name}** è stato kickato. Motivo: {motivo}')

@client.command()
@commands.has_permissions(manage_roles=True)
async def muta(ctx, utente: discord.Member):
    ruolo_muto = discord.utils.get(ctx.guild.roles, name='Muto')
    if not ruolo_muto:
        ruolo_muto = await ctx.guild.create_role(name='Muto')
        for canale in ctx.guild.channels:
            await canale.set_permissions(ruolo_muto, send_messages=False, speak=False)
    await utente.add_roles(ruolo_muto)
    await ctx.send(f'🔇 **{utente.display_name}** è stato mutato.')

@client.command()
async def annuncio(ctx, *, testo: str):
    if ctx.author.id != MIO_ID:
        await ctx.send('Non hai i permessi per farlo! ❌')
        return
    embed = discord.Embed(title='📢 ANNUNCIO', description=f'**{testo}**', color=discord.Color.red())
    embed.set_footer(text=f'Annuncio di {ctx.author.display_name}')
    await ctx.send(embed=embed)

# -------------------- HELP  --------------------

@client.command(aliases=['comandi', 'help'])
async def aiuto(ctx):
    embed = discord.Embed(title='📋 Lista comandi', color=discord.Color.blurple())
    
    embed.add_field(name='🎮 Giochi', value='''
`<dado <facce>` — tira un dado (default 6)
`<coinflip` — testa o croce
`<ball <domanda>` — magic 8-ball
`<rps <sasso/carta/forbice>` — morra cinese
''', inline=False)

    embed.add_field(name='🔧 Utility', value='''
`<avatar @utente` — mostra l\'avatar
`<info @utente` — info sull\'utente
`<poll <domanda>` — crea un sondaggio
`<countdown <n>` — conto alla rovescia (max 30)
`<annuncio <testo>` — manda un annuncio
''', inline=False)

    embed.add_field(name='🛡️ Moderazione', value='''
`<clear <n>` — cancella n messaggi
`<elimina <parola>` — cancella messaggi con "parola"
`<ban @utente` — banna un utente
`<kick @utente` — kicka un utente
`<muta @utente` — muta un utente
''', inline=False)

    embed.set_footer(text=f'Richiesto da {ctx.author.display_name}')
    await ctx.send(embed=embed)

try:
    client.run('DISCORD_TOKEN')
except KeyboardInterrupt:
    pass
