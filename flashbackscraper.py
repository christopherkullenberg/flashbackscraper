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

logo = '''
  ___ _      _   ___ _  _ ___   _   ___ _  _____  ___ ___   _   ___ ___ ___  
 | __| |    /_\ / __| || | _ ) /_\ / __| |/ / __|/ __| _ \ /_\ | _ | __| _ \ 
 | _|| |__ / _  \__ | __ | _ \/ _ | (__| ' <\__ | (__|   // _ \|  _| _||   / 
 |_| |____/_/ \_|___|_||_|___/_/ \_\___|_|\_|___/\___|_|_/_/ \_|_| |___|_|_\ 
                                                                            
'''

print(logo)

text = '''
    \npython flashbackscraper.py <link to thread url>
    Example url: https://www.flashback.org/t2975477
    Written by: Christopher Kullenberg <christopher.kullenberg@gu.se>
'''


parser = argparse.ArgumentParser(description = text)
parser.add_argument("-f", "--file", help="scrape from file containing a list of urls, separated by newline")
parser.add_argument("-u", "--url", help="scrape forum thread from URL")

args = parser.parse_args()


def parsethread(nexturl, cursor, db, mode):
    print("\nScraping page:", nexturl)
    threadnumber = nexturl[26:]
    postidlist = []
    userlist = []
    datelist = []
    timelist = []
    bodylist = []
    inreplylist = []
    r = requests.get(nexturl)
    #print(r)
    html = r.content
    soup = BeautifulSoup(html, "lxml")
    #print(soup)
    postsoup = soup.findAll("div", class_="post_message")
    heading = soup.findAll("div", class_="post-heading")
    titlediv = soup.find("div", class_="page-title")
    title = re.sub(r"[\n\t]*", "", titlediv.text)
    print("---> Thread title:", title)
    username = soup.findAll("li", class_="dropdown-header")
    print("---> Length of page: " + str(len(postsoup)) + " posts.")
    for p in postsoup:
        postid = re.findall("(?<=id\=\"post\_message\_).*?(?=\"\>)", str(p), 
                            re.IGNORECASE)
        if postid:
            postidlist.append(postid[0])
    for u in username:
        if u.text == "Ämnesverktyg":
            continue
        else:
            userlist.append(u.text)
    for h in heading:
        yesterday = datetime.date.today() - datetime.timedelta(1)
        todaymatch = re.findall("Idag,\s\d\d\:\d\d", h.text, re.IGNORECASE)
        yesterdaymatch = re.findall("Igår,\s\d\d\:\d\d", h.text, re.IGNORECASE)
        match = re.findall("\d\d\d\d\-\d\d\-\d\d,\s\d\d\:\d\d", h.text, 
                           re.IGNORECASE)
        if todaymatch:
            datelist.append(datetime.date.today())
            #print(datetime.date.today())
            timelist.append(todaymatch[0][6:])
        elif yesterdaymatch:
            datelist.append(yesterday)
            #print(yesterday)
            timelist.append(yesterdaymatch[0][6:])
        elif match:
            datelist.append(match[0][:10])
            #print(match[0][:10])
            timelist.append(match[0][12:])
    for p in postsoup:
        postbody = re.sub(r"[\n\t]*", "", p.text)
        bodylist.append(postbody)
    for p in postsoup:
        match = re.findall("(?<=Ursprungligen postat av ).*", p.text, 
                           re.IGNORECASE)
        if match:
            inreplylist.append(match[0])
        else:
            inreplylist.append("none")

    #print(len(postidlist), len(userlist), len(datelist), len(timelist), 
    #      len(bodylist), len(inreplylist))
    #print(soup)
    for n in range(0,12):
        #print("Adding post", str(((counter * 12) + n) - 12), "to database")
        try:
            cursor.execute('''
            INSERT INTO fb(idnumber, user, date, time, body, inreply, title)
            VALUES(?,?,?,?,?,?,?)''', 
            (postidlist[n], userlist[n], datelist[n], timelist[n], 
             bodylist[n], inreplylist[n], title)
            )
            db.commit()
        except (IndexError, sqlite3.IntegrityError) as e:
             header = ['rownumber', 'idnumber', 'user', 'date', 
                       'time', 'body', 'inreply', 'title']
             outfile = open(nexturl[26:-2] + ".csv", "w")
             csvWriter = csv.writer(outfile)
             csvWriter.writerow(i for i in header)
             rows = cursor.execute('SELECT * FROM fb')
             csvWriter.writerows(rows)
             outfile.close()
             if mode == "singleurl":
                 sys.exit()
             elif mode == "file":
                 continue
                 #print("Parsethread reports: file mode, continuing...")
            
    return(int(len(postsoup)))

def iterator(starturl, cursor, db, mode):
    urlcounter = 1
    listcounter = 0   
    while True:
        if mode == "singleurl":
            print(starturl)
            #print("Running iterator in single url mode")
            nexturl = starturl + "p" + str(urlcounter)
            parsethread(nexturl, cursor, db, "singleurl")
            urlcounter += 1
        elif mode == "file":
            #print("Running iterator in file mode")
            #print("Urls:\n", str(starturl))
            try:
                nexturl = starturl[listcounter] + "p" + str(urlcounter)
                #print("Next url to crawl: " + nexturl)
                if parsethread(nexturl, cursor, db, "file") == 12:
                    urlcounter += 1
                    #print("Scraping a full page")
                elif parsethread(nexturl, cursor, db, "file") != 12:
                    #print("Scraping partial page. Continuing to next url.")
                    urlcounter = 1
                    listcounter +=1
            except IndexError:
                print("\n\n*** No more URLs, done! ***")
                sys.exit()

def startscraping(url, cursor, db, mode):
    print("Startscraping reports mode:", mode)
    #counter = 1
    while True:
        #print("Scraping page:", str(counter), "\n")
        #counter += 1
        iterator(url, cursor, db, mode)


def createdatabase(starturl, mode):
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
            CREATE TABLE fb(id INTEGER PRIMARY KEY, idnumber TEXT UNIQUE, user TEXT, date TEXT, time TEXT, body TEXT, inreply TEXT, title TEXT)
         ''')
        db.commit()
        if mode == "singleurl":
            print("Starting scraper for url mode")
            startscraping(starturl, cursor, db, "singleurl")
        elif mode == "file":
            print("Starting scraper for file mode")
            for url in starturl:
                print(url)
                startscraping(starturl, cursor, db, "file")
    except sqlite3.OperationalError:
        print("The file", filenameurl +
              ".sqlite3 already exists. Try renaming it first.")
        sys.exit()




if __name__ == '__main__':
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
