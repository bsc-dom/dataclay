""" Class description goes here. """

from dataclay.exceptions.ErrorDefs import ErrorCodes


class DataClayException(Exception):
    """Base class for exceptions in this module."""

    pass


##################
# NEW EXCEPTIONS #
##################


##############
# KV Generic #
##############


class AlreadyExistError(DataClayException):
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return f"{self.id} already exist"


class DoesNotExistError(DataClayException):
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return f"{self.id} does not exist"


###########
# Account #
###########


class AccountError(DataClayException):
    def __init__(self, username):
        self.username = username


class AccountDoesNotExistError(AccountError):
    def __str__(self):
        return f"Account {self.username} does not exist"


class AccountAlreadyExistError(AccountError):
    def __str__(self):
        return f"Account {self.username} already exist"


class AccountInvalidCredentialsError(AccountError):
    def __str__(self):
        return f"Account {self.username} invalid credentials"


###########
# Dataset #
###########


class DatasetError(DataClayException):
    def __init__(self, dataset_name):
        self.dataset_name = dataset_name


class DatasetDoesNotExistError(DatasetError):
    def __str__(self):
        return f"Dataset {self.dataset_name} does not exist"


class DatasetAlreadyExistError(DatasetError):
    def __str__(self):
        return f"Dataset {self.dataset_name} already exist"


class DatasetIsNotAccessibleError(DatasetError):
    def __init__(self, dataset_name, username):
        self.dataset_name = dataset_name
        self.username = username

    def __str__(self):
        return f"Dataset {self.dataset_name} is not accessible by {self.username}"


###########
# Session #
###########


class SessionError(DataClayException):
    def __init__(self, session_id):
        self.session_id = session_id


class SessionDoesNotExistError(SessionError):
    def __str__(self):
        return f"Session {self.session_id} does not exist"


class SessionAlreadyExistError(SessionError):
    def __str__(self):
        return f"Session {self.session_id} already exist"


class SessionIsNotActiveError(SessionError):
    def __str__(self):
        return f"Session {self.session_id} is not active"


###########
# Alias #
###########


class AliasError(DataClayException):
    def __init__(self, alias_name, dataset_name):
        self.alias_name = alias_name
        self.dataset_name = dataset_name


class AliasDoesNotExistError(AliasError):
    def __str__(self):
        return f"Alias {self.dataset_name}/{self.alias_name} does not exist"


class AliasAlreadyExistError(AliasError):
    def __str__(self):
        return f"Alias {self.dataset_name}/{self.alias_name} already exist"


###########
# Object #
###########


class ObjectError(DataClayException):
    def __init__(self, object_id):
        self.object_id = object_id


class ObjectAlreadyRegisteredError(ObjectError):
    def __str__(self):
        return f"Object {self.object_id} is already registered!"


class ObjectNotRegisteredError(ObjectError):
    def __str__(self):
        return f"Object {self.object_id} is not registered!"


class ObjectDoesNotExistError(ObjectError):
    def __str__(self):
        return f"Object {self.object_id} does not exist!"


class ObjectAlreadyExistError(ObjectError):
    def __str__(self):
        return f"Object {self.object_id} already exist!"


class ObjectWithWrongBackendIdError(ObjectError):
    def __init__(self, backend_id, replica_backend_ids):
        self.backend_id = backend_id
        self.replica_backend_ids = replica_backend_ids

    def __str__(self):
        return f"Object {self.object_id} with wrong backend_id!"


class ObjectIsNotVersionError(ObjectError):
    def __str__(self):
        return f"Object {self.object_id} is not a version!"
    
class ObjectIsMasterError(ObjectError):
    def __str__(self):
        return f"Object {self.object_id} is the master!"


###########
# Backend #
###########


class BackendError(DataClayException):
    def __init__(self, ee_id):
        self.ee_id = ee_id


class BackendDoesNotExistError(BackendError):
    def __str__(self):
        return f"Backend {self.ee_id} does not exist!"


class BackendAlreadyExistError(BackendError):
    def __str__(self):
        return f"Backend {self.ee_id} already exist!"


############
# Dataclay #
############


class DataclayError(DataClayException):
    def __init__(self, dataclay_id):
        self.dataclay_id = dataclay_id


class DataclayDoesNotExistError(DataclayError):
    def __str__(self):
        return f"Dataclay {self.dataclay_id} does not exist!"


class DataclayAlreadyExistError(DataclayError):
    def __str__(self):
        return f"Dataclay {self.dataclay_id} already exist!"


###############
# Dataclay ID #
###############


class DataclayIdError(DataClayException):
    pass


class DataclayIdDoesNotExistError(DataclayIdError):
    def __str__(self):
        return f"Dataclay ID does not exist!"


class DataclayIdAlreadyExistError(DataclayIdError):
    def __str__(self):
        return f"Dataclay ID already exist!"


# TODO: Check if old excepions are used
##################
# OLD EXCEPTIONS #
##################


class ImproperlyConfigured(DataClayException):
    """Raised when the settings are not well-formed."""

    # def __init__(self, msg):
    #     self.msg = msg
    pass


class IdentifierNotFound(DataClayException):
    """Raised when a certain identifier (UUID, name...) has not been found."""

    pass


class InvalidPythonSignature(DataClayException):
    """Raised when trying to use a not recognizable Python-signature."""

    pass


class RemoteException(RuntimeError):
    """Exception thrown in client code after a RPC call return with an exception."""

    def __init__(self, error_code, error_string):
        self.error_code = error_code
        self.error_string = error_string
        try:
            self.error_name = ErrorCodes.error_codes[error_code]
        except KeyError:
            self.error_name = "UNDEFINED".format(error_code)
        super(RuntimeError, self).__init__(
            "Error [{}: {}]. Server response: {}".format(
                self.error_code, self.error_name, self.error_string
            )
        )


class NetworkError(RuntimeError):
    """Exception when some socket input/output recv or similar operation
    does not behave as expected."""

    def __init__(self, *args):
        super(RuntimeError, self).__init__(*args)


class ClientError(RuntimeError):
    """Exception when a client has sent some invalid request."""

    def __init__(self, *args):
        super(RuntimeError, self).__init__(*args)
