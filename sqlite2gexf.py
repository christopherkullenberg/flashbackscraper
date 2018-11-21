#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: christopher.kullenberg@gu.se
# Usage: python sqlite2gexf.py <sqlite3 file>

import networkx as nx
import sqlite3
import sys

filename = sys.argv[1]

db = sqlite3.connect(filename)
cursor = db.cursor()

selectedges = cursor.execute('SELECT user, inreply FROM fb')
edges = cursor.fetchall()

G = nx.DiGraph()

for e in edges:
    if e[1] == 'none':
         continue
    else:
         print(e[0], e[1])
         G.add_edge(e[0], e[1])

outfilename = filename[:8] + ".gexf"
print("\nSaving Gexf-file as", outfilename, "Have fun mapping networks!")
nx.write_gexf(G, outfilename)
