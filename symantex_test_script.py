import os
from symantex.core import Symantex

KEY = os.getenv('SYMANTEX_DEV_KEY')

sx4 = Symantex()

sx4.register_key(KEY)
