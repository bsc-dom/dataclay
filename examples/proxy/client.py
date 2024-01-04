from model.company import Employee

from dataclay import Client

client = Client(proxy_host="127.0.0.1", username="testuser", password="s3cret", dataset="testdata")
client.start()

backends = list(client.get_backends().keys())
print("There are #%d backends: %s" % (len(backends), backends))

e = Employee("John Smith", 4.5)
e.make_persistent(backend_id=backends[0])

print("Payroll: %f" % e.get_payroll(42))
print("Name: %s" % e.name)

print("Moving object between backends...")
e.move(backends[1])

print("Payroll: %f" % e.get_payroll(42))
print("Name: %s" % e.name)
