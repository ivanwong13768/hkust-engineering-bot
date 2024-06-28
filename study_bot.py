import discord, dotenv, os
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))

client = discord.Client(intents=intents)

bot = commands.Bot()

@bot.slash_command(
    name = "join_course",
    description = "Join the course channel provided in the argument."
)
async def join_course(interaction: discord.Interaction, name: str):
    pass

@bot.slash_command(
    name = "create_course",
    description = "Create a new course channel."
)
async def create_course(interaction: discord.Interaction, name: str):
    pass

@bot.slash_command(
    name = "list_course",
    description = "List currently existing course channels."
)
async def list_course(interaction: discord.Interaction):
    pass

@bot.event
async def on_ready():
    pass

bot.run(token)