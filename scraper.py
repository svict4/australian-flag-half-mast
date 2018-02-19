# This is a template for a Python scraper on morph.io (https://morph.io)
# including some code snippets below that you should find helpful

from bs4 import BeautifulSoup
import requests

PMCTLD = "http://pmc.gov.au"
FLAGNETWORKLINK = "http://pmc.gov.au/government/australian-national-flag/flag-network"

rFlagNetwork = requests.get(FLAGNETWORKLINK)
soup = BeautifulSoup(rFlagNetwork.content, "html.parser")

pages = int(soup.select("#block-system-main > div > div > div > div.item-list > ul > li.pager-last.last > a")[0].attrs['href'].split("=")[1])

all_announcements = []
for page in range(pages):
    if page != 0:
        rFlagNetwork = requests.get(FLAGNETWORKLINK + "?page=" + str(page))
        soup = BeautifulSoup(rFlagNetwork.content, "html.parser")

    page_content1 = soup.select("#block-system-main > div > div > div > div.view-content > div.views-row > div.views-field.views-field-title > h2 > a")
    page_content2 = soup.select("#block-system-main > div > div > div > div.view-content > div.views-row > div.views-field.views-field-field-action-date > h3 > span")

    page_content = page_content1 + page_content2

    for i in range(-(-len(page_content) // 2)):
        content = page_content[i::-(-len(page_content) // 2)]
        all_announcements.append({'title': content[0].get_text(strip=True), 'link': content[0].attrs['href'], 'date': content[1].get_text(strip=True)})

for announcement in all_announcements:
    rFlagNetwork = requests.get(PMCTLD + announcement['link'])
    soup = BeautifulSoup(rFlagNetwork.content, "html.parser")

    announcement['context'], announcement['locality'] = '', ''

    context = soup.select(".node-flag-alert > div.content.clearfix > div.field.field-name-field-alert-sub-title.field-type-text.field-label-hidden > div > div")
    if context:
        announcement['context'] = context[0].get_text(strip=True)
    locality = soup.select(".node-flag-alert > div.content.clearfix > div.field.field-name-field-salutation.field-type-text.field-label-hidden > div > div")
    if locality:
        announcement['locality'] = locality[0].get_text(strip=True)

i = 0

# import scraperwiki
# import lxml.html
#
# # Read in a page
# html = scraperwiki.scrape("http://foo.com")
#
# # Find something on the page using css selectors
# root = lxml.html.fromstring(html)
# root.cssselect("div[align='left']")
#
# # Write out to the sqlite database using scraperwiki library
# scraperwiki.sqlite.save(unique_keys=['name'], data={"name": "susan", "occupation": "software developer"})
#
# # An arbitrary query against the database
# scraperwiki.sql.select("* from data where 'name'='peter'")

# You don't have to do things with the ScraperWiki and lxml libraries.
# You can use whatever libraries you want: https://morph.io/documentation/python
# All that matters is that your final data is written to an SQLite database
# called "data.sqlite" in the current working directory which has at least a table
# called "data".
