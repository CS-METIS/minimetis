# minimetis
The following procedure has been tested on Ubuntu 20.04 using bash shell
## METIS admin plane
### Install
- Install prerequisite
```bash
$ ./install_prerequisite
```
- Then edit <code>metis.env</code> file
Most of the time, you have have only to set the environment variables PRIVATE_IF, DOMAIN and SHARED_STORAGE_SIZE.
- Export environment variables
```bash
$ source metis.env
```
- Run the install script
```
$ ./install.sh
```
### Configuration of the admin client host
replace PUBLIC_IP by the IP address of the host where you install the minimetis admin plane.
Replace DOMAIN by the value of the DOMAIN environment variable you set in the metis.env file.

- edit /etc/hosts file on linux or C:\Windows\System32\Drivers\etc\hosts on windows to add:
```
PUBLIC_IP	DOMAIN
```
- add the root certificate ./pki/CA.pem to the trusted root certificate of the client browser

## METIS admin plane
### add a new data mining plane
run:
```bash
$ python cli/add_dataminer_plane.py
```
### Configuration of the data miner client host
Replace PUBLIC_IP by the IP address of the host where you install the minimetis admin plane.
Replace DOMAIN by the value of the DOMAIN environment variable you set in the metis.env file.
Replace USERNAME by the user name choosen when adding the mining plane.
- edit /etc/hosts file on linux or C:\Windows\System32\Drivers\etc\hosts on windows to add:
```
PUBLIC_IP	DOMAIN
PUBLIC_IP	USERNAME.DOMAIN
PUBLIC_IP	scdf-USERNAME.DOMAIN
PUBLIC_IP	codeserver-USERNAME.DOMAIN
PUBLIC_IP	jupyterlab-USERNAME.DOMAIN
PUBLIC_IP	ungit-USERNAME.DOMAIN
PUBLIC_IP	filebrowser-USERNAME.DOMAIN
PUBLIC_IP   grafana-USERNAME.DOMAIN
```
- add the root certificate ./pki/CA Root Minimetis.pem to the trusted root certificate of the client browser

Once done the new mining plane is accessible after a few minutes at https://USERNAME.DOMAIN