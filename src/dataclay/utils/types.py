import uuid


def get_msg_id(id):
    if id is None:
        return None
    return str(id)


def get_id(msg_id):
    """Create the ID based on protobuf message.

    :param msg_id: Common protobuf message.

    :return: UUID based on param.
    """

    return uuid.UUID(msg_id) if msg_id else None
