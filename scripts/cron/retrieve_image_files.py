#!/usr/local/bin/python3.5
# -*- coding: utf-8 -*-
from __future__ import print_function
import urllib
import pymysql
import shortuuid
import re, glob, os, sys
from pathlib import Path
from urllib.request import urlopen
from PIL import Image

genus = ''
app = sys.argv[1]
tab = app.lower() + "_spcimages"
size = 500, 400
HOST = '134.209.46.210'
conn = pymysql.connect(host=HOST, user='chariya', port=3306, passwd='Imh#r3r3', db='bluenanta')
cur = conn.cursor()
if app != 'other':
    family = app.title()
    imgdir = "/mnt/static/utils/images/" + family + "/"
    Path(imgdir).mkdir(parents=True, exist_ok=True)

stmthead = "UPDATE " + tab + " set image_file = '%s' where id = %d"
stmt = "SELECT id, image_url, genus, family  FROM " + tab + " where image_url <>'' and image_url is not null and (image_file is null or image_file = '') order by id"
print(stmt)
cur.execute(stmt)
i = 0
for row in cur:
    i = i + 1
    print(i)
    if i > 10: exit
    url = row[1]
    if row[3]:
        if app == 'other' or app == 'fungi' or app == 'aves':
            family = row[3].title()
    urlparts = re.search('\/(.*)(\?)?', url)
    a = urlparts.group(1)
    # ext = a.split('.')[-1]
    ext = 'jpg'
    uid = shortuuid.uuid()
    fname = row[2] + '_' + shortuuid.uuid() + "." + ext
    # fname = "%s_%09d_%09d.jpg" % (type, row[0], row[2])

    if not url or url == '':
        print ("Bad", url)
        cur.nextset()

    try:
        # html = urlopen(url)
        if app == 'other' or app == 'fungi':
            imgdir = "/mnt/static/utils/images/" + family + "/"
            Path(imgdir).mkdir(parents=True, exist_ok=True)
        local_filename, headers = urllib.request.urlretrieve(url, imgdir + fname)
        stmt = stmthead % (fname, row[0])
        curinsert = conn.cursor()

        curinsert.execute(stmt)
        conn.commit()
    except urllib.error.URLError as e:
        print("URLError -- ", row[0], e.reason)
        if "Too many requests" in e.reason:
            exit();
        cur.nextset()
    except urllib.error.HTTPError as e:
        print("HTTPError -- ", row[0], e.reason)
        cur.nextset()
    except urllib.error.FileNotFoundError as e:
        print("HTTPError -- ", row[0], e.reason)
        cur.nextset()
    except:
        cur.nextset()

cur.close()
conn.close()
