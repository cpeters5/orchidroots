#!/usr/local/bin/python3.5
# -*- coding: utf-8 -*-
from __future__ import print_function
import urllib
import pymysql
import shortuuid
import re
from pathlib import Path

genus = ''
family = 'Cactaceae'
tab = "cactaceae_spcimages"

# import mysqlclient
from urllib.request import urlopen
from PIL import Image
import glob, os, sys

size = 500, 400
HOST = '134.209.93.40'
conn = pymysql.connect(host=HOST, user='chariya', port=3306, passwd='Imh#r3r3', db='orchiddev')
cur = conn.cursor()

imgdir = "/mnt/static/utils/images/" + family + "/"
Path(imgdir).mkdir(parents=True, exist_ok=True)

stmthead = "UPDATE " + tab + " set image_file = '%s' where id = %d"
cur.execute(
    "SELECT id, image_url, genus  FROM cactaceae_spcimages where image_url <>'' and image_url is not null and (image_file is null or image_file = '') and genus is not null and genus <> '' order by id")

i = 0
for row in cur:
    i = i + 1
    url = row[1]
    urlparts = re.search('\/(.*)(\?)?', url)
    a = urlparts.group(1)
    ext = a.split('.')[-1]
    uid = shortuuid.uuid()
    fname = row[2] + '_' + shortuuid.uuid() + "." + ext
    if not url or url == '':
        print ("Bad", url)
        cur.nextset()

    try:
        local_filename, headers = urllib.request.urlretrieve(url, imgdir + fname)
    except urllib.error.URLError as e:
        print("URLError -- ", row[0], e.reason)
        cur.nextset()
    except urllib.error.HTTPError as e:
        print("HTTPError -- ", row[0], e.reason)
        cur.nextset()
    except:
        print("?Error -- ", row[0])
        cur.nextset()

    stmt = stmthead % (fname, row[0])
    curinsert = conn.cursor()

    curinsert.execute(stmt)
    conn.commit()
# print (stmt)


cur.close()
conn.close()
