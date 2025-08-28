import random
import string


class VerificationCodeGenerator:
    """
    A utility class for generating random verification codes.
    """
    @staticmethod
    def generate_6_digit_code():
        """
        Generates a random 6-digit string of numbers.
        """
        return ''.join(random.choices(string.digits, k=6))