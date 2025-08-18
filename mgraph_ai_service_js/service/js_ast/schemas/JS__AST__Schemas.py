import re
from typing                                                             import Optional, Dict, Any, List
from osbot_utils.type_safe.Type_Safe                                    import Type_Safe
from osbot_utils.type_safe.primitives.safe_str.Enum__Safe_Str__Regex_Mode import Enum__Safe_Str__Regex_Mode
from osbot_utils.type_safe.primitives.safe_str.Safe_Str                 import Safe_Str
from osbot_utils.type_safe.primitives.safe_int.Safe_Int                 import Safe_Int
from osbot_utils.type_safe.primitives.safe_uint.Safe_UInt import Safe_UInt

from mgraph_ai_service_js.schemas.Safe_Str__Javascript                  import Safe_Str__Javascript


class Safe_Str__ECMAVersion(Safe_Str):
    max_length        = 10
    regex             = re.compile(r'^(latest|es\d{4}|\d{4})$')                 # "latest", "es2023", "2023"
    regex_mode        = Enum__Safe_Str__Regex_Mode.MATCH                        # Use MATCH mode for validation
    strict_validation = True                                                    # Raise error on invalid input

class Safe_Str__SourceType(Safe_Str):
    max_length        = 20
    regex             = re.compile(r'^(module|script|unambiguous)$')
    regex_mode        = Enum__Safe_Str__Regex_Mode.MATCH                        # Use MATCH mode for validation
    strict_validation = True                                                    # Raise error on invalid input


class Safe_Str__NodeType(Safe_Str):                                                  # ESTree node type identifier
    max_length = 50
    regex      = re.compile(r'^[A-Z][a-zA-Z]+$')                                                # PascalCase node types


class Safe_Str__Code__Formatting(Safe_Str):                                         # Code formatting strings (indent/line endings)
    max_length       = 100
    regex            = re.compile(r'[^ \t\r\n]')                                    # Remove anything that's NOT space, tab, CR, LF
    replacement_char = ''                                                           # Remove instead of replacing with _
    allow_empty      = True
    trim_whitespace  = False

class JS__AST__Parser__Options(Type_Safe):                                           # Parser configuration options
    ecma_version : Safe_Str__ECMAVersion = Safe_Str__ECMAVersion("latest")
    source_type  : Safe_Str__SourceType  = Safe_Str__SourceType ("module")
    jsx          : bool                  = False
    typescript   : bool                  = False
    next         : bool                  = True
    locations    : bool                  = True
    ranges       : bool                  = True
    raw          : bool                  = True
    tokens       : bool                  = False
    comments     : bool                  = True
    tolerant     : bool                  = False


class JS__AST__Generator__Options(Type_Safe):                                        # Generator configuration options
    indent       : Safe_Str__Code__Formatting  = Safe_Str__Code__Formatting("  ")
    line_end     : Safe_Str__Code__Formatting  = Safe_Str__Code__Formatting("\n")
    start_indent : Safe_Str__Code__Formatting  = Safe_Str__Code__Formatting("")
    comments     : bool                        = True
    source_map   : bool                        = False


class JS__AST__Location(Type_Safe):                                                  # Source location information
    start_line   : Safe_UInt
    start_column : Safe_UInt
    end_line     : Safe_UInt
    end_column   : Safe_UInt


class JS__AST__Node(Type_Safe):                                                      # Base ESTree node structure
    type  : Safe_Str__NodeType
    loc   : Optional[JS__AST__Location]
    range : Optional[List[Safe_Int]]


class JS__AST__Parse__Request(Type_Safe):                                            # Parse request schema
    code    : Safe_Str__Javascript
    options : Optional[JS__AST__Parser__Options]


class JS__AST__Parse__Response(Type_Safe):                                           # Parse response schema
    success         : bool
    ast             : Optional[Dict[str, Any]]
    error           : Optional[Safe_Str]
    error_location  : Optional[JS__AST__Location]
    parse_time_ms   : Safe_Int = Safe_Int(0)


class JS__AST__Generate__Request(Type_Safe):                                         # Generate request schema
    ast     : Dict[str, Any]
    options : Optional[JS__AST__Generator__Options]


class JS__AST__Generate__Response(Type_Safe):                                        # Generate response schema
    success           : bool
    code              : Optional[Safe_Str__Javascript]
    error             : Optional[Safe_Str]
    generation_time_ms: Safe_Int = Safe_Int(0)


class JS__AST__Roundtrip__Request(Type_Safe):                                        # Roundtrip validation request
    code              : Safe_Str__Javascript
    parser_options    : Optional[JS__AST__Parser__Options]
    generator_options : Optional[JS__AST__Generator__Options]


class JS__AST__Roundtrip__Response(Type_Safe):                                       # Roundtrip validation response
    success          : bool
    is_valid         : bool                       = False
    original_ast     : Optional[Dict[str, Any]]
    generated_code   : Optional[Safe_Str__Javascript]
    regenerated_ast  : Optional[Dict[str, Any]]
    error            : Optional[Safe_Str]
    parse_time_ms    : Safe_Int                   = Safe_Int(0)
    generate_time_ms : Safe_Int                   = Safe_Int(0)
    total_time_ms    : Safe_Int                   = Safe_Int(0)