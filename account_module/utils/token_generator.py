import uuid

class TokenGenerator:
    @staticmethod
    def generate():
        return str(uuid.uuid4()) 