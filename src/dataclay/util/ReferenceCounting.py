""" Class description goes here. """

"""
Created on 19 abr. 2018

@author: dgasull
"""
from dataclay.serialization.python.lang.IntegerWrapper import IntegerWrapper
from dataclay.serialization.python.lang.BooleanWrapper import BooleanWrapper
from dataclay.serialization.python.lang.StringWrapper import StringWrapper
import logging

logger = logging.getLogger("ReferenceCounting")
from dataclay.commonruntime.Runtime import getRuntime


class ReferenceCounting(object):
    """
    classdocs+
    """

    def __init__(self):
        """
        Constructor
        """
        self.reference_counting = dict()
        self.external_references = 0

    def increment_reference_counting(self, oid, hint):

        if not hint in self.reference_counting:
            references_per_hint = dict()
            self.reference_counting[hint] = references_per_hint
        else:
            references_per_hint = self.reference_counting.get(hint)

        if oid in references_per_hint:
            num_refs = references_per_hint.get(oid) + 1
        else:
            num_refs = 1
        references_per_hint[oid] = num_refs

    def serialize_reference_counting(self, dc_obj, io_file):
        """TODO: IMPORTANT: this should be removed in new serialization by using paddings to directly access reference counters inside
        metadata."""
        """
        @postcondition: Serialize reference counting (garbage collector information)
        @param dc_obj: dc object with ref counting
        @param io_file: Buffer in which to serialize
        @param reference_counting: Reference counting to serialize
        """
        self.external_references = 0
        if dc_obj.get_alias() is not None and dc_obj.get_alias() != "":
            logger.trace("Found alias reference")
            self.external_references = self.external_references + 1

        cur_dataclay_id = getRuntime().get_dataclay_id()
        if dc_obj.get_replica_locations() is not None and len(dc_obj.get_replica_locations()) != 0:
            for replica_loc in dc_obj.get_replica_locations():
                replica_dataclay_id = (
                    getRuntime().get_execution_environment_info(replica_loc).dataclay_instance_id
                )
                if replica_dataclay_id != cur_dataclay_id:
                    logger.trace("Found federation reference")
                    self.external_references = self.external_references + 1
                    break
        logger.trace(
            f"Serializing reference counting external references = {self.external_references}"
        )
        IntegerWrapper().write(io_file, self.external_references)
        IntegerWrapper().write(io_file, len(self.reference_counting))
        for location, ref_counting_in_loc in self.reference_counting.items():
            if location is None:
                BooleanWrapper().write(io_file, True)
            else:
                BooleanWrapper().write(io_file, False)
                StringWrapper().write(io_file, str(location))

            IntegerWrapper().write(io_file, len(ref_counting_in_loc))
            for oid, counter in ref_counting_in_loc.items():
                StringWrapper().write(io_file, str(oid))
                IntegerWrapper().write(io_file, counter)

    def has_no_references(self):
        return len(self.reference_counting) == 0 and self.external_references == 0
