from metis_lib import sh
import os
from pathlib import Path
from OpenSSL import crypto  # type: ignore
from OpenSSL.SSL import FILETYPE_PEM  # type: ignore
from certauth.certauth import CertificateAuthority  # type: ignore

# openssl req  -nodes -new -x509  -keyout server.key -out server.cert -subj "/C=US/ST=Oregon/L=Portland/O=Company Name/OU=Org/CN=www.example.com"
# openssl pkcs12 -export -inkey server.key -in server.cert -out kc.pkcs12 -name whatever.com

domain = os.environ.get("DOMAIN", "minimetis.dev")
# config = """[req]
# distinguished_name=dn
# [ dn ]
# [ ext ]
# basicConstraints=CA:TRUE,pathlen:0
# """


class PKI:
    def __init__(self) -> None:
        self.ca = CertificateAuthority(ca_name="CA", ca_file_cache="/tmp/cert.pem")

    def create_ca_cert(self, output_dir: str = "pki", ca_name: str = "CA"):
        p = Path(output_dir)
        if not p.exists():
            p.mkdir()
        ca_cert, ca_key = self.ca.generate_ca_root(ca_name=ca_name)
        ca_cert_file = f"{output_dir}/{ca_name}.pem"
        with open(ca_cert_file, "bw") as f:
            f.write(crypto.dump_certificate(FILETYPE_PEM, ca_cert))
        ca_key_file = f"{output_dir}/{ca_name}.key"
        with open(ca_key_file, "bw") as f:
            f.write(crypto.dump_privatekey(FILETYPE_PEM, ca_key))
        return ca_cert_file, ca_key_file

    def create_server_cert(
        self,
        ca_cert_file: str,
        ca_key_file: str,
        output_dir: str = "pki",
        domain: str = domain,
    ):
        with open(ca_cert_file, "rb") as f:
            ca_cert = crypto.load_certificate(FILETYPE_PEM, f.read())
        with open(ca_key_file, "rb") as f:
            ca_key = crypto.load_privatekey(FILETYPE_PEM, f.read())
        server_cert, server_key = self.ca.generate_host_cert(domain, ca_cert, ca_key, wildcard=True)
        server_cert_file = f"{output_dir}/server.pem"
        with open(server_cert_file, "bw") as f:
            f.write(crypto.dump_certificate(FILETYPE_PEM, server_cert))
        server_key_file = f"{output_dir}/server.key"
        with open(server_key_file, "bw") as f:
            f.write(crypto.dump_privatekey(FILETYPE_PEM, server_key))
        return server_cert_file, server_key_file


def create_keystore(
    keypath: str,
    certpath: str,
    password: str,
    output: str = "kc.pkcs12",
    domain: str = domain,
):
    sh.run(
        f"openssl pkcs12 -export -inkey {keypath} -in {certpath} -out {output} -name {domain} -password pass:{password}"
    )
