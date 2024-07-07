import discord, dotenv, os, pickle, web_scraper, re

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

def get_courses_in_subject(subject: str, course_list: dict) -> dict | None:
    if subject in course_list.keys():
        return course_list[subject]
    else:
        return None
    
def get_course(course: str, course_list: dict) -> list | None:
    c = get_courses_in_subject(course[:4].upper(), course_list)
    if c == None:
        return None
    elif course in c.keys():
        return c[course]
    else:
        return None
    
def reverse_search_course(course: str, option: str, course_list: dict) -> set:
    course = course.upper()
    found_courses = set()
    state = 1
    if option == "pre-req":
        state = 1
    elif option == "co-req":
        state = 2
    elif option == "exclusion":
        state = 3
    for subject in course_list:
        for c in course_list[subject]:
            req = course_list[subject][c][state]
            for r in req:
                if re.search(f"{course[:4]} {course[4:]}", r) or re.search(course, r):
                    found_courses.add(c)
    return found_courses

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
    msg = "List of course channels:\n```"
    for i in sorted(channel_list):
        msg += '- ' + i.upper() + '\n'
    msg.strip()
    msg += '```'
    await ctx.followup.send(msg)

@course.command(name = "scrape", description = "Scrape course information for a certain semester (in the format of <20xx-xx season>)")
async def course_scrape(ctx: discord.Interaction, semester: str):
    await ctx.response.defer()
    sem = semester.split(" ")
    course_list = web_scraper.scrape_courses(sem[0], sem[1])
    if course_list == None:
        await ctx.followup.send("Error: semester is invalid!")
        return
    if not os.path.exists("course_info"):
        os.mkdir("course_info")
    outfile = open(f"course_info/{semester.lower()}.ustcourseinfo", "wb")
    pickle.dump(course_list, outfile)
    outfile.close()
    await ctx.followup.send(f"Course information of {semester} updated and saved.")

@study_path.command(name = "enquire", description = "List a course's details or courses in a subject. Input help for help message.")
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
    
    courses: dict = get_courses_in_subject(name[:4].upper(), course_list)
    msg = ""
    if state == "course":
        msg = f"{name.upper()} in {sem[0]} {sem[1]}:\n"
        details = None
        for c in courses:
            if c == name.upper():
                details = courses[name.upper()]
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
            msg += f"- {c}\n"
        msg.strip()
        msg += '```'
    await ctx.followup.send(msg)

@study_path.command(name = "rev_search", description = "Search if the enquired course is other courses' pre-requisite, co-requisite or exclusion.")
async def search(ctx: discord.Interaction, name: str, option: discord.Option(str, choices=["pre-req", "co-req", "exclusion"]), year: str):
    await ctx.response.defer()
    name = name.upper()
    choice = {"pre-req": "pre-requisite", "co-req": "co-requisite", "exclusion": "exclusion"}
    msg = f"Courses that has {name} as its {choice[option]}:\n```\n"
    res = set()
    for season in ["fall", "winter", "spring", "summer"]:
        sem = [year, season]
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
        season_res = reverse_search_course(name, option, course_list)
        for r in season_res:
            res.add(r)
    for i in sorted(res):
        msg += f"- {i}\n"
    msg += '```'
    await ctx.followup.send(msg)

@study_path.command(name = "scrape", description = "Scrape program information for a certain academic year (in the format of <20xx-xx>)")
async def course_scrape(ctx: discord.Interaction, year: str):
    await ctx.response.defer()
    program_list, program_req = web_scraper.scrape_programs(year)
    if program_list == None:
        await ctx.followup.send("Error: year is invalid!")
        return
    if not os.path.exists("program_info"):
        os.mkdir("program_info")
    outfile = open(f"program_info/{year}.ustprogramlist", "wb")
    pickle.dump(program_list, outfile)
    outfile.close()
    if program_req == None:
        await ctx.followup.send("An error has occurred while scraping program requirements. Please try again later.\nIf this error continues, please contact the bot owner.")
        return
    outfile = open(f"program_info/{year}.ustprogramreq", "wb")
    pickle.dump(program_req, outfile)
    outfile.close()
    await ctx.followup.send(f"Program information of {year} updated and saved.")

@study_path.command(name = "req", description = "List a program's requirements")
async def program_req(ctx: discord.Interaction, name: str):
    await ctx.response.defer()
    msg = f"{name.upper()}'s program requirements:\n"
    await ctx.followup.send(msg)

@client.event
async def on_ready():
    print("bot is now online")

bot.run(token)