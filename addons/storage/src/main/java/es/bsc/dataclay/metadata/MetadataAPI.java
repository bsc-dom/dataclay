package es.bsc.dataclay.metadata;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.params.ScanParams;
import redis.clients.jedis.resps.ScanResult;

import java.util.HashSet;
import java.util.HashMap;
import java.util.Set;
import java.util.Map;

import com.google.gson.Gson;

public class MetadataAPI {

    private Jedis jedis;
    private Gson gson = new Gson();

    public MetadataAPI(final String host, final int port) {
        jedis = new Jedis(host, port);
    }

    public void shutdown() {
        jedis.close();
    }

    public ObjectMetadata getObjectMetadata(final String objectID) {
        String value = jedis.get("/object/" + objectID);
        ObjectMetadata objMD = gson.fromJson(value, ObjectMetadata.class);
        return objMD;
    }

    public Map<String, BackendMetadata> getBackends() {
        String prefix = "/backend/";
        String cursor = ScanParams.SCAN_POINTER_START;

        Map<String, BackendMetadata> backendMetadatas = new HashMap<>();

        do {
            // Use the SCAN command to iterate over keys that match the prefix
            ScanResult<String> scanResult = jedis.scan(cursor, new ScanParams().match(prefix + "*"));

            scanResult.getResult().forEach((key) -> {
                String value = jedis.get(key);
                BackendMetadata backendMetadata = gson.fromJson(value, BackendMetadata.class);
                backendMetadatas.put(key, backendMetadata);
            });

            // Get the next cursor
            cursor = scanResult.getCursor();
        } while (!cursor.equals(ScanParams.SCAN_POINTER_START));

        return backendMetadatas;
    }

}
