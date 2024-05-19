# from __future__ import print_function
import urllib
import pymysql
import os
from dotenv import load_dotenv
load_dotenv()

conn = pymysql.connect(host=os.getenv('DBHOST'), user='chariya', port=3306, passwd=os.getenv('MYDBPSSWD'), db=os.getenv('DBNAME'))
cur = conn.cursor()

cur.execute(f"delete from common_commonname where 1")
if cur.rowcount > 0:
    print(f"{cur.rowcount} rows: deleted")

cur.execute(f"ALTER TABLE common_commonname  AUTO_INCREMENT = 0;")
cur.execute("insert into common_commonname (common_name, common_name_search, application, level, taxon_id) "
            "select common_name, common_name, application,'Family',family from common_family where common_name is not null;")
if cur.rowcount > 0:
    print(f"{cur.rowcount} rows: Families")

for app in ['animalia', 'aves', 'fungi', 'other', 'orchidaceae']:
    cur.execute(f"insert into common_commonname (common_name, common_name_search, application, level, taxon_id) "
                f"select common_name, common_name, '{app}', 'Genus', pid from {app}_genus where common_name is not null;")
    if cur.rowcount > 0:
        print(f"{cur.rowcount} rows: {app} genus")

    cur.execute(f"insert into common_commonname (common_name, common_name_search, application, level, taxon_id) "
                f"select common_name, common_name_search, '{app}', 'Accepted', pid from {app}_accepted where common_name is not null;")
    if cur.rowcount > 0:
        print(f"{cur.rowcount} rows: {app} species")

conn.commit()
cur.close()
conn.close()