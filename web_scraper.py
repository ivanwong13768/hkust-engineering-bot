import requests, html_to_json, re, pandas as pd
from xml.sax.saxutils import escape

year_list = {(2024, "fall") : 2310, (2024, "winter") : 2320, (2024, "spring") : 2330, (2024, "summer") : 2340}
seasons = ["fall", "winter", "spring", "summer"]
subject_list = ["ACCT", "AESF", "BEHI", "BIEN", "BTEC", "CENG", "CHEM", "CIEM", "CIVL", "COMP", "CPEG", "CSIT", "ECON", "EEMT", "EESM", "ELEC", "EMBA", "EMIA", "ENEG", "ENGG", "ENTR", "ENVR", "EVSM", "FINA", "GFIN", "GNED", "HLTH", "HMMA", "HUMA", "IBTM", "IDPO", "IEDA", "IMBA", "ISDN", "ISOM", "JEVE", "LABU", "LANG", "LIFS", "MAED", "MAFS", "MARK", "MASS", "MATH", "MCEE", "MECH", "MESF", "MGCS", "MGMT", "MILE", "MIMT", "MSBD", "MTLE", "OCES", "PDEV", "PHYS", "PPOL", "SBMT", "SHSS", "SOSC", "TEMG", "UROP"]

def scrape(year: str, season: str):
    # validation rules
    consecutive_year = (int(year[:2] + year[5:7]) - int(year[:4]) == 1)
    consecutive_year_century_change = (((int(year[:2]) + 1) * 100 + int(year[5:7]) - int(year[:4])) == 1)
    if not (consecutive_year or consecutive_year_century_change) or re.match(r"\d{4}-\d{2}", year) == None:
        print("Error: year does not exist")
        return None
    if season.lower() not in seasons:
        print("Error: season does not exist")
        return None
    current_year = int(year[:4]) + 1
    current_season = season.lower()
    num = 0
    for i in year_list.keys():
        if i[1] == current_season:
            num = year_list[i]
            num += (current_year - i[0]) * 40
            break
    course_list = []
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
                    if title[0]["_value"] == "CO-REQUISITE":
                        co_req = val[0]["_value"].split(", ")
                    if title[0]["_value"] == "EXCLUSION":
                        exclusion = val[0]["_value"].split(", ")
                subject_course_list.append({course_name: [desc, pre_req, co_req, exclusion]})
            course_list.append({s: subject_course_list})
        except Exception:
            continue
    return course_list

# structure of course_list (dict type):
# access course_list with short form of subject to get list of courses of that subject
# access list with course code to get a list of [description, pre-requisite, co-requisite, exclusion]