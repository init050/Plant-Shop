import random
import string

class VerificationCodeGenerator:
    @staticmethod
    def generate_6_digit_code():
        return ''.join(random.choices(string.digits, k=6))