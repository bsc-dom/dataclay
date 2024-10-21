import logging
import os

from model.client_model import Client_model

from dataclay import Client

logger = logging.getLogger(__name__)

logger.debug("First Debug log")
logger.info("First Info log")

logging.basicConfig(force=True, level=getattr(logging, os.getenv("LOG_LEVEL", "DEBUG").upper()))
dclogger = logging.getLogger("dataclay")
dclogger.setLevel(logging.INFO)
grpclogger = logging.getLogger("grpc")
grpclogger.setLevel(logging.INFO)

client = Client(host="127.0.0.1", username="testuser", password="s3cret", dataset="testdata")
client.start()

client_mod = Client_model("Client")
client_mod.make_persistent("alias")

name = client_mod.get_name()
logger.debug("My name is : %s", name)
logger.info("My name is : %s", name)
