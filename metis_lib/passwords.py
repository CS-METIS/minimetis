import random
import string


def generate_random(length: int):
    letters = string.ascii_letters + string.digits + "#$%&()*+,-./:;<=>?@[]^_{|}~"
    return "".join(random.choice(letters) for i in range(length))
