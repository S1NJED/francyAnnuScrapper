import requests
import openpyxl
from bs4 import BeautifulSoup
from time import time
import sqlite3


class Annuaire:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        }
        self.prefixes = []

    
    def getPrefixes(self):
        print("getPrefixes method")
        url = "https://francy-annu.com/fr.php"

        req = self.session.get(url)

        soup = BeautifulSoup(req.text, "html.parser")

        for elem in soup.select("div > ul[role='menu']:nth-of-type(1) > li"):
            self.prefixes.append({
                'letter': ''.join(i for i in elem.select_one("a").text.strip().replace('\n', '') if i.isalpha() or i == '-') ,
                'amount': int(elem.select_one("a > span").text.strip())
            })

    def getAvailableLinksFromPrefix(self, prefix):
        print(f"[{prefix}] getAvailableLinksFromPrefix")
        url = f"https://francy-annu.com/fr.php?q={prefix}"

        req = self.session.get(url)
        
        soup = BeautifulSoup(req.text, "html.parser")

        links = [f"https://francy-annu.com/{elem.attrs.get("href").replace('\n', '')}" for elem in soup.select("button > a")]

        return links

    def getProspectFromLink(self, url):
        print(f"getProspectFromLink")
        req = self.session.get(url)

        soup = BeautifulSoup(req.text, "html.parser")

        prospects = []

        for elem in soup.select("div.wrapper > div"):
            # We check if it's not a div ad
            if elem.attrs.get('class') is None: continue

            # First we check if it's not an empty div
            try:
                if elem.select_one("div > div.panel-body > h2").text.replace(' ', '') == '': continue
            except:
                continue

            # We can then append to the array
            basePath = "div > div.panel-body"
            addr = elem.find(f"p").decode_contents().split('<br/>')
            
            postal_code = addr[-1][:5]
            city = addr[-1][6:]

            prospects.append({
                "name": elem.select_one(f"{basePath} > h2").text,
                "number": elem.select_one(f"{basePath} > label").text,
                "address": addr[1],
                "postal_code": postal_code,
                "city": city
            })

        return prospects

    # TODO: add requests multithreads
    def start(self):
        print("starting")
        """ Flow
        1. Get prefixes
        2. for each prefix
            2.1 Get available links
                2.1.1 Get prospect add to db etc
        """

        self.getPrefixes()

        for prefix in self.prefixes:
            links = self.getAvailableLinksFromPrefix(prefix['letter'])

            for link in links:
                start_time = time()
                prospects = self.getProspectFromLink(link)

                conn = sqlite3.connect("bdd.sqlite")
                
                for prospect in prospects:

                    try:
                        conn.execute(
                            "INSERT INTO prospects VALUES(?,?,?,?,?)", 
                            (prospect['name'],prospect['number'],prospect['address'],prospect['postal_code'],prospect['city'])
                        )
                    except sqlite3.IntegrityError:
                        pass

                conn.commit()
                conn.close()

                print(f"[{prefix['letter']}] - Added {len(prospects)} prospects in {time() - start_time} seconds")


if __name__ == '__main__':
    st = time()
    Annuaire().start()
    print(f"Total: {time() - st} seconds")
