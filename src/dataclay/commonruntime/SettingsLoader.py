
""" Class description goes here. """

"""Automatic population helpers for the settings.

When certain unknown setting is asked (like account UUID), the classes defined
here help to automatically populate them.
"""
from abc import ABCMeta, abstractmethod

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'
from dataclay.commonruntime.Runtime import getRuntime
import six

@six.add_metaclass(ABCMeta)
class AbstractLoader(object):
    """An abstraction to allow lazy evaluation of settings fields.

    See dataclay.conf._SettingsHub to check the behaviour and purpose of this
    class. The different loaders expose an abstraction to allow lazy and late
    initialization of variable values.
    """

    @abstractmethod
    def __init__(self, settings_object):
        self._settings = settings_object

    @abstractmethod
    def load_value(self):
        """Perform the active load of the requested value.

        This is typically executed only once, as the settings will store the
        real object in its place.

        :return: The expected commonruntime value for the settings field.
        """
        pass


class AccountIdLoader(AbstractLoader):

    def __init__(self, settings_object, field_of_account_name):
        """Load an Account ID for a certain user

        :param field_of_account_name: The name of the field of the settings
        that contain the account name.
        """
        self._field = field_of_account_name
        super(AccountIdLoader, self).__init__(settings_object)

    def load_value(self):
        account_name = getattr(self._settings, self._field)
        return getRuntime().ready_clients["@LM"].get_account_id(account_name)


class AccountCredentialLoader(AbstractLoader):

    def __init__(self, settings_object, field_of_account_id, field_of_account_password):
        """Prepare a credential pair for a certain account.
        :param field_of_account_id: The name of the field of the settings
        that contain the account id.
        :param field_of_account_password: Same but for the password.
        that contain the account name.
        """
        self._field_id = field_of_account_id
        self._field_password = field_of_account_password
        super(AccountCredentialLoader, self).__init__(settings_object)

    def load_value(self):
        return (getattr(self._settings, self._field_id),
                getattr(self._settings, self._field_password))
