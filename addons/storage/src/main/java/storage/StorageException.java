package storage;

public class StorageException extends Exception {
	/** Generated serial version UID. */
	private static final long serialVersionUID = 6182015160913789272L;


	public StorageException() {
		super();
	}

	public StorageException(final Exception ex) {
		super(ex);
	}

	public StorageException(final String msg) {
		super(msg);
	}
}
