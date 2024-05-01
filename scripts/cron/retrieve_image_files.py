#!/usr/local/bin/python3.5
# -*- coding: utf-8 -*-
from __future__ import print_function
import urllib
from urllib.parse import urlparse, parse_qs
import pymysql
import shortuuid
import re, glob, os, sys
from pathlib import Path
from urllib.request import urlopen
from PIL import Image
from dotenv import load_dotenv
load_dotenv()

debug = 1
genus = ''
app = sys.argv[1]
tab = app.lower() + "_spcimages"
size = 500, 400
conn = pymysql.connect(host=os.getenv('DBHOST'), user='chariya', port=3306, passwd=os.getenv('MYDBPSSWD'), db=os.getenv('DBNAME'))
cur = conn.cursor()
if app != 'other':
    family = app.title()
    imgdir = "/mnt/static/utils/images/" + family + "/"
    Path(imgdir).mkdir(parents=True, exist_ok=True)

stmthead = "UPDATE " + tab + " set image_file = '%s' where id = %d"
stmt = "SELECT id, image_url, genus, family  FROM " + tab + " where image_url <>'' and image_url is not null and (image_file is null or image_file = '') order by id"
cur.execute(stmt)
i = 0
for row in cur:
    i = i + 1
    if i > 10: exit
    url = row[1]
    if debug:
        print("url = ", row[0], url)

    if row[3]:
        if app in ('other', 'fungi', 'aves', 'animalia'):
            family = row[3].title()
    urlparts = re.search('\/(.*)(\?)?', url)
    a = urlparts.group(1)
    # temp_name, ext = os.path.splitext(url)

    parsed_url = urlparse(url)
    path = parsed_url.path
    ext = os.path.splitext(path)[1]

    if not ext:
        query_params = parse_qs(parsed_url.query)
        ext = f".{query_params['format'][0]}" if 'format' in query_params else ''
    # path = parsed_url.path
    # ext = os.path.splitext(path)[1]

    uid = shortuuid.uuid()
    fname = row[2] + '_' + shortuuid.uuid() + ext
    # fname = "%s_%09d_%09d.jpg" % (type, row[0], row[2])

    if not url or url == '':
        print ("Bad", url)
        cur.nextset()

    try:
        # html = urlopen(url)
        if app in ('other', 'fungi', 'aves', 'animalia'):
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
