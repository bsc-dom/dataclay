package es.bsc.dataclay.metadata;

import java.util.List;
import com.google.gson.Gson;


public class ObjectMetadata {
    private String id;
    private String dataset_name;
    private String class_name;
    private String master_backend_id;
    private List<String> replica_backend_ids;
    private boolean is_read_only;
    private String original_object_id;
    private List<String> versions_object_ids;

    private static Gson gson = new Gson();

    public static ObjectMetadata fromJson(String objectMdJson)
    {
        return gson.fromJson(objectMdJson, ObjectMetadata.class);
    }

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

    public String getMasterBackendId() {
        return this.master_backend_id;
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
