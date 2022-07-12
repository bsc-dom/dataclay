from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch
from test_dataclay.test_utils import import_mock

""" Mock all imports done by the tested module """
with patch("builtins.__import__", side_effect=import_mock):
    import dataclay.api as api


class Test(TestCase):
    def setUp(self):
        # Mock logger #
        api.logger.debug = print
        api.logger.verbose = print

    def tearDown(self):
        pass

    def test_is_initialized(self):
        api._initialized = False
        self.assertFalse(api.is_initialized())

    def test_reinitialize_logging(self):
        fake_return_value = dict()
        api._get_logging_dict_config.return_value = fake_return_value
        api.reinitialize_logging()
        self.assertFalse(api._get_logging_dict_config()["disable_existing_loggers"])

    def test_reinitialize_clients(self):
        api.settings.logicmodule_host = "logicmodule"
        api.settings.logicmodule_port = "1024"
        result_ready_clients = {
            "@LM": api.LMClient(api.settings.logicmodule_host, api.settings.logicmodule_port),
        }
        api.reinitialize_clients()
        self.assertEqual(result_ready_clients, api.getRuntime().ready_clients)

    def test_init_connection(self):
        pass
        # api.init_connection(client_file)

    def test_get_backends(self):
        pass

    def test_get_backends_info(self):
        pass

    def test_get_backend_id_by_name(self):
        pass

    def test_register_dataclay(self):
        pass

    def test_get_dataclay_id(self):
        pass

    def test_unfederate(self):
        pass

    def test_migrate_federated_objects(self):
        pass

    def test_federate_all_objects(self):
        pass

    def test_pre_network_init(self):
        pass

    def test_init(self):
        pass

    def test_post_network_init(self):
        pass

    def test_finish_tracing(self):
        pass

    def test_finish(self):
        pass
