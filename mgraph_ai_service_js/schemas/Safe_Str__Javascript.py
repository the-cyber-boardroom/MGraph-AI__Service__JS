import re
from osbot_utils.type_safe.primitives.safe_str.Safe_Str  import Safe_Str

class Safe_Str__Javascript(Safe_Str):   # Safe string type for JavaScript code that preserves syntax while removing dangerous patterns

    max_length        : int                = 1048576  # 1MB max code size
    regex            : re.Pattern          = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')  # Remove control chars only
    replacement_char : str                 = ' '      # Replace control chars with space