from metis_lib import miningservices

if __name__ == "__main__":
    user_email = input("Enter miner email address")
    user_firstname = input("Enter user firstname")
    user_lastname = input("Enter user lastname")
    user_name = input("Enter miner user name")
    user_password = input("Enter user password")
    user_cpu_limit = input("Enter user cpu limit (ex: 4)")
    user_memory_limit = input("Enter user memory limit (ex: 8Gi")

    miningservices.deploy(
        email=user_email,
        username=user_name,
        password=user_password,
        firstname=user_firstname,
        lastname=user_lastname,
        cpu_limit=int(user_cpu_limit),
        memory_limit=user_memory_limit,
        storage_limit="10Gi"
    )
