from metis_lib import miningservices
from getpass import getpass

if __name__ == "__main__":
    user_email = input("Enter miner email address\n>>")
    user_firstname = input("Enter user firstname\n>>")
    user_lastname = input("Enter user lastname\n>>")
    user_name = input("Enter miner user name\n>>")
    user_password = getpass("Enter user password\n>>")
    user_cpu_limit = input("Enter user cpu limit (ex: 4)\n>>")
    user_memory_limit = input("Enter user memory limit (ex: 8Gi)\n>>")

    miningservices.deploy(
        email=user_email,
        username=user_name,
        password=user_password,
        firstname=user_firstname,
        lastname=user_lastname,
        cpu_limit=int(user_cpu_limit),
        memory_limit=user_memory_limit,
        storage_limit="10Gi",
    )
