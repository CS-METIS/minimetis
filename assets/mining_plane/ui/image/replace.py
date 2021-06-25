import string
import os

if __name__ == "__main__":
    index_path = "/usr/local/apache2/htdocs/index.html"
    with open(index_path) as f:
        username = os.environ["USERNAME"]
        domain = os.environ["DOMAIN"]
        content = string.Template(f.read()).substitute(username=username, domain=domain)
    with open(index_path, "w") as f:
        f.write(content)
