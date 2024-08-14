import urllib
import pymysql
import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(filename='/var/log/bluenanta/hybrid_processing.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def reset_processed_hybrids_if_empty(conn):
    cursor = conn.cursor()
    # Check if AncDesc is empty
    cursor.execute('SELECT COUNT(*) FROM orchidaceae_ancestordescendant')
    ancdesc_count = cursor.fetchone()[0]
    if ancdesc_count == 0:
        # If AncDesc is empty, delete all entries from ProcessedHybrids
        cursor.execute('DELETE FROM orchid_processed_hybrids')
        conn.commit()
        logging.info("AncDesc table is empty. Reset ProcessedHybrids table.")
    else:
        logging.info(f"AncDesc table contains {ancdesc_count} records. Resuming from last processed hybrid.")

def get_ancestors(conn, pid, level=0, visited=None):
    if visited is None:
        visited = set()

    if pid in visited:
        logging.warning(f"Circular reference detected for pid {pid}")
        return []

    visited.add(pid)

    cursor = conn.cursor()
    cursor.execute('SELECT seed_id, pollen_id FROM orchidaceae_hybrid WHERE pid = %s', (pid,))
    result = cursor.fetchone()

    if result is None:
        return []

    seed_id, pollen_id = result

    # Cinvert synonym id to accepted
    # Commented the following two lines if retain synonym aids
    seed_id = get_accepted_id(conn, seed_id)
    pollen_id = get_accepted_id(conn, pollen_id)

    current_level = [(seed_id, 50, level + 1), (pollen_id, 50, level + 1)]

    next_level = (get_ancestors(conn, seed_id, level + 1, visited.copy()) +
                  get_ancestors(conn, pollen_id, level + 1, visited.copy()))

    return current_level + next_level


def calculate_percentage(ancestors):
    result = {}
    for aid, pct, level in ancestors:
        contribution = pct / (2 ** (level - 1))
        if aid in result:
            result[aid] += contribution
        else:
            result[aid] = contribution
    return result


def get_species_info(conn, pid):
    cursor = conn.cursor()
    cursor.execute('SELECT type FROM orchidaceae_species WHERE pid = %s', (pid,))
    result = cursor.fetchone()
    return result[0] if result else None


def get_accepted_id(conn, pid):
    cursor = conn.cursor()
    cursor.execute('SELECT acc_id FROM orchidaceae_synonym WHERE spid = %s', (pid,))
    result = cursor.fetchone()
    return result[0] if result else pid


def process_hybrid(conn, pid):
    try:
        ancestors = get_ancestors(conn, pid)
        percentages = calculate_percentage(ancestors)

        cursor = conn.cursor()
        for aid, pct in percentages.items():
            species_type = get_species_info(conn, aid)
            acc_id = get_accepted_id(conn, aid)

            cursor.execute('''
            INSERT INTO orchidaceae_ancestordescendant (did, aid, pct, anctype)
            VALUES (%s, %s, %s, %s)
            ''', (pid, acc_id, pct, species_type))
        # Mark hybrid as processed
        cursor.execute('''
        INSERT INTO orchid_processed_hybrids (pid, processed_at)
        VALUES (%s, %s)
        ''', (pid, datetime.now()))

        conn.commit()
        # print("processed ", pid, datetime.now())
        # exit()
        return True
    except Exception as e:
        conn.rollback()
        logging.error(f"Error processing hybrid {pid}: {str(e)}")
        return False


def get_unprocessed_hybrids(conn, batch_size):
    cursor = conn.cursor()
    cursor.execute('''
    SELECT h.pid FROM orchidaceae_hybrid h
    LEFT JOIN orchid_processed_hybrids p ON h.pid = p.pid
    WHERE p.pid IS NULL
    LIMIT %s
    ''', (batch_size,))
    return [row[0] for row in cursor.fetchall()]


def process_hybrid_batch(conn, batch_size=1000):
    time_limit = 1000  # Set time limit in seconds (e.g., 1 hour)
    start_time = time.time()
    total_processed = 0
    while True:
        hybrids = get_unprocessed_hybrids(conn, batch_size)
        if not hybrids:
            # done
            break

        for pid in hybrids:
            if process_hybrid(conn, pid):
                total_processed += 1
            if total_processed % 1000 == 0:
                elapsed_time = time.time() - start_time
                print(total_processed, elapsed_time)
                logging.info(f"Processed {total_processed} hybrids. Elapsed time: {elapsed_time:.2f} seconds")

        conn.commit()

        elapsed_time = time.time() - start_time
        logging.info(f"Batch completed. Total processed: {total_processed}. Elapsed time: {elapsed_time:.2f} seconds")
        # exit()
    total_time = time.time() - start_time
    logging.info(f"All hybrids processed. Total: {total_processed}. Total time: {total_time:.2f} seconds")


def main():
    start_time = time.time()
    conn = pymysql.connect(
        host=os.getenv('DBHOST'),
        user='chariya',
        port=3306,
        passwd=os.getenv('MYDBPSSWD'),
        database=os.getenv('DBNAME'),
        autocommit = False
    )
    print(os.getenv('DBNAME'))
    try:
        print("reset_processed_hybrids_if_empty")
        reset_processed_hybrids_if_empty(conn)
        print("process_hybrid_batch")
        process_hybrid_batch(conn)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    finally:
        conn.close()

    total_time = time.time() - start_time
    logging.info(f"Total script execution time: {total_time:.2f} seconds")


if __name__ == "__main__":
    main()