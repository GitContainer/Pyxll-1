class TFException(Exception):
    """Exception occured during Column Transformation"""
    pass


class ApiError(TFException):
    """Error during API Transformation"""
    pass


class SectionError(TFException):
    """Error during Section Transformation"""
    pass


