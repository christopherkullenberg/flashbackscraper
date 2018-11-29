#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Usage: 
python flashbackscraper.py <link to thread url>
Example url: https://www.flashback.org/t2975477
Written by: Christopher Kullenberg <christopher.kullenberg@gu.se>
"""
from bs4 import BeautifulSoup
import requests
import re
import sqlite3
import sys
import datetime
import csv

counter = 1

def parsethread(nexturl):
    print("Scraping", nexturl)
    threadnumber = nexturl[26:]
    postidlist = []
    userlist = []
    datelist = []
    timelist = []
    bodylist = []
    inreplylist = []
    r = requests.get(nexturl)
    print(r)
    html = r.content
    soup = BeautifulSoup(html, "lxml")
    #print(soup)
    postbody = soup.findAll("div", class_="post_message")
    username = soup.findAll("li", class_="dropdown-header")
    heading = soup.findAll("div", class_="post-heading")
    titlediv = soup.findAll("div", class_="page-title")
    title = titlediv[0].text
    print("Length: " + str(len(postbody)))
    for p in postbody:
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
            print(match[0][:10])
            timelist.append(match[0][12:])
    for p in postbody:
        bodylist.append(p.text)
    for p in postbody:
        match = re.findall("(?<=Ursprungligen postat av ).*", p.text, 
                           re.IGNORECASE)
        if match:
            inreplylist.append(match[0])
        else:
            inreplylist.append("none")

    print(len(postidlist), len(userlist), len(datelist), len(timelist), 
          len(bodylist), len(inreplylist))
    #print(soup)
    for n in range(0,12):
        print("Adding post", str(((counter * 12) + n) - 12), "to database")
        try:
            cursor.execute('''
            INSERT INTO fb(idnumber, user, date, time, body, inreply, title)
            VALUES(?,?,?,?,?,?,?)''', 
            (postidlist[n], userlist[n], datelist[n], timelist[n], 
             bodylist[n], inreplylist[n], title)
            )
            db.commit()
        except (IndexError, sqlite3.IntegrityError) as e:
             print("\nEnd of thread\nWriting sqlite3 and csv files\nExiting...")
             header = ['rownumber', 'idnumber', 'user', 'date', 
                       'time', 'body', 'inreply', 'title']
             outfile = open(nexturl[26:-2] + ".csv", "w")
             csvWriter = csv.writer(outfile)
             csvWriter.writerow(i for i in header)
             rows = cursor.execute('SELECT * FROM fb')
             csvWriter.writerows(rows)
             outfile.close()
             sys.exit()

def iterator(starturl):
    nexturl = starturl + "p" + str(counter)
    parsethread(nexturl)

if __name__ == '__main__':
    starturl = sys.argv[1]
    try:
        db = sqlite3.connect(starturl[26:] + '.sqlite3')
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE fb(id INTEGER PRIMARY KEY, idnumber TEXT UNIQUE, user TEXT, date TEXT, time TEXT, body TEXT, inreply TEXT, title TEXT)
         ''')
        db.commit()
        while True:
            iterator(starturl)
            print("All done for page:", str(counter), "\n")
            counter += 1
    except sqlite3.OperationalError:
        print("The file", starturl[26:] + 
              ".sqlite3 already exists. Try renaming it first.")
        sys.exit()


