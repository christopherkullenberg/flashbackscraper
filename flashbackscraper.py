#!/usr/bin/python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import re
import sqlite3
import sys, getopt
import datetime
import csv
import argparse
import random

logo = '''
  ___ _      _   ___ _  _ ___   _   ___ _  _____  ___ ___   _   ___ ___ ___  
 | __| |    /_\ / __| || | _ ) /_\ / __| |/ / __|/ __| _ \ /_\ | _ | __| _ \ 
 | _|| |__ / _  \__ | __ | _ \/ _ | (__| ' <\__ | (__|   // _ \|  _| _||   / 
 |_| |____/_/ \_|___|_||_|___/_/ \_\___|_|\_|___/\___|_|_/_/ \_|_| |___|_|_\ 

    Written by Christopher Kullenberg <christopher.kullenberg@gu.se>
'''
print(logo)

text = '''
    \npython flashbackscraper.py <link to thread url>
    Example url: https://www.flashback.org/t2975477
'''

parser = argparse.ArgumentParser(description = text)
parser.add_argument("-f", "--file", 
                    help="scrape from file containing a list of urls, separated\                    by newline")
parser.add_argument("-u", "--url", help="scrape forum thread from URL")
parser.add_argument("-s", "--subforum", help="scrape an entire subforum")
parser.add_argument("-t", "--tor", help="run scraper though Tor proxy on\
                    on localhost:9050 (socks5 proxy)", action="store_true")
args = parser.parse_args()

previouslyaddedbody = []
usetor = False # the -t argument switches this on.
user_agent_list = [] # fills up with user agents from 'user_agents.txt'

with open("user_agents.txt", "r") as uafile:
    agents = uafile.readlines()
    for a in agents:
        user_agent_list.append(a.strip("\n"))

def parsethread(nexturl, cursor, db, mode):
    '''This is the main parser for flashback threads. It receives URLs from\
    iterator(), then extracts content and meta-data of each post before\
    saving it all to a common sqlite3 database. For each thread, it also\
    saves a csv file. Sorry for the ugly complexity of this function...'''
    print("\nScraping page:", nexturl)
    threadnumber = nexturl[26:]
    # Create arrays of data containing parsed page content:
    postidlist = []
    userlist = []
    datelist = []
    timelist = []
    bodylist = []
    inreplylist = []
    pathlist = []
    # Get and parse html:
    global usetor # Check if Tor mode is on or off
    global user_agent_list # get large list of various headers
    user_agent = random.choice(user_agent_list)
    headers = {'User-Agent': user_agent}
    print("Using header:", headers)
    if usetor == True:
        print("---> Running in Tor mode!")
        try:
            session = requests.session()
            session.proxies['https'] = 'socks5h://localhost:9050' # requires Tor
            r = session.get(nexturl, headers=headers)
        except: #there are multiple errors for a Tor conn to go wrong
            print("There was an ERROR with TOR. Proceeding to next url")
            with open("failed_urls.txt", "a") as failfile:
                failfile.write(nexturl + "\n") # record failed urls
            return(9000)
    elif usetor == False:
        r = requests.get(nexturl, headers=headers)
    html = r.content
    soup = BeautifulSoup(html, "lxml")
    # Extract the posts and their headings
    postsoup = soup.findAll("div", class_="post_message")
    heading = soup.findAll("div", class_="post-heading")
    # Extract all moderator messages
    modsoup = soup.findAll("div", class_="panel panel-warning panel-form")
    try:
        titlediv = soup.find("div", class_="page-title")
        title = re.sub(r"[\n\t]*", "", titlediv.text) # clean out tab, newlines
    except:
        title = "<error getting title>" # if title extraction fails.
    print("---> Thread title:", title)
    # If length == 12 it is a full page:
    print("---> Length of page: " + str(len(postsoup)) + " posts.")
    for p in postsoup:
        postid = re.findall("(?<=id\=\"post\_message\_).*?(?=\"\>)", str(p), 
                            re.IGNORECASE)
        if postid:
            postidlist.append(postid[0])
    # Extract usernames:     
    username = soup.findAll("li", class_="dropdown-header")
    for u in username:
        if u.text == "Ämnesverktyg": # exclude false positive.
            continue
        else:
            userlist.append(u.text)
    # Datetime extractor
    for h in heading:
        yesterday = datetime.date.today() - datetime.timedelta(1)
        todaymatch = re.findall("Idag,\s\d\d\:\d\d", h.text, re.IGNORECASE)
        yesterdaymatch = re.findall("Igår,\s\d\d\:\d\d", h.text, re.IGNORECASE)
        match = re.findall("\d\d\d\d\-\d\d\-\d\d,\s\d\d\:\d\d", h.text, 
                           re.IGNORECASE)
        if todaymatch:
            datelist.append(datetime.date.today())
            timelist.append(todaymatch[0][6:])
        elif yesterdaymatch:
            datelist.append(yesterday)
            timelist.append(yesterdaymatch[0][6:])
        elif match:
            datelist.append(match[0][:10])
            timelist.append(match[0][12:])
    for p in postsoup:
        postbody = re.sub(r"[\n\t]*", "", p.text) # clean out tab, newlines
        bodylist.append(postbody)
    checksum = int(len(bodylist))+int(len(modsoup)) # This val returns to iterator() 

    global previouslyaddedbody # fetch global variable, see top of this file.
    if bodylist == previouslyaddedbody: # test if previous page is identical.
        print("Found duplicate page, exiting or continuing to next url")
        checksum = 9000  # return a fake number to break the loop
    else: 
        print("OK")
    for p in postsoup:
        match = re.findall("(?<=Ursprungligen postat av ).*", p.text, 
                           re.IGNORECASE)
        if match:
            inreplylist.append(match[0])
        else:
            inreplylist.append("none")
    # And now add to database: 
    for n in range(0,len(bodylist)):

        try:
            cursor.execute('''
            INSERT INTO fb(idnumber, user, date, time, body, 
                           inreply, title, path)
            VALUES(?,?,?,?,?,?,?,?)''', 
            (postidlist[n], userlist[n], datelist[n], timelist[n], 
             bodylist[n], inreplylist[n], title, str(parseforumstructure(soup)))
            )
            db.commit()
        except (IndexError, sqlite3.IntegrityError) as e:
            '''If database writing fails, An indexerror means no more posts, 
            a sqlite3.IntegrityError means the database found a duplicate 
            idnumber, then a .csv file is written
            and the script exits.''' 
            if mode == "singleurl":
                 header = ['rownumber', 'idnumber', 'user', 'date', 
                           'time', 'body', 'inreply', 'title', 'path']
                 outfile = open(nexturl[26:-2] + ".csv", "w")
                 csvWriter = csv.writer(outfile)
                 csvWriter.writerow(i for i in header)
                 rows = cursor.execute('SELECT * FROM fb') # All data from db
                 csvWriter.writerows(rows)
                 outfile.close()
                 sys.exit()
            else: # If file or subforum mode is selected, just continue.
                 continue
    previouslyaddedbody = bodylist # Fills global variable with the current data
    return(checksum) # Finally, return to iterator() the checksum value.

def parseforumstructure(soup):
    pathdiv = soup.find("div", class_="form-group")
    pathdata = pathdiv.findAll("option")
    pathlist = []
    for p in pathdata:
        if p.text != "Detta ämne":
            pathlist.append(p.text)
    return(pathlist)

def parsesubforum(subforumurl):
    '''This is a special function that crawls through a subforum in order to 
    find thread urls. Once it has interated through all the pages listing thread
    urls and writing them to a file, it closes the file and exits.'''
    iterator = 1
    outfile = open(subforumurl[26:] + ".txt", "w")
    while True:
        currenturl = subforumurl + "p" + str(iterator)
        r = requests.get(currenturl)
        html = r.content
        soup = BeautifulSoup(html, "lxml")
        print("Collecting threads from", currenturl)
        topics = soup.findAll('a', id=re.compile("thread_title_\d"))
        print("Found " + str(len(topics)) + " threads")
        if len(topics) >= 50:
            for t in topics:
                threadurl = 'https://flashback.org' + t.get('href')
                print(threadurl)
                outfile.write(threadurl + "\n")
            iterator += 1
        elif len(topics) < 50:
            for t in topics:
                threadurl = 'https://flashback.org' + t.get('href')
                print(threadurl)
                outfile.write(threadurl + "\n")
            print("Done, writing to file and exiting")
            outfile.close()
            print('''\n You can now run python3 flashbackscraper.py -f ''' 
                  + subforumurl[26:] + '''.txt''')
            sys.exit()
 
def iterator(starturl, cursor, db, mode):
    '''This function makes possible to go through all urls in a thread. It 
    takes the first url of a thread, then simply adds "p[n]", where n = a number    increasing by 1 until it receives a number which is either less than 12 or 
    the error message 9000.'''
    urlcounter = 1
    listcounter = 0   
    while True:
        if mode == "singleurl":
            print(starturl)
            nexturl = starturl + "p" + str(urlcounter)
            parsethread(nexturl, cursor, db, "singleurl")
            urlcounter += 1
        elif mode == "file":
            try:
                nexturl = starturl[listcounter] + "p" + str(urlcounter)
                if parsethread(nexturl, cursor, db, "file") == 12:
                    urlcounter += 1
                    print("Scraping a full page")
                elif parsethread(nexturl, cursor, db, "file") < 12:
                    print("Scraping partial page. Continuing to next url.")
                    urlcounter = 1
                    listcounter += 1
                elif parsethread(nexturl, cursor, db, "file") == 9000:
                    print("Error 9000: Duplicate, lets move on")
                    urlcounter = 1
                    listcounter += 1
            except IndexError:
                print("\n\n*** No more URLs, done! ***")
                sys.exit()

def startscraping(url, cursor, db, mode):
    '''This function just starts the scraper by triggering the iterator'''
    print("Startscraping reports mode:", mode)
    while True:
        iterator(url, cursor, db, mode)

def createdatabase(starturl, mode):
    '''This function creates a database, then starts the scraper differently\
       depending on mode'''
    if mode == "singleurl":
        print("Creating database for url mode")
        filenameurl = starturl[26:] 
    elif mode == "file":
        print("Creating database for file mode")
        filenameurl = "from_file"
    try:
        db = sqlite3.connect(filenameurl + '.sqlite3')
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE fb(id INTEGER PRIMARY KEY, idnumber TEXT UNIQUE,\
            user TEXT, date TEXT, time TEXT, body TEXT, inreply TEXT,\
             title TEXT, path TEXT)
            ''')
        db.commit()
        if mode == "singleurl":
            print("Starting scraper in url mode")
            startscraping(starturl, cursor, db, "singleurl")
        elif mode == "file":
            print("Starting scraper in file mode")
            for url in starturl:
                print(url)
                startscraping(starturl, cursor, db, "file")
    except sqlite3.OperationalError:
        print("The file", filenameurl +
              ".sqlite3 already exists. Try renaming it first.")
        sys.exit()

if __name__ == '__main__':
    if args.tor:
        usetor = True
        testsession = requests.session()
        testsession.proxies['https'] = 'socks5h://localhost:9050'
        testr = testsession.get("https://httpbin.org/ip")
        print("Fetching Tor IP once for testing...")
        print(testr.text)
        print("If the IP above is your real IP, Tor mode has failed")
    if args.url:
        createdatabase(args.url, "singleurl")
    elif args.file:
        print("Reading urls from file...")
        urlfile = open(args.file, "r")
        lines = urlfile.readlines()
        lines = list(map(lambda s: s.strip(), lines))
        print("Loaded urls:\n")
        crawlurlcounter = 1
        for l in lines:
            print("\t" + str(crawlurlcounter) + ". " + l)
            crawlurlcounter += 1
        print("\n")
        createdatabase(lines, "file")
    elif args.subforum:
        parsesubforum(args.subforum)
