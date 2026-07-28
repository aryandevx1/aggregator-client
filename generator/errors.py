class LoaderError(Exception): 
    """Base exception for all schema loader errors."""

class SchemaDirectoryError(LoaderError):
    """Raised when the schema directory is missing or invalid."""


class SchemaFileError(LoaderError):
    """Raised when a schema file cannot be read."""


class SchemaParseError(LoaderError):
    """Raised when YAML syntax is invalid."""


class SchemaStructureError(LoaderError):
    """Raised when the YAML structure is incorrect."""