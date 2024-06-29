import discord, dotenv, os, pickle, web_scraper

intents = discord.Intents.default()
intents.message_content = True

dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))

client = discord.Client(intents=intents)
bot = discord.Bot()

channel_list_file = open("channel_list.txt", "r+")
channel_list = channel_list_file.readlines()
for i in range(len(channel_list)):
    channel_list[i] = channel_list[i].strip()

course = bot.create_group("course", "Course-related commands")
study_path = bot.create_group("study_path", "Study path planning commands")

def find_role(name: str, role_list: list[discord.Role]) -> discord.Role:
    for r in role_list:
        if r.name == name.lower():
            return r

def get_courses_in_subject(subject: str, course_list: dict):
    if subject in course_list.keys():
        return course_list[subject]

@course.command(name = "join", description = "Join an existing course channel")
async def join_course(ctx: discord.Interaction, name: str):
    await ctx.response.defer()
    try:
        if len(name) != 8 or len(name) != 9:
            await ctx.respond(f"Error: name is invalid!")
            return
        for c in name[:4]:
            if not c.isalpha():
                await ctx.respond(f"Error: name is invalid!")
                return
        for c in name[4:8]:
            if not c.isnumeric():
                await ctx.respond(f"Error: name is invalid!")
                return
        formatted_name = name.upper()
        server = ctx.guild
        role_list = server.roles
        role = find_role(name.lower(), role_list)
        await ctx.user.add_roles(role)
        await ctx.followup.send(f"Joined {formatted_name}'s channel.")
    except Exception as e:
        await ctx.followup.send("An error has occurred. Please try again!")
        print(e)

@course.command(name = "create", description = "Create a new course channel")
async def create_course(ctx: discord.Interaction, name: str):
    await ctx.response.defer()
    try:
        if len(name) != 8 or len(name) != 9:
            await ctx.respond(f"Error: name is invalid!")
            return
        for c in name[:4]:
            if not c.isalpha():
                await ctx.respond(f"Error: name is invalid!")
                return
        for c in name[4:8]:
            if not c.isnumeric():
                await ctx.respond(f"Error: name is invalid!")
                return
        if name.lower() in channel_list:
            await ctx.respond(f"Error: channel already exists!")
            return
        channel_name = name[:4].lower() + "-" + name[4:].lower()
        formatted_name = name.upper()
        server = ctx.guild
        role_list = server.roles
        role_names = [r.name for r in role_list]
        role = None
        if name.lower() not in role_names:
            role = await server.create_role(name=name.lower(), mentionable=True)
        else:
            role = find_role(name.lower(), role_list)
        category_list = server.categories
        category = None
        category_name = str(os.getenv("CATEGORY_NAME"))
        for c in category_list:
            if c.name == category_name:
                category = c
                break
        if category != None:
            channel = await server.create_text_channel(name=channel_name, category=category)
            for r in role_list:
                await channel.set_permissions(target=r, overwrite=discord.PermissionOverwrite(read_messages=False))
            await channel.set_permissions(target=role, overwrite=discord.PermissionOverwrite(read_messages=True))
            if name.lower() not in channel_list:
                channel_list_file.write(name.lower() + '\n')
                channel_list.append(name.lower())
                channel_list.sort()
        await ctx.followup.send(f"Created channel for {formatted_name}.")
    except Exception as e:
        await ctx.followup.send("An error has occurred. Please try again!")
        print(e)

@course.command(name = "list", description = "List currently existing course channels")
async def list_course(ctx: discord.Interaction):
    await ctx.response.defer()
    msg = "List of course channels:\n"
    for i in sorted(channel_list):
        msg += '* ' + i.upper() + '\n'
    msg.strip()
    await ctx.followup.send(msg)

@course.command(name = "scrape", description = "Scrape course information for a certain semester (in the format of <20xx-xx season>)")
async def course_scrape(ctx: discord.Interaction, semester: str):
    await ctx.response.defer()
    sem = semester.split(" ")
    course_list = web_scraper.scrape(sem[0], sem[1])
    if course_list == None:
        await ctx.followup.send("Error: semester is invalid!")
        return
    if not os.path.exists("course_info"):
        os.mkdir("course_info")
    outfile = open(f"course_info/{semester.lower()}.ustcourseinfo", "wb")
    pickle.dump(course_list, outfile)
    outfile.close()
    await ctx.followup.send("Course information updated and saved.")

@course.command(name = "enquire", description = "List a course's details or courses in a subject. Input help for help message.")
async def course_enquire(ctx: discord.Interaction, name: str, semester: str):
    await ctx.response.defer()
    state = ""
    if name.lower() == "help" and semester == None:
        await ctx.followup.send("List a course's details if course code and semester are provided, or list open courses if subject code and semester are provided. Semester should be in the form of `20xx-xx season`.")
        return
    if semester == None:
        await ctx.followup.send("Error: semester is invalid!")
        return
    elif len(name) == 4 and name.upper() in web_scraper.subject_list:
        state = "subject"
    elif (len(name) == 8 or len(name) == 9) and name[:4].upper() in web_scraper.subject_list:
        state = "course"
    else:
        await ctx.followup.send("Error: course/subject code is invalid!")
        return
    sem = semester.split(" ")
    if len(sem) != 2:
        await ctx.followup.send("Error: semester is invalid!")
        return
    sem[1] = sem[1].lower()
    course_list = None
    if not os.path.exists(f"course_info/{sem[0]} {sem[1]}.ustcourseinfo"):
        await ctx.followup.send("Error: semester does not exist! Consider running `/course scrape` first.")
        return
    else:
        infile = open(f"course_info/{sem[0]} {sem[1]}.ustcourseinfo", "rb")
        course_list = pickle.load(infile)
        infile.close()
    courses: list[dict] = get_courses_in_subject(name[:4].upper(), course_list)
    msg = ""
    if state == "course":
        msg = f"{name.upper()} in {sem[0]} {sem[1]}:\n"
        details = None
        for c in courses:
            if list(c.keys())[0] == name.upper():
                details = c[name.upper()]
                break
        if details == None:
            await ctx.followup.send("Error: course does not exist!")
            return
        msg += f"**Description:**\n{details[0]}\n"
        msg += "**Pre-requisites:**\n"
        if len(details[1]) == 0:
            msg += "None"
        else:
            for i in details[1]:
                msg += f"{i}, "
            msg = msg[:-2]
        msg += "\n**Co-requisites:**\n"
        if len(details[2]) == 0:
            msg += "None"
        else:
            for i in details[2]:
                msg += f"{i}, "
            msg = msg[:-2]
        msg += "\n**Exclusions:**\n"
        if len(details[3]) == 0:
            msg += "None"
        else:
            for i in details[3]:
                msg += f"{i}, "
            msg = msg[:-2]
    elif state == "subject":
        msg = f"{name.upper()} in {sem[0]} {sem[1]}:\n```"
        for c in courses:
            msg += f"- {list(c.keys())[0]}\n"
        msg.strip()
        msg += '```'
    await ctx.followup.send(msg)

@study_path.command(name = "req", description = "List a major's requirements")
async def major_req(ctx: discord.Interaction, name: str):
    await ctx.response.defer()
    msg = f"{name.upper()}'s major requirements:\n"
    await ctx.followup.send(msg)

@client.event
async def on_ready():
    print("bot is now online")

bot.run(token)