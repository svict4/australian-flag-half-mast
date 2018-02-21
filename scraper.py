# This is a template for a Python scraper on morph.io (https://morph.io)

from bs4 import BeautifulSoup
import requests
import re
import scraperwiki
from dateutil.parser import parse

PMCTLD = "http://pmc.gov.au"
FLAGNETWORKLINK = "/government/australian-national-flag/flag-network"

STATES_ABBR = ["australia-wide", "act", "nsw", "qld", "sa", "tas", "nt", "wa", "vic"]
STATES_FULL = ["australia wide", "australian capital territory", "new south wales", "queensland", "south australia", "tasmania", "northern territory", "western australia", "victoria"]
states_list = zip(STATES_ABBR, STATES_FULL)
states_pattern = re.compile(r"\b(ACT|NT|SA|WA|NSW|QLD|VIC|TAS|(Australia Capital|Northern) Territory|(South|Western) Australia|New South Wales|Queensland|Victoria|Tasmania|Australia( |-)wide)\b", re.IGNORECASE)

rFlagNetwork = requests.get(PMCTLD + FLAGNETWORKLINK)
soup = BeautifulSoup(rFlagNetwork.content, "html.parser")

pages = int(soup.select("#block-system-main > div > div > div > div.item-list > ul > li.pager-last.last > a")[0].attrs['href'].split("=")[1])

all_announcements = [] # pipe this into the sqlite db for morph.io

def is_date(string):
    try:
        parse(string, fuzzy=True)
        return True
    except ValueError as e:
        if e.args[0] == "String does not contain a date.":
            return False
        return True # assume true, so it doesn't mess with the final data

# on every page, get the title/link/dates of every announcement
def scrape_pages(soup):
    for page in range(pages):
        if page != 0:
            rFlagNetwork = requests.get(PMCTLD + FLAGNETWORKLINK + "?page=" + str(page))
            soup = BeautifulSoup(rFlagNetwork.content, "html.parser")

        page_content1 = soup.select("#block-system-main > div > div > div > div.view-content > div.views-row > div.views-field.views-field-title > h2 > a")
        page_content2 = soup.select("#block-system-main > div > div > div > div.view-content > div.views-row > div.views-field.views-field-field-action-date > h3 > span")

        page_content = page_content1 + page_content2

        for i in range(-(-len(page_content) // 2)):
            content = page_content[i::-(-len(page_content) // 2)]
            all_announcements.append({'title': content[0].get_text(strip=True), 'link': content[0].attrs['href'], 'date': content[1].get_text(strip=True)})

# ∀ announcements, get the extra info from the headings (where does it apply, half-mast or not)
def scrape_individual_announcements(announcement):

    rFlagNetwork = requests.get(PMCTLD + announcement['link'])
    soup = BeautifulSoup(rFlagNetwork.content, "html.parser")

    announcement['context'], announcement['locality'], announcement['halfMast'] = '', [], False

    context = soup.select(".node-flag-alert > div.content.clearfix > div.field.field-name-field-alert-sub-title.field-type-text.field-label-hidden > div > div")  
    if context:
        context_text = context[0].get_text(strip=True)
        if not is_date(context_text):
            announcement['context'] = context_text
            if context_text.lower().find("half-mast") or context_text.lower().find("half mast"):
                announcement['halfMast'] = True
    
    locality = soup.select(".node-flag-alert > div.content.clearfix > div.field.field-name-field-salutation.field-type-text.field-label-hidden > div > div")
    if locality:
        locality_text = locality[0].get_text(strip=True)
        if not is_date(locality_text):
            matches = re.findall(states_pattern, locality_text)
            announcement['locality'] = [x if x not in dict(states_list) else dict(states_list)[x] for x in matches]
        
        # if not is_date(locality_text):
        #     matches = [x for x in (STATES_FULL + STATES_ABBR) if x in locality_text.lower().split()]
        #     # clean the values so they're ABBRs
        #     matches = [x if x not in dict(states_list) else dict(states_list)[x] for x in matches]
        #     # [x[0] for x in list(zip(STATES_ABBR, STATES_FULL))]
        #     announcement['locality'] = matches

scrape_pages(soup)
for announcement in all_announcements:
     scrape_individual_announcements(announcement)

scraperwiki.sqlite.save(['link'], all_announcements)