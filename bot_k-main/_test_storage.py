import os
os.environ['BOT_DATA_DIR'] = '/opt/klasykbot/data'
from database import get_storage_stats, get_top_users_by_storage, get_users_over_threshold

s = get_storage_stats()
for k, v in s.items():
    print(f"{k}: {v}")
print("---TOP---")
for u in get_top_users_by_storage(5):
    print(u)
print("---ALERTS---")
print(get_users_over_threshold())
