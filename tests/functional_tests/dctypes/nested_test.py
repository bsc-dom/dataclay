from __future__ import absolute_import
""" Class description goes here. """

""" 
Use absolute imports. By default, when you import a package in Python 2, it adds '.' in the beggining, it means all 
imports are relative. It's a problem for our testing since our test can be in a package but our stubs are not including 
the package of the test (and shouldn't!). With __future__ we add Python 3 functionality for all imports to be absolute. 
"""
# Initialize dataClay
from mock.simplemock import SimpleMock
import unittest 
import os
import logging
import pytest
"""
Types testing. 
"""
logger = logging.getLogger(__name__)


class TypesTest(unittest.TestCase):

    """
    DataClayMock object for simulation. 
    """
    
    mock = SimpleMock() 
    
    def setUp(self):
        """
        PyUnit function called before every test case.
        Starts DataClay simulation in one Python interpreter and one Java VM. This allows us to Debug in a local machine without 
        dockers and without a full start of DataClay (jars, configurations, ...) 
        """ 
        self.mock.setUp(__file__, nodes=2)

    def tearDown(self):
        """ 
        Finish all services started for simulation. 
        """ 
        self.mock.tearDown()

    @unittest.skip("skipping nested type test")
    @pytest.mark.timeout(300, method='thread')
    def test(self):
        """Test. note that all test method names must begin with 'test.'"""
        """WARNING: IT IS HIGHLY RECOMMENDED TO HAVE ONE TEST ONLY TO ISOLATE FUNCTIONAL TESTS FROM EACH OTHER. i.e. 
        Start a new Python Interpreter and JVM for each test. In the end, it means only one test in this class. """
        from dataclay.api import init

        logger.debug('**Starting init**')
        init()
        
        """ 
        Imports. Imports must be located here in order to simulate "import" order in a real scenario. 
        VERY IMPORTANT: Imports must be located AFTER init
        """
        from model.nested_classes import NestedColl
        from dataclay import getRuntime
        from dataclay.DataClayObjProperties import DCLAY_GETTER_PREFIX

        self.session_initialized = True
    
        """
        Test. From now on, the Functional Test itself. 
        """
        environments_ids = list(getRuntime().get_execution_environments_info().keys())
        environment1_id = environments_ids[0]
        environment2_id = environments_ids[1]
        dict_a = dict()
        dict_a["test"] = 1
        set_a = set()
        set_a.add(1)

        main_list = [dict_a, [1, 2, 3, 4, 5], (1, 2, 3, 4, 5), set_a]
        self.assertEqual(type(main_list[0]), dict)
        self.assertEqual(type(main_list[1]), list)
        self.assertEqual(type(main_list[2]), tuple)
        self.assertEqual(type(main_list[3]), set)

        main_dict = dict()
        main_dict["dict"] = dict_a
        main_dict["list"] = [1, 2, 3, 4]
        main_dict["tuple"] = (1, 2, 3, 4)
        main_dict["set"] = set_a
        self.assertEqual(type(main_dict["dict"]), dict)
        self.assertEqual(type(main_dict["list"]), list)
        self.assertEqual(type(main_dict["tuple"]), tuple)
        self.assertEqual(type(main_dict["set"]), set)

        main_tuple = (dict_a, [1, 2, 3, 4, 5], (1, 2, 3, 4, 5), set_a)
        self.assertEqual(type(main_tuple[0]), dict)
        self.assertEqual(type(main_tuple[1]), list)
        self.assertEqual(type(main_tuple[2]), tuple)
        self.assertEqual(type(main_tuple[3]), set)

        main_set = set()
        main_set.add((1, 2, 3, 4))
        main_set.add(1)
        main_set.add("a")
        self.assertIn(1, main_set)
        self.assertIn("a", main_set)
        self.assertIn((1, 2, 3, 4), main_set)
        
        nested_coll = NestedColl(main_list, main_dict, main_tuple, main_set)
        
        # Test Persistence
        nested_coll.make_persistent(backend_id=environment1_id)

        self.assertEqual(main_list, nested_coll.a)
        self.assertEqual(main_dict, nested_coll.b)
        self.assertEqual(main_tuple, nested_coll.c)
        self.assertEqual(main_set, set(nested_coll.d))
        
        # Test Replication
        nested_coll.new_replica(backend_id=environment2_id)

        nested_coll_locations = nested_coll.get_all_locations()

        # Check that object is replicated
        self.assertEqual(len(nested_coll_locations), 2)
        self.assertIn(environment1_id, nested_coll_locations)
        self.assertIn(environment2_id, nested_coll_locations)

        replicated_list = nested_coll.run_remote(environment2_id, DCLAY_GETTER_PREFIX + 'a', None)
        replicated_dict = nested_coll.run_remote(environment2_id, DCLAY_GETTER_PREFIX + 'b', None)
        replicated_tuple = nested_coll.run_remote(environment2_id, DCLAY_GETTER_PREFIX + 'c', None)
        replicated_set = nested_coll.run_remote(environment2_id, DCLAY_GETTER_PREFIX + 'd', None)

        self.assertEqual(replicated_list, nested_coll.a)
        self.assertEqual(replicated_dict, nested_coll.b)
        self.assertEqual(replicated_tuple, nested_coll.c)
        self.assertEqual(replicated_set, nested_coll.d)

        # Test Version
        version_info, unloaded_version_info = nested_coll.new_version(environment1_id)
        logger.debug("Version info are:\n%s", version_info)
        versionOID = version_info.versionOID

        nested_coll_version = NestedColl.get_object_by_id(versionOID)
        logger.debug("New version of nested_coll is:\n%s", nested_coll_version)

        # NewVersion ID is different
        self.assertNotEqual(nested_coll.get_object_id(), nested_coll_version.get_object_id())

        # NewVersion fields are the same of the original
        self.assertEqual(nested_coll.a, nested_coll_version.a)
        self.assertEqual(nested_coll.b, nested_coll_version.b)
        self.assertEqual(nested_coll.c, nested_coll_version.c)
        self.assertEqual(nested_coll.d, nested_coll_version.d)

        # Change fields and check that they are different from the original one
        dict_b = dict()
        dict_b["version"] = 23
        set_b = set()
        set_b.add(34)
        main_vers_list = [dict_b, [34, 2, 32, 4, 5], (1, 25, 3, 4, 5), set_b]
        main_vers_tuple = (dict_b, [1, 2, 35, 4, 5], (1, 2, 3, 42, 5), set_b)
        main_vers_dict = dict()
        main_vers_dict["vdict"] = dict_b 
        main_vers_dict["vlist"] = [1, 2, 3, 4, 3]
        main_vers_dict["vtuple"] = (4, 2, 3, 4, 2)
        main_vers_dict["vset"] = set_b
        main_vers_set = set()
        main_vers_set.add((2, 4, 6, 3))
        main_vers_set.add(3)
        main_vers_set.add("c")
        nested_coll_version.change_fields(main_vers_list, main_vers_dict, main_vers_tuple, main_vers_set)
        
        self.assertNotEqual(nested_coll.a, nested_coll_version.a)
        self.assertNotEqual(nested_coll.b, nested_coll_version.b)
        self.assertNotEqual(nested_coll.c, nested_coll_version.c)
        self.assertNotEqual(nested_coll.d, nested_coll_version.d)

        nested_coll.consolidate_version(unloaded_version_info)        
        
        self.assertEqual(main_vers_list, nested_coll.a)
        self.assertEqual(main_vers_dict, nested_coll.b)
        self.assertEqual(main_vers_tuple, nested_coll.c)
        self.assertEqual(main_vers_set, set(nested_coll.d))

        logger.debug("Test OK!")
