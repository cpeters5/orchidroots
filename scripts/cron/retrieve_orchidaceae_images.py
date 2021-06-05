#!/usr/local/bin/python3.5
# -*- coding: utf-8 -*-
from __future__ import print_function
import urllib
import pymysql
# import mysqlclient
from urllib.request import urlopen
from PIL import Image
import glob, os, sys

size = 500, 400

HOST = '134.209.46.210'
conn = pymysql.connect(host=HOST, user='chariya', port=3306, passwd='Imh#r3r3', db='bluenanta')
# conn = pymysql.connect(host='134.209.46.210', user='chariya', port=3306, passwd='Imh#r3r3', db='orchiddev')
cur = conn.cursor()

type = sys.argv[1]
# type = "hyb"
print(type)
# dir = "C:/projects/orchids/bluenanta/utils/static/utils/images/"
dir = "/mnt/static/utils/images/"
if type == "spc":
    # thumbdir = dir +"species_thumb/"
    imgdir = dir + "species/"
    stmthead = "UPDATE orchidaceae_spcimages set image_file = '%s' where id = %d"
    cur.execute(
        "SELECT id, image_url, pid  FROM orchidaceae_spcimages where image_url <>'' and image_url is not null and (image_file is null or image_file = '') and pid >= 0 order by pid")
else:
    # thumbdir = dir + "hybrid_thumb/"
    imgdir = dir + "hybrid/"
    stmthead = "UPDATE orchidaceae_hybimages set image_file = '%s' where id = %d"
    cur.execute(
        "SELECT id, image_url, pid  FROM orchidaceae_hybimages where image_url <>'' and image_url is not null and (image_file is null or image_file = '') order by pid")

# print(cur.description)

# thumbdir = "thumb/"
# imgdir = "download/"

i = 0
for row in cur:
    i = i + 1
    # if i >2:
    # break
    url = row[1]
    pid = row[2]
    if not url or url == '':
        # print ("Bad", url)
        cur.nextset()
    if not pid or pid == '':
        # print ("Bad", url)
        cur.nextset()

    fname = "%s_%09d_%09d.jpg" % (type, row[0], row[2])
    print(fname)

    try:
        print(url)
        # html = urlopen(url)
        local_filename, headers = urllib.request.urlretrieve(url, imgdir + fname)
        # print("True",url,html.read(),"\n")
        print(">>", local_filename, headers, "\n\n\n")
    except urllib.error.URLError as e:
        print("URLError -- ", row[0], e.reason)
        cur.nextset()
    except urllib.error.HTTPError as e:
        print("HTTPError -- ", row[0], e.reason)
        cur.nextset()
    except urllib.error.FileNotFOundError as e:
        print("HTTPError -- ", row[0], e.reason)
        cur.nextset()
    except:
        print("? Error -- ", row[0])
        cur.nextset()
    stmt = stmthead % (fname, row[0])
    curinsert = conn.cursor()

    curinsert.execute(stmt)
    conn.commit()
# print (stmt)


cur.close()
conn.close()
