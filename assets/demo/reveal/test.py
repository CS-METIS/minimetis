from reveal import orientapi as api
from reveal import model
import io
client = api.OrientDBClient()

print(client.get("DVFfinal","Adresse", "#19:0"))

print("\n")

mut = client.get("DVFfinal", "Mutation", "#13:485")
print(mut)
print(mut.__dict__)

print("\n")

print(client.get("DVFfinal", "Disposition", "#17:857"))

sio = io.StringIO("ksflqmsdkjfqsdmjfml\nsklqfjldq")

print(f"{sio.getvalue()}")
print(api.orient_type_name(io.StringIO))