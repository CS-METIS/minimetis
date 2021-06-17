from metis_lib import miningservices

if __name__ == "__main__":
    miningservices.deploy(
        email="sebastien.dorgan@csgroup.eu",
        username="sdorgan",
        password="azer1234",
        firstname="Sébastien",
        lastname="Dorgan",
        cpu_limit=2,
        memory_limit="2Gi",
        storage_limit="10Gi"
    )
