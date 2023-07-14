
package storage;

import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Random;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.UUID;
import java.util.HashMap;

// import es.bsc.dataclay.api.Backend;
// import es.bsc.dataclay.api.BackendID;
// import es.bsc.dataclay.api.CallbackEvent;
// import es.bsc.dataclay.api.CallbackHandler;
// import es.bsc.dataclay.api.DataClay;
// import es.bsc.dataclay.api.DataClayException;
// import es.bsc.dataclay.commonruntime.ClientRuntime;
// import es.bsc.dataclay.communication.grpc.messages.common.CommonMessages.Langs;
// import es.bsc.dataclay.util.Configuration;
// import es.bsc.dataclay.util.ids.ExecutionEnvironmentID;
// import es.bsc.dataclay.util.ids.MetaClassID;
// import es.bsc.dataclay.util.ids.ObjectID;
// import es.bsc.dataclay.util.ids.SessionID;
// import es.bsc.dataclay.util.info.VersionInfo;
// import es.bsc.dataclay.util.management.metadataservice.MetaDataInfo;
// import es.bsc.dataclay.util.structs.Triple;
// import es.bsc.dataclay.util.structs.Tuple;

import es.bsc.dataclay.metadata.ObjectMetadata;
import es.bsc.dataclay.metadata.BackendMD;
// import es.bsc.dataclay.metadata.MetadataClient;
import es.bsc.dataclay.metadata.MetadataAPI;

import es.bsc.dataclay.backend.BackendClient;


/**
 * This class intends to offer a basic API based on Severo Ochoa project needs.
 */
public final class StorageItf {

	// private static MetadataClient metadataClient = new MetadataClient("127.0.0.1:16587");
	private static MetadataAPI metadataAPI = new MetadataAPI("localhost", 6379);

	private static Map<String, BackendClient> backendClients = new HashMap<>();


	/**
	 * @brief Gets all the locations of an object.
	 * @param objectIDstr
	 *            object to retrieve its locations.
	 * @return locations of an object.
	 * @throws StorageException
	 *             if an exception occurs
	 */
	public static List<String> getLocations(final String objectIDstr) throws StorageException {
		try {
			ObjectMetadata objMD = metadataAPI.getObjectMetadata(objectIDstr);
            List<String> locations = objMD.getReplicaBackendIds();
            String backend = objMD.getBackendId();
            locations.add(backend);
            return locations;
		} catch (final Exception e) {
			throw new StorageException(e);
		}
	}

	public static BackendClient getBackendClient(final String backendID) throws StorageException {
		BackendClient backendClient = backendClients.get(backendID);
		if (backendClient == null) {
			updateBackendClients();
			backendClient = backendClients.get(backendID);
			if (backendClient == null) {
				throw new StorageException("Backend " + backendID + " not found");
			}
		}
		return backendClient;
	}

	public static void updateBackendClients() throws StorageException {
		Map<String, BackendMD> backendMDs = metadataAPI.getBackends();

		for (BackendMD backendMD : backendMDs.values()) {
			if (!backendClients.containsKey(backendMD.getId())) {
				BackendClient backendClient = new BackendClient(backendMD.getHostname(), backendMD.getPort());
				backendClients.put(backendMD.getId(), backendClient);
			}
        }
	}

	public static void newAccount(final String username, String password) {
		// metadataClient.newAccount(username, password);

	}

	/**
	 * @brief Create a new version of the object in the specified hostname. If no destination is specified random one is
	 *        selected.
	 * @param objectIDstr
	 *            object id to be versioned
	 * @param preserveSource
	 *            whether the source object is preserved or otherwise can be deleted.
	 * @param optDestHost
	 *            target location for the version of the object (if null, a random location will be chosen).
	 * @return the object id of the corresponding to the new version of the object.
	 * @throws StorageException
	 *             if an exception occurs
	 */
	// public static String newVersion(final String objectIDstr, final boolean preserveSource, final String optDestHost) throws StorageException {
	// 	// TODO preserveSource is currently ignored, but we could take advantage of it (jmarti 15-09-2017)
	// 	try {
	// 		ClientRuntime commonLib = DataClay.getCommonLib();
	// 		// Check object language to select destination backends

	// 		final Triple<ObjectID, BackendID, MetaClassID> ids = DataClay.string2IDandHintID(objectIDstr);
	// 		final ObjectID originalObjectID = ids.getFirst();
	// 		final BackendID originalHint = ids.getSecond();
	// 		final MetaClassID originalClassID = ids.getThird();

	// 		Tuple<ObjectID, BackendID> result = commonLib.newVersion(originalObjectID,
	// 				(ExecutionEnvironmentID) originalHint, originalClassID, null, null, optDestHost);
	// 		ObjectID versionOID = result.getFirst();
	// 		BackendID destBackendID = result.getSecond();
	// 		if (DEBUG_ENABLED) {
	// 			System.out.println("[DATACLAY] Object " + originalObjectID + " versioned in " + destBackendID);
	// 			// System.out.println("[DATACLAY] Current versions " + versions.toString());
	// 		}

	// 		return DataClay.ids2String(versionOID, destBackendID, originalClassID);
	// 	} catch (final Exception ex) {
	// 		ex.printStackTrace();
	// 		throw new StorageException(ex);
	// 	}
	// }

	public static void main(String[] args) throws Exception {
		System.out.println("Hello World!");

		System.out.println(getLocations("dc548dd1-1561-44b4-9d78-bfd7e386b420"));

		newAccount("user1", "pass1");


		getBackendClient("271bd4b4-074f-499e-90b8-7302b1fee1b5");

		for (String key : backendClients.keySet()) {
			System.out.println(key);
		}

  	}

		/**
	 * @brief Finish connections to DataClay.
	 * @throws StorageException
	 *             if an exception occurs
	 */
	public static void finish() throws StorageException {
		try {
			metadataAPI.shutdown();
			for (BackendClient backendClient : backendClients.values()) {
				backendClient.shutdown();
			}
		} catch (final Exception e) {
			throw new StorageException(e);
		}
	}

}
