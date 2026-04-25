#!/usr/bin/env python3
"""One-shot deep DB audit script — run on the server."""
import sqlite3, os

DATA = '/opt/klasykbot/data'
GDB = os.path.join(DATA, 'global.db')
UDIR = os.path.join(DATA, 'users')

c = sqlite3.connect(GDB)
c.row_factory = sqlite3.Row

print('=== GLOBAL.DB PRAGMAS ===')
for p in ['journal_mode','page_size','auto_vacuum','freelist_count','page_count','cache_size']:
    print(f'  {p}: {c.execute(f"PRAGMA {p}").fetchone()[0]}')

print()
print('=== TABLE ROW COUNTS ===')
for t in ['schedule_events','knowledge_items','user_index','submission_index','signups']:
    cnt = c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
    print(f'  {t}: {cnt} rows')

print()
print('=== INDEXES ===')
for row in c.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'").fetchall():
    print(f'  {row[0]} on {row[1]}')

print()
print('=== USER DB DETAILS ===')
total_user_db = 0
for uid in sorted(os.listdir(UDIR)):
    p = os.path.join(UDIR, uid, 'data.db')
    if not os.path.exists(p):
        continue
    sz = os.path.getsize(p)
    total_user_db += sz
    uc = sqlite3.connect(p)
    uc.row_factory = sqlite3.Row
    prof_cnt = uc.execute('SELECT COUNT(*) FROM profile').fetchone()[0]
    sub_cnt = uc.execute('SELECT COUNT(*) FROM submissions').fetchone()[0]
    set_cnt = uc.execute('SELECT COUNT(*) FROM settings').fetchone()[0]
    jm = uc.execute('PRAGMA journal_mode').fetchone()[0]
    
    # Show submission details
    subs = uc.execute('SELECT id, content_type, file_type, file_id, file_size, text_content FROM submissions').fetchall()
    sub_detail = ''
    for s in subs:
        fid = str(s['file_id'])[:40] + '...' if s['file_id'] else 'NULL'
        sub_detail += f'\n      sub#{s["id"]}: type={s["content_type"]}, file_type={s["file_type"]}, file_id={fid}, size={s["file_size"]}'
        if s['text_content']:
            sub_detail += f', text_len={len(s["text_content"])}'
    
    uc.close()
    print(f'  {uid}: {sz}B, profile={prof_cnt}, submissions={sub_cnt}, settings={set_cnt}, journal={jm}{sub_detail}')

print(f'  TOTAL user DBs: {total_user_db} bytes ({total_user_db/1024:.1f} KB)')
print(f'  global.db: {os.path.getsize(GDB)} bytes ({os.path.getsize(GDB)/1024:.1f} KB)')

c.close()
