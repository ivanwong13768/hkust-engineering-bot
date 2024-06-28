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
    for c in name[:4]:
        if not c.isalpha():
            await interaction.respond(f"Error: name is invalid")
            return
    for c in name[4:]:
        if not c.isnumeric():
            await interaction.respond(f"Error: name is invalid")
            return
    formatted_name = name[:4].lower() + "_" + name[4:]
    await interaction.respond(f"Joined channel {formatted_name}")

@bot.slash_command(
    name = "create_course",
    description = "Create a new course channel."
)
async def create_course(interaction: discord.Interaction, name: str):
    for c in name[:4]:
        if not c.isalpha():
            await interaction.respond(f"Error: name is invalid")
            return
    for c in name[4:]:
        if not c.isnumeric():
            await interaction.respond(f"Error: name is invalid")
            return
    formatted_name = name[:4].lower() + "_" + name[4:]
    await interaction.respond(f"Created channel {formatted_name}")

@bot.slash_command(
    name = "list_course",
    description = "List currently existing course channels."
)
async def list_course(interaction: discord.Interaction):
    await interaction.respond("List of channels:")

@bot.event
async def on_ready():
    pass

bot.run(token)