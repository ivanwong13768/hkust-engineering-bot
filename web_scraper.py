import requests, html_to_json, re, io, pandas as pd, pymupdf
from xml.sax.saxutils import escape

year_list = {(2024, "fall") : 2310, (2024, "winter") : 2320, (2024, "spring") : 2330, (2024, "summer") : 2340}
seasons = ["fall", "winter", "spring", "summer"]
subject_list = ["ACCT", "AESF", "BEHI", "BIEN", "BTEC", "CENG", "CHEM", "CIEM", "CIVL", "COMP", "CPEG", "CSIT", "ECON", "EEMT", "EESM", "ELEC", "EMBA", "EMIA", "ENEG", "ENGG", "ENTR", "ENVR", "EVSM", "FINA", "GFIN", "GNED", "HLTH", "HMMA", "HUMA", "IBTM", "IDPO", "IEDA", "IMBA", "ISDN", "ISOM", "JEVE", "LABU", "LANG", "LIFS", "MAED", "MAFS", "MARK", "MASS", "MATH", "MCEE", "MECH", "MESF", "MGCS", "MGMT", "MILE", "MIMT", "MSBD", "MTLE", "OCES", "PDEV", "PHYS", "PPOL", "SBMT", "SHSS", "SOSC", "TEMG", "UROP"]

def check_year_valid(year: str) -> bool:
    consecutive_year = (int(year[:2] + year[5:7]) - int(year[:4]) == 1)
    consecutive_year_century_change = (((int(year[:2]) + 1) * 100 + int(year[5:7]) - int(year[:4])) == 1)
    if not (consecutive_year or consecutive_year_century_change) or re.match(r"\d{4}-\d{2}", year) == None:
        return False
    else:
        return True

def scrape_courses(year: str, season: str):
    # validation rules
    if check_year_valid(year) == False:
        print("Error: year does not exist!")
        return None
    if season.lower() not in seasons:
        print("Error: season does not exist!")
        return None
    current_year = int(year[:4]) + 1
    current_season = season.lower()
    num = 0
    for i in year_list.keys():
        if i[1] == current_season:
            num = year_list[i]
            num += (current_year - i[0]) * 40
            break
    course_list = dict()
    for s in subject_list:
        try:
            subject_course_list = []
            res = requests.get(f"https://w5.ab.ust.hk/wcq/cgi-bin/{str(num)}/subject/{s}")
            res_json = html_to_json.convert(escape(res.text))
            res_json = html_to_json.convert(res_json["_value"])["html"][0]["body"][0]["div"][2]["div"]  # extract html of each course
            # i["div"][0] = course name, i["div"][1] = course info
            for i in res_json:
                course_name = i["div"][0]["a"][0]["_attributes"]["name"]
                desc = ""
                pre_req = []
                co_req = []
                exclusion = []
                table = pd.DataFrame.from_records(i["div"][1]["div"][-1]["div"][0]["table"][0]["tr"])
                for title, val in zip(table["th"], table["td"]):
                    if "_value" not in title[0].keys():
                        continue
                    if title[0]["_value"] == "DESCRIPTION":
                        desc = val[0]["_value"]
                    if title[0]["_value"] == "PRE-REQUISITE":
                        pre_req = val[0]["_value"].split(", ")
                        for j in range(len(pre_req)):
                            if re.match(r"[A-Z]{4} \d{4}[A-Z]{0,1}", pre_req[j]):
                                pre_req[j] = pre_req[j][:4] + pre_req[j][5:]
                    if title[0]["_value"] == "CO-REQUISITE":
                        co_req = val[0]["_value"].split(", ")
                        for j in range(len(co_req)):
                            if re.match(r"[A-Z]{4} \d{4}[A-Z]{0,1}", co_req[j]):
                                co_req[j] = co_req[j][:4] + co_req[j][5:]
                    if title[0]["_value"] == "EXCLUSION":
                        exclusion = val[0]["_value"].split(", ")
                        for j in range(len(exclusion)):
                            if re.match(r"[A-Z]{4} \d{4}[A-Z]{0,1}", exclusion[j]):
                                exclusion[j] = exclusion[j][:4] + exclusion[j][5:]
                subject_course_list.append({course_name: [desc, pre_req, co_req, exclusion]})
            course_list.update({s: subject_course_list})
        except Exception:
            continue
    return course_list

# structure of course_list (dict type):
# access course_list with short form of subject to get list of courses of that subject
# access list with course code to get a list of [description, pre-requisite, co-requisite, exclusion]

def scrape_programs(year: str):
    if check_year_valid(year) == False:
        print("Error: year does not exist!")
        return None
    res = requests.get(f"https://prog-crs.hkust.edu.hk/ugprog/{year}")
    res_json = html_to_json.convert(escape(res.text))
    res_json = html_to_json.convert(res_json["_value"])["html"][0]["body"][0]["div"][3]["div"][0]["div"][1]["div"][1:]
    program_list = {}
    for group in res_json:
        school = group["div"][0]["_value"]
        majors = group["ul"][0]["li"]
        program_list.update({school : [m["a"][0]["div"][1]["_value"] for m in majors]})
    program_req = {}
    for s in program_list.values():
        for program in s:
            r = None
            try:
                p = program.lower()
                if p == "sreq-ssci":
                    p = "ssci_requirements"
                elif p == "sreq-sbm":
                    p = "sbm_requirements"
                r = requests.get(f"https://ugadmin.hkust.edu.hk/prog_crs/ug/{year[0:4] + year[5:7]}/pdf/{year[2:7]}{p}.pdf")
                on_fly_mem_obj = io.BytesIO(r.content)
                pdf_file = pymupdf.open(stream=on_fly_mem_obj, filetype="pdf")
                requirements = []
                for page in pdf_file:
                    t = page.get_text("text").split('\n')
                    requirements.append([line for line in t if (0 < (len(line.split(' ')) <= 10) and (re.search(r"[A-Za-z]{5,6} Requirements", line) == None) and (re.search(r"(\d{4}-\d{2} intake)", line) == None) and (re.search(r"Page \d", line) == None))])
                requirements_dict = {p : [r for req in requirements for r in req]}
                program_req.update(requirements_dict)
            except Exception as e:
                print(f"Exception '{e}' occurred when scraping programs.")

    return program_list, program_req