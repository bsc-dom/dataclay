package es.bsc.dataclay.metadata;


public class BackendMetadata {
    private String id;
    private String host;
    private int port;
    private String dataclay_id;

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
