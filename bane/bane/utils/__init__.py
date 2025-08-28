# Utils module imports
# Educational/Research purposes only

try:
    from .extrafun import *
except ImportError as e:
    print(f"Warning: Could not import extrafun: {e}")

try:
    from .handle_files import *
except ImportError:
    pass

try:
    from .handle_instances import *
except ImportError:
    pass

try:
    from .js_fuck import *
except ImportError:
    pass

try:
    from .pager import *
except ImportError:
    pass

try:
    from .proxer import *
except ImportError:
    pass

try:
    from .swtch import *
except ImportError:
    pass

try:
    from .updating import *
except ImportError:
    pass

try:
    from .socket_connection import *
except ImportError:
    pass
