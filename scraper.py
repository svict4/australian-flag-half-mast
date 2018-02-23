# This is a template for a Python scraper on morph.io (https://morph.io)

from bs4 import BeautifulSoup
import requests
import re
import sqlite3
from dateutil.parser import parse

PMCTLD = "http://pmc.gov.au"
FLAGNETWORKLINK = "/government/australian-national-flag/flag-network"

STATES_ABBR = ["Australia-wide", "ACT", "NSW", "QLD", "SA", "TAS", "NT", "WA", "VIC"]
STATES_FULL = ["australia wide", "australian capital territory", "new south wales", "queensland", "south australia", "tasmania", "northern territory", "western australia", "victoria"]
states_list = dict(zip(STATES_FULL, STATES_ABBR))
states_pattern = re.compile(r"\b(?:ACT|NT|SA|WA|NSW|QLD|VIC|TAS|(?:Australian Capital|Northern) Territory|(?:South|Western) Australia|New South Wales|Queensland|Victoria|Tasmania|Australia(?: |-)wide)\b", re.IGNORECASE)
halfMast_pattern = re.compile(r"half(?: |-)mast", re.IGNORECASE)

rFlagNetwork = requests.get(PMCTLD + FLAGNETWORKLINK)
soup = BeautifulSoup(rFlagNetwork.content, "html.parser")

pages = int(soup.select("#block-system-main > div > div > div > div.item-list > ul > li.pager-last.last > a")[0].attrs['href'].split("=")[1]) + 1

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
        print("scraping ", str(page + 1), "of", str(pages), "pages")
        if page != 0:
            rFlagNetwork = requests.get(PMCTLD + FLAGNETWORKLINK + "?page=" + str(page))
            soup = BeautifulSoup(rFlagNetwork.content, "html.parser")

        # weird bug when combinding css selector, so I've just split it into two
        page_content1 = soup.select("#block-system-main > div > div > div > div.view-content > div.views-row > div.views-field.views-field-title > h2 > a")
        page_content2 = soup.select("#block-system-main > div > div > div > div.view-content > div.views-row > div.views-field.views-field-field-action-date > h3 > span")
        page_content = page_content1 + page_content2

        for i in range(-(-len(page_content) // 2)):
            content = page_content[i::-(-len(page_content) // 2)]
            all_announcements.append({'title': content[0].get_text(strip=True), 'link': content[0].attrs['href'], 'date': content[1].get_text(strip=True)})

# ∀ announcements, get the extra info from the headings (where does it apply, half-mast or not)
def scrape_individual_announcements(announcement):
    print("scraping", announcement['link'])
    rFlagNetwork = requests.get(PMCTLD + announcement['link'])
    soup = BeautifulSoup(rFlagNetwork.content, "html.parser")

    announcement['locality'], announcement['halfMast'] = '', ''

    locality = soup.select(".node-flag-alert > div.content.clearfix > div.field.field-name-field-salutation.field-type-text.field-label-hidden > div > div")
    if locality:
        locality_text = locality[0].get_text(strip=True)
        #if not is_date(locality_text):
        matches = re.findall(states_pattern, locality_text)
        announcement['locality'] = ','.join([states_list.get(item.lower(), item) for item in matches])
        announcement['halfMast'] = int(bool(re.search(halfMast_pattern, locality_text)))

    context = soup.select(".node-flag-alert > div.content.clearfix > div.field.field-name-field-alert-sub-title.field-type-text.field-label-hidden > div > div")  
    if context and not announcement['halfMast']:
        announcement['halfMast'] = int(bool(re.search(halfMast_pattern, context[0].get_text(strip=True))))

scrape_pages(soup)
for announcement in all_announcements:
     scrape_individual_announcements(announcement)

con = sqlite3.connect("data.sqlite")
cur = con.cursor()
cur.execute("DROP TABLE IF EXISTS `data`")
cur.execute("""CREATE TABLE `data` ( 
        title TEXT NOT NULL,
        link TEXT NOT NULL PRIMARY KEY,
        actionDate TEXT NOT NULL,
        locality TEXT,
        halfMast BOOL NOT NULL
    )""")

data = [tuple(i.values()) for i in all_announcements]
cur.executemany("""
    INSERT INTO data (
        title, link, actionDate, locality, halfMast
    ) VALUES (
        :text, :link, :actionDate, :locality, :halfMast
    )""", data)

con.commit()
cur.close()
con.close()
