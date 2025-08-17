import os
import tempfile
import sys

paths = []
# 1. Ścieżka podana przez DATABASE_URL
db_env = os.environ.get('DATABASE_URL')
if db_env and db_env.startswith('sqlite:///'):
    paths.append(db_env.replace('sqlite:///', ''))

# 2. backend/test.db (relatywnie)
paths.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'test.db')))
# 3. projektowy root/test.db
paths.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test.db')))
# 4. tmp
paths.append(os.path.join(tempfile.gettempdir(), 'kocikocidrapki_test.db'))

print('cwd:', os.path.abspath(os.getcwd()))
print('Checking candidate paths:')
for p in paths:
    try:
        print('\nPath:', p)
        d = os.path.dirname(p) or '.'
        print(' dir exists:', os.path.isdir(d))
        try:
            os.makedirs(d, exist_ok=True)
            print(' ensured dir')
        except Exception as e:
            print(' ensure dir error:', e)
        exists = os.path.exists(p)
        print(' exists:', exists)
        try:
            f = open(p, 'a')
            f.close()
            print(' open_append: OK')
            print(' writable:', os.access(p, os.W_OK))
        except Exception as e:
            print(' open_append: ERROR:', e)
            print(' writable:', os.access(p, os.W_OK))
    except Exception as e:
        print('Unexpected error for path:', p, e)

# Print temp dir
print('\nTemp dir:', tempfile.gettempdir())
print('User:', os.getlogin() if hasattr(os, "getlogin") else 'unknown')

# Exit code 0
sys.exit(0)
