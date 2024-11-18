from dataclay import Client


def test_client_settings(client):
    client_test = Client(
        host="127.0.0.1", username="testuser", password="s3cret", dataset="testdata"
    )
    client_test.start()
    assert client_test.settings.dataclay_host == "127.0.0.1"
