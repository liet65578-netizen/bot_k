import py_compile
import sys
files = ['bot.py','config.py','database.py','i18n.py','logging_config.py','handlers/__init__.py','handlers/admin.py','handlers/content.py','handlers/knowledge.py','handlers/main_menu.py','handlers/profile.py','handlers/registration.py','handlers/schedule.py']
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f'{f}: OK')
    except py_compile.PyCompileError as e:
        print(f'{f}: ERROR - {e}')
        sys.exit(1)
print('All files compile OK')
