""" Class description goes here. """


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
        return f"{self.id} already exists"


class DoesNotExistError(DataClayException):
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return f"{self.id} does not exists"


###########
# Account #
###########


class AccountError(DataClayException):
    def __init__(self, username):
        self.username = username


class AccountInvalidCredentialsError(AccountError):  # TODO: testing
    def __str__(self):
        return f"Account {self.username} invalid credentials"


###########
# Dataset #
###########


class DatasetError(DataClayException):
    def __init__(self, dataset_name):
        self.dataset_name = dataset_name


class DatasetIsNotAccessibleError(DatasetError):
    def __init__(self, dataset_name, username):
        self.dataset_name = dataset_name
        self.username = username

    def __str__(self):
        return f"Dataset {self.dataset_name} is not accessible by {self.username}"


#########
# Alias #
#########


class AliasError(DataClayException):
    def __init__(self, alias_name, dataset_name):
        self.alias_name = alias_name
        self.dataset_name = dataset_name


class AliasDoesNotExistError(AliasError):
    def __str__(self):
        return f"Alias {self.dataset_name}/{self.alias_name} does not exists"


class AliasAlreadyExistError(AliasError):
    def __str__(self):
        return f"Alias {self.dataset_name}/{self.alias_name} already exists"


##########
# Object #
##########


class ObjectError(DataClayException):
    def __init__(self, object_id):
        self.object_id = object_id


class ObjectNotRegisteredError(ObjectError):
    def __str__(self):
        return f"Object {self.object_id} is not registered!"


class ObjectWithWrongBackendIdError(ObjectError):  # TODO: testing
    def __init__(self, backend_id, replica_backend_ids):
        self.backend_id = backend_id
        self.replica_backend_ids = replica_backend_ids

    def __str__(self):
        return f"Object {self.object_id} with wrong backend_id!"


class ObjectIsNotVersionError(ObjectError):
    def __str__(self):
        return f"Object {self.object_id} is not a version!"


class ObjectIsMasterError(ObjectError):  # TODO: testing
    def __str__(self):
        return f"Object {self.object_id} is the master!"


###########
# Backend #
###########


class BackendError(DataClayException):
    def __init__(self, ee_id):
        self.ee_id = ee_id


############
# Dataclay #
############


class DataclayError(DataClayException):
    def __init__(self, dataclay_id):
        self.dataclay_id = dataclay_id


###############
# Dataclay ID #
###############


class DataclayIdError(DataClayException):
    pass
