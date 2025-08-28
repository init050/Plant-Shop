import uuid


class TokenGenerator:
    """
    A simple utility class for generating unique tokens using UUIDv4.
    """
    @staticmethod
    def generate():
        return str(uuid.uuid4()) 