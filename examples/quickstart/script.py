from model.company import Employee, Company

from dataclay import Client

client = Client(host="127.0.0.1", username="testuser", password="s3cret", dataset="testdata")
client.start()
