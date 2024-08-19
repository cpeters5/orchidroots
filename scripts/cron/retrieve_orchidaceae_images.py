#!/usr/local/bin/python3.5
# -*- coding: utf-8 -*-
from __future__ import print_function
import urllib
import pymysql
import time, glob, os, sys
# import mysqlclient
from urllib.request import urlopen
from PIL import Image
from dotenv import load_dotenv
load_dotenv()
current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

size = 500, 400

conn = pymysql.connect(host=os.getenv('DBHOST'), user='chariya', port=3306, passwd=os.getenv('MYDBPSSWD'), db=os.getenv('DBNAME'))
cur = conn.cursor()

type = sys.argv[1]
dir = "/mnt/static/utils/images/"
if type == "spc":
    imgdir = "/mnt/static/utils/images/species/"
    stmthead = "UPDATE orchidaceae_spcimages set image_file = '%s' where id = %d"
    cur.execute(
        "SELECT id, image_url, pid  FROM orchidaceae_spcimages where image_url <>'' and image_url is not null and (image_file is null or image_file = '') and pid >= 0 order by pid")
else:
    imgdir = "/mnt/static/utils/images/hybrid/"
    stmthead = "UPDATE orchidaceae_hybimages set image_file = '%s' where id = %d"
    cur.execute(
        "SELECT id, image_url, pid  FROM orchidaceae_hybimages where image_url <>'' and image_url is not null and (image_file is null or image_file = '') order by pid")

i = 0
for row in cur:
    i = i + 1
    url = row[1]
    pid = row[2]
    if not url or url == '':
        cur.nextset()
    if not pid or pid == '':
        cur.nextset()

    fname = "%s_%09d_%09d.jpg" % (type, row[0], row[2])
    time.sleep(15)

    try:
        local_filename, headers = urllib.request.urlretrieve(url, imgdir + fname)
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

if i > 0:
    print(current_time, "# images ", i)

cur.close()
conn.close()
