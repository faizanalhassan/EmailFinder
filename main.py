import os
import csv
import io
import sys
import traceback
import asyncio
import pyppeteer
from pyppeteer import errors
from dotenv import load_dotenv
from pathlib import Path


def get_traceback():
    """Get traceback of current exception"""
    sio = io.StringIO()
    traceback.print_exc(file=sio)
    return sio.getvalue()


get_emails_by_xpath = r"""
function getMailsByXpath(xpath){
    debugger;
    let result = document.evaluate(xpath, document, null,
            XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
    let emails = [], node;
    while(node =result.iterateNext()){
        let email = /(([^<>()\[\]\.,;:\s@"]+(\.[^<>()\[\]\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))/i.exec(node.innerText.replace(/\s/g, ''))?.[0];
        if(!email)
            email = /(([^<>()\[\]\.,;:\s@"]+(\.[^<>()\[\]\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))/i.exec(node.getAttribute('href'))?.[0];
        if(email)
            emails.push(email);
    }
    return emails;
}
"""
href_by_xpath = """
function hrefByXpath(xpath, element=null, scrollIntoView=false) {
    debugger;
    let parent = document;
    if (element) {
        parent = element;
    }
    let node = document.evaluate(xpath, parent, null,
        XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
    if (node) {
        if (scrollIntoView)
            node.scrollIntoView({
                behavior: 'auto',
                block: 'center',
                inline: 'center'
            });
        return (new URL(node.getAttribute('href'), document.baseURI)).href;
    }
    return null;
}
"""
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / "vars.txt")
CHROME_PATH = os.environ['CHROME_PATH']
try:
    MAX_SUB_URLS = int(os.environ['MAX_SUB_URLS'])
except:
    MAX_SUB_URLS = 10
HEADLESS = os.getenv("HEADLESS", 'True').lower() != "false"
try:
    TIMEOUT = float(os.environ["TIMEOUT"])
except:
    TIMEOUT = 120000
xpaths = {
    "email_element": "//*[(contains(@*, '@') or contains(., '@')) and not(./*) and not(name()='style' or name()='script')]",
    "contact_page": "//a[contains(@href, 'contact')]"
}


class EmailFinder:
    def __init__(self) -> None:
        input_file = BASE_DIR / "input.csv"
        output_file = BASE_DIR / "output.csv"
        self.ifh = open(input_file, newline='')
        self.ofh = open(output_file, 'w', newline='')
        self.reader = csv.reader(self.ifh)
        self.writer = csv.writer(self.ofh)
        next(self.reader)  # remove first row
        self.writer.writerow(['brand', 'website', 'emails'])

    def run(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.arun())
        self.ifh.close()
        self.ofh.close()

    async def run_browser(self):
        self.browser = await pyppeteer.launch(
            {
                "headless": HEADLESS,
                "defaultViewport": None,
                "executablePath": CHROME_PATH,
                "args": [
                    # f"--user-data-dir={BASE_DIR / 'cd'}",
                    "--disable-session-crashed-bubble",
                    "--disable-infobars",
                ],
            }
        )

    async def arun(self):
        await self.run_browser()
        self.page = (await self.browser.pages())[0]
        for i, row in enumerate(self.reader):
            try:
                url = str(row[1])
                if not url.startswith("http"):
                    url = "http://" + url
                print(f"Working with '{url}'")
                emails = await self.find_emails(url)
                row.append(str(emails))
                self.writer.writerow(row)
            except KeyboardInterrupt:
                return
            except BaseException as be:
                print(f"Error in row '{i}', type='{type(be)}', traceback='{get_traceback()}'")
                print(f'locals: {sys.exc_info()[2].tb_next.tb_frame.f_locals}')
            finally:
                self.ofh.flush()
        try:
            await self.browser.close()
        except:
            pass

    async def find_emails(self, url):
        print('Working on home page')
        await self.page.goto(url, {"timeout": TIMEOUT})
        emails = await self.page.evaluate(get_emails_by_xpath, xpaths['email_element'])
        if emails:
            print('Found.')
            return emails
        contact_page_url = await self.page.evaluate(href_by_xpath, "//a[contains(@href, 'contact')]")
        all_urls = await self.page.evaluate(
            r"""
function getLinks() {
let anchors = document.querySelectorAll("a"), hrefs= [];
    for(let a of anchors){
        let href = a.getAttribute('href');
        if (href !== '#')
        hrefs.push((new URL(href, document.baseURI)).href)
    }
return hrefs
}
""")
        if contact_page_url:
            print('Working on contact page')
            await self.page.goto(contact_page_url, {"timeout": TIMEOUT})
            emails = await self.page.evaluate(get_emails_by_xpath, xpaths['email_element'])
            if emails:
                print('Found.')
                return emails
        all_urls = list(set(all_urls))
        count = length = len(all_urls)
        if MAX_SUB_URLS > -1:
            count = MAX_SUB_URLS
        i = 0
        while i < count and i < length:
            print(f'Working on sub_url({i})')
            await self.page.goto(all_urls[i], {'timeout': TIMEOUT})
            emails = await self.page.evaluate(get_emails_by_xpath, xpaths['email_element'])
            if emails:
                print(f'Found.')
                return emails
            i += 1


if __name__ == '__main__':
    EmailFinder().run()
