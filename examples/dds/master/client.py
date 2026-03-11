from pycompss.dds import DDS
#from dataclay import Client
import dataclay
from pycompss.api.task import task

@task(returns=1)
def _filter(dds):
    print("##Filter numbers##")
    even_numbers = dds.filter( lambda x : x % 2 == 0 ).collect()
    return even_numbers

def main():
    print(dir(dataclay))
    #client = Client(host="127.0.0.1", username="testuser", password="s3cret", dataset="testdata")
    #client.start()

    print("##Creating DDS object and making it persistent##")
    data = range(10)
    dds = DDS().load(data)
    dds.make_persistent("dds")

    even_numbers=_filter(dds)

    print("##Print##")
    print(even_numbers)

if __name__ =='__main__':
    main()