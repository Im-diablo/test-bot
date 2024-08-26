import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp as youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
import re

# Setup bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
intents.voice_states = True

bot = commands.Bot(intents=intents)

# Spotify credentials
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id='YOUR_SPOTIPY_CLIENT_ID',
                                                           client_secret='YOUR_SPOTIPY_CLIENT_SECRET'))

# Music related variables
queues = {}

# Function to extract audio URL from a YouTube link
def get_youtube_url(search_query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        return info['formats'][0]['url']

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="join", description="Join the voice channel")
    async def join(self, interaction: discord.Interaction):
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            await channel.connect()
            await interaction.response.send_message(f'Joined {channel}')
        else:
            await interaction.response.send_message('You are not in a voice channel!')

    @app_commands.command(name="leave", description="Leave the voice channel")
    async def leave(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message('Left the voice channel!')
        else:
            await interaction.response.send_message('I am not in a voice channel!')

    @app_commands.command(name="play", description="Play a track from YouTube or Spotify")
    @app_commands.describe(url="The URL of the track to play")
    async def play(self, interaction: discord.Interaction, url: str):
        if interaction.guild.voice_client is None:
            if interaction.user.voice:
                channel = interaction.user.voice.channel
                await channel.connect()
            else:
                await interaction.response.send_message('You are not in a voice channel!')
                return

        voice_client = interaction.guild.voice_client
        if 'spotify.com' in url:
            track_id = re.search(r'spotify\.com/track/(\w+)', url).group(1)
            track = sp.track(track_id)
            track_name = track['name']
            track_url = track['external_urls']['spotify']

            search_query = f"{track_name} {track['artists'][0]['name']}"
            youtube_url = get_youtube_url(search_query)

            voice_client.stop()
            voice_client.play(discord.FFmpegPCMAudio(youtube_url, **{'options': '-vn'}))
            await interaction.response.send_message(f'Now playing: {track_name} by {track["artists"][0]["name"]}')
        elif url.startswith('https://www.youtube.com/') or url.startswith('https://youtu.be/'):
            youtube_url = get_youtube_url(url)
            voice_client.stop()
            voice_client.play(discord.FFmpegPCMAudio(youtube_url, **{'options': '-vn'}))
            await interaction.response.send_message(f'Now playing: {url}')
        else:
            await interaction.response.send_message('Unsupported URL. Please provide a valid YouTube or Spotify URL.')

    @app_commands.command(name="pause", description="Pause the current track")
    async def pause(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            await interaction.response.send_message('Playback paused.')
        else:
            await interaction.response.send_message('No music is currently playing.')

    @app_commands.command(name="resume", description="Resume the current track")
    async def resume(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            await interaction.response.send_message('Playback resumed.')
        else:
            await interaction.response.send_message('Music is not paused.')

    @app_commands.command(name="skip", description="Skip the current track")
    async def skip(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            await interaction.response.send_message('Skipped the current song.')
        else:
            await interaction.response.send_message('No music is currently playing.')

    @app_commands.command(name="queue", description="Queue a track from YouTube or Spotify")
    @app_commands.describe(url="The URL of the track to queue")
    async def queue(self, interaction: discord.Interaction, url: str):
        if interaction.guild.voice_client is None:
            if interaction.user.voice:
                channel = interaction.user.voice.channel
                await channel.connect()
            else:
                await interaction.response.send_message('You are not in a voice channel!')
                return

        if interaction.guild.id not in queues:
            queues[interaction.guild.id] = []

        if 'spotify.com' in url:
            track_id = re.search(r'spotify\.com/track/(\w+)', url).group(1)
            track = sp.track(track_id)
            track_name = track['name']
            track_url = track['external_urls']['spotify']

            search_query = f"{track_name} {track['artists'][0]['name']}"
            youtube_url = get_youtube_url(search_query)

            queues[interaction.guild.id].append(youtube_url)
            await interaction.response.send_message(f'Added to queue: {track_name} by {track["artists"][0]["name"]}')

            if not interaction.guild.voice_client.is_playing():
                await self.play_next(interaction)
        elif url.startswith('https://www.youtube.com/') or url.startswith('https://youtu.be/'):
            youtube_url = get_youtube_url(url)
            queues[interaction.guild.id].append(youtube_url)
            await interaction.response.send_message(f'Added to queue: {url}')

            if not interaction.guild.voice_client.is_playing():
                await self.play_next(interaction)
        else:
            await interaction.response.send_message('Unsupported URL. Please provide a valid YouTube or Spotify URL.')

    async def play_next(self, interaction: discord.Interaction):
        if interaction.guild.id in queues and queues[interaction.guild.id]:
            url = queues[interaction.guild.id].pop(0)
            interaction.guild.voice_client.play(discord.FFmpegPCMAudio(url, **{'options': '-vn'}),
                                                after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(interaction), bot.loop))
            await interaction.response.send_message('Now playing the next song in the queue.')

    @app_commands.command(name="volume", description="Set the volume of the current track")
    @app_commands.describe(volume="The volume percentage (0-100)")
    async def volume(self, interaction: discord.Interaction, volume: int):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.source.volume = volume / 100
            await interaction.response.send_message(f'Volume set to {volume}%.')
        else:
            await interaction.response.send_message('No music is currently playing.')

@bot.event
async def on_ready():
    await bot.tree.sync()  # Sync the commands with Discord
    print(f'Logged in as {bot.user.name}')

url = 'https://drive.google.com/u/0/uc?id=1F3ZGuaKN4ugYe_K1k9jLpAndTrNUvyWs'
output = 'token.txt'
gdown.download(url, output, quiet=False)

with open('token.txt') as f:
    TOKEN = f.readline()

bot.run(TOKEN)
