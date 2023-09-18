package es.bsc.dataclay.metadata;

import com.google.gson.Gson;

public class BackendMetadata {
    private String id;
    private String host;
    private int port;
    private String dataclay_id;
    private static Gson gson = new Gson();

    public static BackendMetadata fromJson(String backendMdJson)
    {
      return gson.fromJson(backendMdJson, BackendMetadata.class);
    }

    // Getters
    public String getId() {
        return this.id;
    }

    public String getHost() {
        return this.host;
    }

    public int getPort() {
        return this.port;
    }

    public String getDataclayId() {
        return this.dataclay_id;
    }
}
