"""In general, dataClay will prefer to raise the exceptions defined below."""


class DataClayException(Exception):
    """Base class for exceptions in this module."""
    pass


##############
# KV Generic #
##############


class AlreadyExistError(DataClayException):
    """<id> already exists."""

    def __init__(self, id):
        self.id = id

    def __str__(self):
        return f"{self.id} already exists"


class DoesNotExistError(DataClayException):
    """<id> does not exist."""

    def __init__(self, id):
        self.id = id

    def __str__(self):
        return f"{self.id} does not exist"


###########
# Account #
###########


class AccountError(DataClayException):
    """Base exception for account errors."""

    def __init__(self, username):
        self.username = username


class AccountInvalidCredentialsError(AccountError):  # TODO: testing
    """A credentials verification returned False. The credentials were invalid"""

    def __str__(self):
        return f"Account {self.username} invalid credentials"


###########
# Dataset #
###########


class DatasetError(DataClayException):
    """Base exception for dataset errors."""

    def __init__(self, dataset_name):
        self.dataset_name = dataset_name


class DatasetIsNotAccessibleError(DatasetError):
    """The dataset is not accessible."""

    def __init__(self, dataset_name, username):
        self.dataset_name = dataset_name
        self.username = username

    def __str__(self):
        return f"Dataset {self.dataset_name} is not accessible by {self.username}"


#########
# Alias #
#########


class AliasError(DataClayException):
    """Base exception for alias errors."""

    def __init__(self, alias_name, dataset_name):
        self.alias_name = alias_name
        self.dataset_name = dataset_name


class AliasDoesNotExistError(AliasError):
    """The alias <alias_name> does not exist in the dataset <dataset_name>"""

    def __str__(self):
        return f"Alias {self.dataset_name}/{self.alias_name} does not exist"


class AliasAlreadyExistError(AliasError):
    """The alias <alias_name> already exists in the dataset <dataset_name>, so you can not define
    it again"""

    def __str__(self):
        return f"Alias {self.dataset_name}/{self.alias_name} already exists"


##########
# Object #
##########


class ObjectError(DataClayException):
    """Base exception for object errors."""

    def __init__(self, object_id):
        self.object_id = object_id


class ObjectNotRegisteredError(ObjectError):
    """The object is not registered in dataClay (one of the ways to register
    an object is by using the function {make_persistent})"""

    def __str__(self):
        return f"Object {self.object_id} is not registered!"


class ObjectWithWrongBackendIdError(ObjectError):  # TODO: testing
    """DataClay had the wrong backend ID stored for the object <object_id>. DataClay will
    automaticaly search for the correct backend."""

    def __init__(self, backend_id, replica_backend_ids):
        self.backend_id = backend_id
        self.replica_backend_ids = replica_backend_ids

    def __str__(self):
        return f"Object {self.object_id} with wrong backend_id!"


class ObjectIsNotVersionError(ObjectError):
    """The object doesn't have an <_dc_meta.original_object_id>, which means that it is
    not a version"""

    def __str__(self):
        return f"Object {self.object_id} is not a version!"


class ObjectIsMasterError(ObjectError):  # TODO: testing
    """The object <object_id> is the master. This means it is registred, it is local and it is not a replica"""

    def __str__(self):
        return f"Object {self.object_id} is the master!"


class ObjectNotFound(ObjectError):
    """The object <object_id> could not be found"""

    def __str__(self):
        return f"Object {self.object_id} not found."


class ObjectStorageError(ObjectError):
    """The object could not be stored"""

    def __str__(self):
        return f"Could not store object {self.object_id}."


###########
# Backend #
###########


class BackendError(DataClayException):
    """Base exception for backend errors."""

    def __init__(self, ee_id):
        self.ee_id = ee_id


class NoOtherBackendsAvailable(BackendError):
    """There are no other backends. This means that there is only one backend running
    or even there are no backend running at all"""

    def __str__(self):
        return f"There are no other backends available"


############
# Dataclay #
############


class DataclayError(DataClayException):
    """Base exception for dataclay errors."""

    def __init__(self, dataclay_id):
        self.dataclay_id = dataclay_id


###############
# Dataclay ID #
###############


class DataclayIdError(DataClayException):
    """Base exception for dataclayId errors."""

    pass

