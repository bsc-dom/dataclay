from unittest import TestCase
from unittest.mock import Mock
from dataclay.heap.ClientHeapManager import ClientHeapManager
import uuid


class TestClientHeapManager(TestCase):

    def test_add_to_heap(self):
        runtime = Mock()
        dc_object = Mock()
        object_id = uuid.uuid4()
        dc_object.get_object_id.return_value = object_id
        heap_manager = ClientHeapManager(runtime)
        heap_manager.add_to_heap(dc_object)
        retrieved_object = heap_manager.get_from_heap(object_id)
        self.assertEqual(retrieved_object, dc_object)

    def test_flush_all(self):
        pass
        #self.fail()

    def test_run_task(self):
        pass
        #self.fail()
