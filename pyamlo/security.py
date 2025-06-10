"""
Default security policy for pyamlo: configurable restrictions.
"""

import fnmatch


class SecurityPolicy:
    """
    Defines restrictions for environment variables, imports, includes, and expressions.
    Can be configured to be restrictive or permissive based on use case.
    """

    def __init__(self, 
                 allowed_env_vars=None, 
                 allowed_imports=None, 
                 allowed_include_paths=None, 
                 allow_expressions=None,
                 restrictive=True):
        """
        Initialize security policy.
        
        Args:
            allowed_env_vars: Set of allowed environment variable names
            allowed_imports: Set of allowed import module names
            allowed_include_paths: Set of allowed file/folder paths for includes
            allow_expressions: Whether to allow general expressions (default: False in restrictive mode)
            restrictive: If True, only the allowed items are permitted; if False, all except the allowed items are restricted.
        """            

        #check if lists or bools
        if not isinstance(restrictive, bool):
            raise TypeError("restrictive must be a boolean value")
        if not isinstance(allowed_env_vars, (set, list, tuple,  type(None))):
            raise TypeError("allowed_env_vars must be a set, list, tuple, or None")
        if not isinstance(allowed_imports, (set, list, tuple, type(None))):
            raise TypeError("allowed_imports must be a set, list, tuple, or None")
        if not isinstance(allowed_include_paths, (set, list, tuple, type(None))):
            raise TypeError("allowed_include_paths must be a set, list, tuple, or None")
        if not isinstance(allow_expressions, (bool, type(None))):
            raise TypeError("allow_expressions must be a boolean value or None")

        self.restrictive = restrictive
        self.allowed_env_vars = set() if allowed_env_vars is None else set(allowed_env_vars)
        self.allowed_imports = set() if allowed_imports is None else set(allowed_imports)
        self.allowed_include_paths = set() if allowed_include_paths is None else set(allowed_include_paths)
        
        if restrictive:
            self.allow_expressions = False if allow_expressions is None else allow_expressions
        else:
            self.allow_expressions = True if allow_expressions is None else allow_expressions
 
    def check_env_var(self, name):
        if self.restrictive:
            if name not in self.allowed_env_vars:
                raise PermissionError(
                    f"Access to environment variable '{name}' is not allowed by security policy."
                )
        else:
            # In permissive mode, allow all unless restricted
            if self.allowed_env_vars and name not in self.allowed_env_vars:
                raise PermissionError(
                    f"Access to environment variable '{name}' is not allowed by security policy."
                )
            
    def check_import(self, module):
        if self.restrictive:
            # In restrictive mode, only allow explicitly allowed imports
            if not self._matches_patterns(module, self.allowed_imports):
                raise PermissionError(
                    f"Import of module '{module}' is not allowed by security policy."
                )
        else:
            # In permissive mode, block explicitly blocked imports
            if self.allowed_imports and self._matches_patterns(module, self.allowed_imports):
                raise PermissionError(
                    f"Import of module '{module}' is not allowed by security policy."
                )

    def check_include(self, path):
        if self.restrictive:
            if not self._matches_patterns(path, self.allowed_include_paths):
                raise PermissionError(
                    f"Include of file or folder '{path}' is not allowed by security policy."
                )
        else:
            # In permissive mode, allow all unless restricted
            if self.allowed_include_paths and not self._matches_patterns(path, self.allowed_include_paths):
                raise PermissionError(
                    f"Include of file or folder '{path}' is not allowed by security policy."
                )

    def _matches_patterns(self, check, patterns):
        """Check if path matches any of the allowed patterns (supports wildcards)."""
        for pattern in patterns:
            if fnmatch.fnmatch(check, pattern):
                return True
        return False


    def check_expression(self, expr):
        if not self.allow_expressions:
            raise PermissionError(
                "Expression evaluation is not allowed by security policy."
            )
