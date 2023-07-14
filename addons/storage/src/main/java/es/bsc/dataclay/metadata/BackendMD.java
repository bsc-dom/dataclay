package es.bsc.dataclay.metadata;


public class BackendMD {
    private String id;
    private String hostname;
    private int port;
    private String dataclay_id;

    // Getters
    public String getId() {
        return this.id;
    }

    public String getHostname() {
        return this.hostname;
    }

    public int getPort() {
        return this.port;
    }

    public String getDataclayId() {
        return this.dataclay_id;
    }
}
