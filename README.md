# minimetis
The following procedure has been tested on Ubuntu 20.04 using bash shell
## Installation of the METIS admin plane
- Install prerequisite
```bash
$ ./install_prerequisite
```
- Then edit <code>metis.env</code> file
Most of the time, you have have to set the environment variables PRIVATE_IF and DOMAIN.
- Export environment variables
```bash
$ source metis.env
```
- Run the install script
```
$ ./install.sh
```
## Configuration of the client host
replace PUBLIC_IP by the IP address of the host where you install the minimetis admin plane.

Replace DOMAIN by the value of the DOMAIN environment variable you set in the metis.env file.
- edit /etc/hosts file on linux or C:\Windows\System32\Drivers\etc\hosts on windows to add:
```
PUBLIC_IP	DOMAIN.dev
PUBLIC_IP	portainer.DOMAIN.dev
```
- add the root certificate ./pki/CA.pem to the trusted root certificate of the client browser

