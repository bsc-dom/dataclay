
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

import javax.security.auth.login.Configuration;

import java.util.HashMap;

import es.bsc.dataclay.metadata.ObjectMetadata;
import es.bsc.dataclay.metadata.BackendMetadata;
import es.bsc.dataclay.metadata.MetadataAPI;

import es.bsc.dataclay.backend.BackendClient;

/**
 * This class intends to offer a basic API based on Severo Ochoa project needs.
 */
public final class StorageItf {

	private static MetadataAPI metadataAPI = new MetadataAPI("localhost", 6379);
	private static Map<String, BackendClient> backendClients = new HashMap<>();


	public static void init(final String configFilePath) throws StorageException {

	}


	/**
	 * @brief Gets all the locations of an object.
	 * @param objectId
	 *                 object to retrieve its locations.
	 * @return locations of an object.
	 * @throws StorageException
	 *                          if an exception occurs
	 */
	public static List<String> getLocations(final String objectId) throws StorageException {
		try {
			ObjectMetadata objectMetadata = metadataAPI.getObjectMetadata(objectId);
			List<String> replicaBackendIds = objectMetadata.getReplicaBackendIds();
			String masterBackendId = objectMetadata.getMasterBackendId();
			replicaBackendIds.add(masterBackendId);
			return replicaBackendIds;
		} catch (final Exception e) {
			throw new StorageException("Error getting locations of object " + objectId, e);
		}
	}


	/**
	 * @brief Create a new replica of the given object.
	 * @param objectInfo
	 *            objectInfo to be replicated.
	 * @param backendId
	 *            target backend of the new replica.
	 * @throws StorageException
	 *            if an exception occurs
	 */
	public static void newReplica(final String objectInfo, final String backendId) throws StorageException {
		try {
			String[] splitObjectInfo = objectInfo.split(":");
			final String objectId = splitObjectInfo[0];
			final String masterBackendId = splitObjectInfo[1];
			// final String className = splitObjectInfo[2];

			BackendClient backendClient = getBackendClient(masterBackendId);
			backendClient.newObjectReplica(objectId, backendId);
		} catch (final Exception e) {
			throw new StorageException("Error creating new version of object " + objectInfo, e);
		}
	}


	/**
	 * @brief Create a new version of the object in the specified host. If no
	 *        destination is specified random one is
	 *        selected.
	 * @param objectInfo
	 *                       object id to be versioned
	 * @param preserveSource
	 *                       whether the source object is preserved or otherwise can
	 *                       be deleted.
	 * @param optDestHost
	 *                       target location for the version of the object (if null,
	 *                       a random location will be chosen).
	 * @return the object id of the corresponding to the new version of the object.
	 * @throws StorageException
	 *                          if an exception occurs
	 */
	public static String newVersion(final String objectInfo, final boolean preserveSource, final String optDestHost)
			throws StorageException {
		// TODO preserveSource is currently ignored, but we could take advantage of it
		try {
			String[] splitObjectInfo = objectInfo.split(":");
			final String objectId = splitObjectInfo[0];
			final String masterBackendId = splitObjectInfo[1];
			// final String className = splitObjectInfo[2];

			BackendClient backendClient = getBackendClient(masterBackendId);
			String newVersionInfo = backendClient.newObjectVersion(objectId);

			return newVersionInfo;
		} catch (final Exception e) {
			throw new StorageException("Error creating new version of object " + objectInfo, e);
		}
	}

	public static void consolidateVersion(final String objectInfo) throws StorageException {
		try {
			String[] splitObjectInfo = objectInfo.split(":");
			final String objectId = splitObjectInfo[0];
			final String masterBackendId = splitObjectInfo[1];
			// final String className = splitObjectInfo[2];

			BackendClient backendClient = getBackendClient(masterBackendId);
			backendClient.consolidateObjectVersion(objectId);
		} catch (final Exception e) {
			throw new StorageException("Error consolidating version " + objectInfo, e);
		}
	}

	public static BackendClient getBackendClient(final String backendId) throws StorageException {
		BackendClient backendClient = backendClients.get(backendId);
		if (backendClient == null) {
			updateBackendClients();
			backendClient = backendClients.get(backendId);
			if (backendClient == null) {
				throw new StorageException("Backend " + backendId + " not found");
			}
		}
		return backendClient;
	}

	public static void updateBackendClients() throws StorageException {
		Map<String, BackendMetadata> backendMetadatas = metadataAPI.getBackends();

		for (BackendMetadata backendMetadata : backendMetadatas.values()) {
			if (!backendClients.containsKey(backendMetadata.getId())) {
				BackendClient backendClient = new BackendClient(backendMetadata.getHost(), backendMetadata.getPort());
				backendClients.put(backendMetadata.getId(), backendClient);
			}
		}
	}

	/**
	 * @brief Finish connections to DataClay.
	 * @throws StorageException
	 *                          if an exception occurs
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

	public static void main(String[] args) throws Exception {

		String objectId = "13ca3710-d971-47fc-bcbb-58daf047352f";
		String backendId = "f3ec9132-40fb-4c72-8a5b-4dd0a280a6f2";
		String objectInfo = objectId + ":" + backendId + ":" + "es.bsc.dataclay.logic.LogicModule";

		System.out.println(getLocations(objectId));

		getBackendClient(backendId);

		for (String key : backendClients.keySet()) {
			System.out.println(key);
		}

		newVersion(objectInfo, true, null);

		newReplica(objectInfo, "9012d76c-ea44-4112-b646-178ee6dbcf0e");

	}

}
