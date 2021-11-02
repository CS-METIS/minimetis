from metis_lib import miningservices
import logging
# import sys

root = logging.getLogger()
root.setLevel(logging.INFO)

# handler = logging.StreamHandler(sys.stdout)
# handler.setLevel(logging.INFO)
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# handler.setFormatter(formatter)
# root.addHandler(handler)


if __name__ == "__main__":
    # username = input("Enter user username\n>>")
    username = "toto"

    miningservices.destroy(username=username)
