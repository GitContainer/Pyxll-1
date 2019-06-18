class NamespaceMismatch(Exception):
    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        return f"Namespace Mismatch between {self.args[0]} and {self.args[1]}"


class ColumnMismatch(Exception):
    def __init__(self, expected_columns, received_columns):
        self.expected_columns = expected_columns
        self.received_columns = received_columns
        self.missing_columns = [
            col for col in self.expected_columns if col not in self.received_columns
        ]

    def __str__(self):

        return f"Missing {self.missing_columns}"


class PyxllModeLoadError(Exception):
    def __str__(self):
        return "Could not load xl_app"


class ApiError:
    pass


class NameMissingInExcel(Exception):
    def __init__(self, *args):
        self.args = args

    def __str__(self):
        return f"{self.args} not found in the excel workbook"


class NullAttributeValue(Exception):
    def __init__(self, *args):
        self.args = args

    def __str__(self,):
        return f"{self.args} value is null"


class TransformationTypeError(Exception):
    def __init__(self, expected_type, received_type):
        self.expected_type = expected_type
        self.received_type = received_type

    def __str__(self,):
        return f"Expected {self.expected_type} but got {self.received_type}"


class IncompatibleDataModelException(Exception):
    def __init__(self, expected_model, received_model):
        self.expected_model = expected_model
        self.received_model = received_model

    def __str__(self,):
        return f"Expected {self.expected_model} but got {self.received_model}"


class IncompatibleDataModelVersionException(Exception):
    def __init__(self, expected_model_version, received_model_version):
        self.expected_model_version = expected_model_version
        self.received_model_version = received_model_version

    def __str__(self,):
        return f"Expected {self.expected_model_version} but got {self.received_model_version}"


class InvalidExcelAddressException(Exception):
    def __init__(self, address):
        self.address = address

    def __str__(self):
        return f"Invalid excel address {self.address}"


class MismatchingColumnCountException(Exception):
    def __init__(self, expected_count, recieved_count):
        self.expected_count = expected_count
        self.recieved_count = recieved_count

    def __str__(self,):
        return f"Expected {self.expected_count} but got {self.recieved_count}"


class Win32COMCacheException(Exception):
    """
    TODO: Are there any other exceptions getting caught in this catch?
    """

    def __str__(self):
        return (
            f"Win32COMCacheException. Verify that it's not because of any other errors."
        )


class SheetNameNotFoundException(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Sheet name for excel name {self.name} not found"


class AssignmentErrorException(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Assignment not know for {self.name}"


class ErrorFindingProjectParameter(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Error finding parameter {self.name}"


class MissingDataLoaderFunction(Exception):
    def __init__(self, table_name):
        self.table_name = table_name

    def __str__(self):
        return f"{self.table_name} missing in DataLoader"


class MissingDataFormatterFunction(Exception):
    def __init__(self, table_name):
        self.table_name = table_name

    def __str__(self):
        return f"{self.table_name} missing in DataFormatter"
