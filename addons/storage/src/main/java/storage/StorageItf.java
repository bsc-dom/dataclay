
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
	 * @param objectMdJson
	 *                 object to retrieve its locations.
	 * @return locations of an object.
	 * @throws StorageException
	 *                          if an exception occurs
	 */
	public static List<String> getLocations(final String objectMdJson) throws StorageException {
		try {
      ObjectMetadata objectMd = ObjectMetadata.fromJson(objectMdJson);
			List<String> replicaBackendIds = objectMd.getReplicaBackendIds();
			String masterBackendId = objectMd.getMasterBackendId();
			replicaBackendIds.add(masterBackendId);
			return replicaBackendIds;
		} catch (final Exception e) {
			throw new StorageException("Error getting locations of object " + objectMdJson, e);
		}
	}


	/**
	 * @brief Create a new replica of the given object.
	 * @param objectMdJson
	 *            objectMdJson to be replicated.
	 * @param newBackendId
	 *            target backend of the new replica.
	 * @throws StorageException
	 *            if an exception occurs
	 */
	public static void newReplica(final String objectMdJson, final String newBackendId) throws StorageException {
		try {
      ObjectMetadata objectMd = ObjectMetadata.fromJson(objectMdJson);
			final String objectId = objectMd.getId();
			final String masterBackendId = objectMd.getMasterBackendId();

			BackendClient backendClient = getBackendClient(masterBackendId);
			backendClient.newObjectReplica(objectId, newBackendId);
		} catch (final Exception e) {
			throw new StorageException("Error creating new version of object " + objectMdJson, e);
		}
	}


	/**
	 * @brief Create a new version of the object in the specified host. If no
	 *        destination is specified random one is
	 *        selected.
	 * @param objectMdJson
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
	public static String newVersion(final String objectMdJson, final boolean preserveSource, final String optDestHost)
			throws StorageException {
		// TODO preserveSource is currently ignored, but we could take advantage of it
		try {
      ObjectMetadata objectMd = ObjectMetadata.fromJson(objectMdJson);
			final String objectId = objectMd.getId();
			final String masterBackendId = objectMd.getMasterBackendId();

			BackendClient backendClient = getBackendClient(masterBackendId);
			String newVersionInfo = backendClient.newObjectVersion(objectId);
			return newVersionInfo;
		} catch (final Exception e) {
			throw new StorageException("Error creating new version of object " + objectMdJson, e);
		}
	}

	public static void consolidateVersion(final String objectMdJson) throws StorageException {
		try {
      ObjectMetadata objectMd = ObjectMetadata.fromJson(objectMdJson);
			final String objectId = objectMd.getId();
			final String masterBackendId = objectMd.getMasterBackendId();

			BackendClient backendClient = getBackendClient(masterBackendId);
			backendClient.consolidateObjectVersion(objectId);
		} catch (final Exception e) {
			throw new StorageException("Error consolidating version " + objectMdJson, e);
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
