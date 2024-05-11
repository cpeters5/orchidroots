# from __future__ import print_function
import urllib
import pymysql
import os
from dotenv import load_dotenv
load_dotenv()

conn = pymysql.connect(host=os.getenv('DBHOST'), user='chariya', port=3306, passwd=os.getenv('MYDBPSSWD'), db=os.getenv('DBNAME'))
cur = conn.cursor()

cur.execute(f"delete from common_commonname where application = 'common' and level = 'Family';")
cur.execute("insert into common_commonname (common_name, application, level, taxon_id) select common_name, application,'Family',family from common_family where common_name is not null;")

for app in ['animalia', 'aves', 'fungi', 'other', 'orchidaceae']:
    cur.execute(f"delete from common_commonname where application = '{app}'")
    cur.execute(f"insert into common_commonname (common_name, application, level, taxon_id) select common_name, '{app}', 'Genus', pid from {app}_genus where common_name is not null;")
    cur.execute(f"insert into common_commonname (common_name, application, level, taxon_id) select common_name, '{app}', 'Accepted', pid from {app}_accepted where common_name is not null;")


