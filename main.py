import asyncio
import random
from operator import truediv, mul, add, sub

import discord
import sqlite3
from discord.ext import commands

with open('token.txt') as fp:
    token = fp.read()

client = commands.Bot(command_prefix="m?")
client.remove_command("help")


@client.event
async def on_ready():
    print("Ready!")
    print(client.user.name)
    await client.change_presence(activity=discord.Game("m?help"))
    db = sqlite3.connect('Miscordle.db')
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS main(
        userid BIGINT,
        health BIGINT,
        damage BIGINT,
        coins BIGINT,
        xp BIGINT,
        deaths BIGINT,
        area BIGINT,
        maxhealth BIGINT,
        incommand TINYINT,
        level BIGINT
        )''')
    db.commit()
    db.close()


async def isitme(ctx):
    return ctx.author.id == 803766890023354438


@client.event
async def on_message(message):
    if message.content.startswith("m?"):
        player = open_account(message.author, False)
        if message.content.startswith("m?sql"):
            await client.process_commands(message)
        elif player[7] == 0:
            await client.process_commands(message)
        else:
            await message.channel.send("Please end your previous command!")


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await asyncio.sleep(0)
    elif isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        await ctx.send(
            f"You are currently on cooldown for this command! Try again in {int(round(error.retry_after))} seconds")
    elif isinstance(error, discord.ext.commands.MemberNotFound):
        await ctx.send("Member not found, please try again. Join the support server if this error persists")
    else:
        await ctx.send(f"Please contact Bloop#9966 with the following text ```{str(error)}```")
        print(f"{ctx.author.name}#{ctx.author.discriminator} Raised an exception:\n{error}\n")


@client.event
async def on_message_edit(before, after):
    if before.guild.id == 773298357644820531:
        if before.content != after.content:
            if not before.author.bot:
                embed = discord.Embed(title=f"Message edited in {before.channel} from {before.author.display_name}")
                embed.add_field(name="\u200b", value=f"Before: {before.content}\nAfter: {after.content}")
                await client.get_channel(776874151796539413).send(embed=embed)


@client.event
async def on_message_delete(message):
    if message.guild.id == 773298357644820531:
        if not message.author.bot:
            embed = discord.Embed(title=f"Message deleted in {message.channel} from {message.author.display_name}")
            embed.add_field(name="\u200b", value=f"{message.content}")
            await client.get_channel(776874151796539413).send(embed=embed)


@client.command()
async def help(ctx):
    embed = discord.Embed(title="Help for Miscordle", color=0xff0099)
    embed.add_field(name="\u200b",
                    value="**m?fight (area):** Fight an enemy to help you progress\n**m?profile:** View your stats "
                          "and others in your profile\n**m?heal:** Heal yourself from your battle scars")
    await ctx.send(embed=embed)


def open_account(user: discord.User, setincommand):
    db = sqlite3.connect('Miscordle.db')
    cursor = db.cursor()
    cursor.execute(
        f'''SELECT health, damage, coins, xp, deaths, area, maxhealth, incommand, level FROM main WHERE userid={user.id}''')
    result = cursor.fetchone()
    if result is None:
        cursor.execute(
            f'''INSERT INTO main (userid, health, damage, coins, xp, deaths, area, maxhealth, incommand, level) VALUES({user.id}, 25, 1, 10, 0, 0, 1, 25, 0, 1)''')
        cursor.execute(
            f'''SELECT health, damage, coins, xp, deaths, area, maxhealth, incommand, level FROM main WHERE userid={user.id}''')
        result = cursor.fetchone()
    if setincommand:
        cursor.execute(f'''UPDATE main SET incommand = 1 WHERE userid={user.id}''')
    db.commit()
    db.close()
    return result


def generate_enemy(minhealth, maxhealth, attackmin, attackmax, mincoins, maxcoins, names, xpmin, xpmax):
    name = names[random.randint(0, int(len(names) - 1))]
    coins = random.randint(mincoins, maxcoins)
    health = random.randint(minhealth, maxhealth)
    attack = random.randint(attackmin, attackmax)
    xp = random.randint(xpmin, xpmax)
    enemy = [health, attack, coins, name, xp]
    return enemy


def generate_area(areavalue):
    if areavalue == 1:
        enemy = generate_enemy(17, 24, 1, 1, 13, 18, ["Rabbit", "Squirrel", "Woodchuck", "Garden Snake"], 4, 10)
    elif areavalue == 2:
        enemy = generate_enemy(60, 75, 5, 8, 50, 64,
                               ["Giant Spider", "Horse", "Baby Bear", "Commoner", "Lesser Spirit"], 23, 36)
    return enemy


async def on_death(player, enemy, message):
    embed = discord.Embed(title=f"You lost to {enemy[3]}   HP: {enemy[-1]}/{enemy[0]}",
                          description=f"1 Death has been added to your death count and you lost a level",
                          color=0xff0099)
    await message.edit(embed=embed)
    db = sqlite3.connect('Miscordle.db')
    cursor = db.cursor()
    if int(player[8]) - 1 >= 1:
        player[8] = int(player[8] - 1)
        totalxp = 0
        for x in range(1, player[8] + 1):
            totalxp += xp_for_level(x)
        player[3] = totalxp
    else:
        player[3] = 0
    cursor.execute(
        f'''UPDATE main SET level = {player[8]}, xp = {player[3]}, health = {player[6]}, deaths = {int(player[4]) + 1}, incommand = 0 WHERE userid={player[-1]}''')
    db.commit()
    db.close()


def xp_for_level(level):
    return (50 * (level ** 2)) - (level * 50)


async def on_victory(player, enemy, message):
    area = pendant = ""
    embed = discord.Embed(title=f"{enemy[3]} has been defeated!  HP: 0/{enemy[0]}",
                          description=f"{player[-1]}: {player[0]}/{player[6]}\nYou earned: {enemy[2]} Coins\nAnd {enemy[4]} XP",
                          color=0xff0099)
    await message.edit(embed=embed)
    db = sqlite3.connect('Miscordle.db')
    cursor = db.cursor()
    if int(player[5]) - 1 >= 1: player[5] = int(player[5] - 1)
    nextlevel = xp_for_level(player[8] + 1)
    randomint = random.randint(0, 100)
    if int(player[3]) + int(enemy[4]) >= nextlevel:
        player[8] = int(player[8]) + 1
        player[1] = int(player[1]) + 1
        player[6] = int(player[6]) + 10
        if player[8] == 3:
            player[5] = 2
            area = "\nYou have unlocked area 2!"
        await message.channel.send(
            f"You leveled up! You are now level {player[8]}!\nYour new max health is {player[6]}\nYour new attack is {player[1]}{area}{pendant}")
    cursor.execute(
        f'''UPDATE main SET incommand = 0, maxhealth = {player[6]},damage = {player[1]}, health = {player[0]}, area = {player[5]}, xp = {player[3] + enemy[4]}, coins = {player[2] + enemy[2]}, level = {player[8]} WHERE userid={player[-2]}''')
    db.commit()
    db.close()


@client.command()
@commands.check(isitme)
async def sql(ctx, *, sqlcode):
    db = sqlite3.connect('Miscordle.db')
    cursor = db.cursor()
    cursor.execute(f'''{sqlcode}''')
    await ctx.send("SQL Executed")
    db.commit()
    db.close()


@client.command(aliases=["f"])
@commands.cooldown(1, 30, commands.BucketType.user)
async def fight(ctx, area=900001):
    player = list(open_account(ctx.author, False))
    if area == 900001:
        area = player[5]
    if area > player[5]:
        await ctx.send("The given area is not unlocked yet! Try a lower number")
    elif area < 1:
        await ctx.send("1 is the lowest area, try a higher number")
    else:
        player = list(open_account(ctx.author, True))
        enemy = list(generate_area(area))
        playerhealth = player[0]
        health = enemy[0]
        idleturns = times = 0
        while health > 0 and playerhealth > 0:
            embed = discord.Embed(title=f"{enemy[3]}   HP: {health}/{enemy[0]}",
                                  description=f"{ctx.author.display_name}: {playerhealth}/{player[6]}", color=0xff0099)
            embed.add_field(name="Rage", value="Deal 250% damage but lose the next 2 turns", inline=False)
            embed.add_field(name="Attack", value="Deal 100% damage", inline=False)
            embed.add_field(name="Parry", value="Block 50% of incoming damage, and deal 30% damage", inline=False)
            embed.add_field(name="Guard", value="Block 90% of incoming damage", inline=False)
            if idleturns == 0:
                if times == 0:
                    messageembed = await ctx.send(embed=embed)
                    times += 1
                else:
                    await messageembed.edit(embed=embed)

                def check(m):
                    if str(m.content).lower() == "rage" or str(m.content).lower() == "attack" or str(
                            m.content).lower() == "parry" or str(m.content).lower() == "guard":
                        if ctx.author.id == m.author.id:
                            return True

                try:
                    msg = await client.wait_for('message', timeout=90.0, check=check)
                except asyncio.TimeoutError:
                    await ctx.send("You took too long to respond and died... nerd")
                    playerhealth = 0
                else:
                    await msg.delete()
                    if str(msg.content).lower() == "rage":
                        health -= int(round(float(player[1]) * 2.5))
                        idleturns += 2
                        playerhealth -= enemy[1]
                    if str(msg.content).lower() == "attack":
                        health -= player[1]
                        playerhealth -= enemy[1]
                    if str(msg.content).lower() == "parry":
                        health -= int(round(float(player[1]) * 0.3))
                        playerhealth -= int(round(float(enemy[1]) * 0.51))
                    if str(msg.content).lower() == "guard":
                        playerhealth -= int(round(float(enemy[1]) * 0.1))
            if idleturns > 0:
                idleturns -= 1
                playerhealth -= enemy[1]
        if health <= 0:
            if playerhealth <= 0:
                playerhealth = 1
            player[0] = playerhealth
            player.append(ctx.author.id)
            player.append(ctx.author.display_name)
            await on_victory(player, enemy, messageembed)
        elif playerhealth <= 0:
            enemy.append(health)
            player.append(ctx.author.id)
            await on_death(player, enemy, messageembed)


@client.command(aliases=["p"])
async def profile(ctx, user: discord.Member = None):
    if user is None:
        user = ctx.author
    player = open_account(user, False)
    embed = discord.Embed(title=f"{user.display_name}'s Profile", color=0xff0099)
    embed.add_field(name="Progression",
                    value=f":arrow_up: Level: {player[8]}\n:star: XP: {player[3]}/{xp_for_level(int(player[8]) + 1)}\n:door: Area: {player[5]}")
    embed.add_field(name="Stats",
                    value=f":hearts: Health: {player[0]}/{player[6]}\n:crossed_swords: Damage: {player[1]}\n:coin: Coins: {player[2]}\n:skull: Deaths: {player[4]}",
                    inline=False)
    await ctx.send(embed=embed)


@client.command(aliases=["h"])
async def heal(ctx):
    player = open_account(ctx.author, False)
    if int(player[0]) == int(player[6]):
        await ctx.send("You do not need any healing!")
    else:
        if int(player[5]) == 1:
            coins = 10
        elif int(player[5]) == 2:
            coins = 25
        if int(player[2]) < coins:
            await ctx.send(f"You do not have enough money! You need {coins} coins but only have {player[2]}")
        else:
            db = sqlite3.connect('Miscordle.db')
            cursor = db.cursor()
            cursor.execute(
                f'''UPDATE main SET health = {player[6]}, coins = {int(player[2]) - coins} WHERE userid={ctx.author.id}''')
            db.commit()
            db.close()
            await ctx.send(f"You were successfully healed for {coins} coins")


client.run(token)
