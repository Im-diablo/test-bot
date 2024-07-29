import os
from discord.ext import commands
from discord import app_commands 
from collections import defaultdict
import discord  
import gdown

intents = discord.Intents.all()
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="x", intents=discord.Intents.all())

@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hey {interaction.user.mention}! My latency is {round(bot.latency * 1000)}ms",
        ephemeral=True)

@bot.tree.command(name="say", description="Want to say something? to someone,say with the help of this")
@app_commands.describe(thing_to_say="synced")
async def say(interaction: discord.Interaction, thing_to_say: str,
            to: discord.Member):
  await interaction.response.send_message(
      f"{interaction.user.mention} said: `{thing_to_say}` to '{to.mention}'")

bad_words = ["chutiya", "lodu","fuck", "maderchod", "madarchod", "madarchoda", "madarchod", "madarchod","bhenchod", "bhenchoda", "bhenchod", "bhenchod", "bsdk", "chutiya",
        "chutiye", "chutiye", "chutiya", "betichod", "betichoda", "betichod",
        "betichoda", "gandu", "chut", "lund"]  
user_levels = defaultdict(int)
user_xp = defaultdict(int)
spam_tracker = defaultdict(list)

@bot.event
async def on_message(message):
        if message.author == bot.user:
            return

        # Check for bad words
        if any(word in message.content.lower() for word in bad_words):
            await message.delete()
            await message.channel.send(f"{message.author.mention}, please avoid using bad language!")
            return

        # Check for spam
        now = message.created_at.timestamp()
        spam_tracker[message.author.id].append(now)
        spam_tracker[message.author.id] = [t for t in spam_tracker[message.author.id] if now - t < 10]
        if len(spam_tracker[message.author.id]) > 5:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, please do not spam!")
            return

@bot.command()
async def mute(ctx, member: discord.Member, *, reason=None):
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not mute_role:
            mute_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(mute_role, speak=False, send_messages=False)
        await member.add_roles(mute_role, reason=reason)
        await ctx.send(f"{member.mention} has been muted.")

@bot.command()
async def leaderboard(ctx):
        sorted_users = sorted(user_levels.items(), key=lambda x: x[1], reverse=True)
        leaderboard = "\n".join([f"<@{user_id}> - Level {level}" for user_id, level in sorted_users[:10]])
        await ctx.send(f"Leaderboard:\n{leaderboard}")


url = 'https://drive.google.com/u/0/uc?id=1F3ZGuaKN4ugYe_K1k9jLpAndTrNUvyWs'
output = 'token.txt'
gdown.download(url, output, quiet=False)

with open('token.txt') as f:
    TOKEN = f.readline()

bot.run(TOKEN)
