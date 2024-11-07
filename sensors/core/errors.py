class BaseError(Exception):
    pass


class ConfigParseError(BaseError, ValueError):
    pass


class ArgumentError(BaseError, ValueError):
    pass


class ResponseParseError(BaseError, ValueError):
    pass
