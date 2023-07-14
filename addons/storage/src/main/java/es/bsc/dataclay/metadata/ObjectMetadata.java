package es.bsc.dataclay.metadata;

import java.util.List;


public class ObjectMetadata {
    private String id;
    private String dataset_name;
    private String class_name;
    private String backend_id;
    private List<String> replica_backend_ids;
    private boolean is_read_only;
    private String original_object_id;
    private List<String> versions_object_ids;

    // Getters
    public String getId() {
        return this.id;
    }

    public String getDatasetName() {
        return this.dataset_name;
    }

    public String getClassName() {
        return this.class_name;
    }

    public String getBackendId() {
        return this.backend_id;
    }

    public List<String> getReplicaBackendIds() {
        return this.replica_backend_ids;
    }

    public boolean getIsReadOnly() {
        return this.is_read_only;
    }

    public String getOriginalObjectId() {
        return this.original_object_id;
    }

    public List<String> getVersionsObjectIds() {
        return this.versions_object_ids;
    }
}
