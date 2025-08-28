# Bruteforce module imports
# Educational/Research purposes only

try:
    from .bruteforcer import *
except ImportError as e:
    print(f"Warning: Could not import bruteforcer: {e}")

try:
    from .admin_panel_finder import *
except ImportError:
    pass

try:
    from .decrypt import *
except ImportError:
    pass

try:
    from .web_login import *
except ImportError:
    pass

try:
    from .services_login import *
except ImportError:
    pass

try:
    from .hydra import *
except ImportError:
    pass

try:
    from .jwter import *
except ImportError:
    pass