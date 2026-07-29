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


class ValidatorError(Exception): 
    """Base exception for all the validator errors"""


class DuplicateObjectError(ValidatorError): 
    """Raised when a duplicate object is encountered"""


class DuplicateFieldError(ValidatorError): 
    """Raised when a duplicate field is encountered"""


class KindValidationError(ValidatorError): 
    """Raised when an invalid kind is encountered"""


class TypeValidationError(ValidatorError): 
    """Raised when an invalid type is encountered"""


class RefValidationError(ValidatorError): 
    """Raised when an invalid ref is encountered"""


class EnumValidationError(ValidatorError): 
    """Raised when an invalid enum is encountered"""


class TagLockerError(Exception):
    """Base exception for tag-locking failures."""


class TagLockFileNotFoundError(TagLockerError):
    """Raised when the tag lock file does not exist."""


class TagLockFileReadError(TagLockerError):
    """Raised when the tag lock file cannot be read."""


class TagLockFileWriteError(TagLockerError):
    """Raised when the tag lock file cannot be written."""


class TagLockFileParseError(TagLockerError):
    """Raised when the tag lock file contains invalid JSON."""