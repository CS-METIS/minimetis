mkdir -p /home/sdorgan/stream-data/input
aws s3api create-bucket --bucket input --endpoint https://oos.eu-west-2.outscale.com
/usr/bin/s3fs input /home/sdorgan/stream-data/input -o passwd_file=/home/sdorgan/.config/credentials,use_path_request_style,url=https://oos.eu-west-2.outscale.com

mkdir -p /home/sdorgan/stream-data/images
aws s3api create-bucket --bucket images --endpoint https://oos.eu-west-2.outscale.com
/usr/bin/s3fs images /home/sdorgan/stream-data/images -o passwd_file=/home/sdorgan/.config/credentials,use_path_request_style,url=https://oos.eu-west-2.outscale.com

mkdir -p /home/sdorgan/stream-data/detection-output
aws s3api create-bucket --bucket detection-output --endpoint https://oos.eu-west-2.outscale.com
/usr/bin/s3fs detection-output /home/sdorgan/stream-data/detection-output -o passwd_file=/home/sdorgan/.config/credentials,use_path_request_style,url=https://oos.eu-west-2.outscale.com

mkdir -p /home/sdorgan/stream-data/recognition-output
aws s3api create-bucket --bucket recognition-output --endpoint https://oos.eu-west-2.outscale.com
/usr/bin/s3fs recognition-output /home/sdorgan/stream-data/recognition-output -o passwd_file=/home/sdorgan/.config/credentials,use_path_request_style,url=https://oos.eu-west-2.outscale.com

mkdir -p /home/sdorgan/cats_and_dogs/data
aws s3api create-bucket --bucket cats_and_dogs_data --endpoint https://oos.eu-west-2.outscale.com
/usr/bin/s3fs cats_and_dogs_data /home/sdorgan/cats_and_dogs/data -o passwd_file=/home/sdorgan/.config/credentials,use_path_request_style,url=https://oos.eu-west-2.outscale.com

mkdir -p /home/sdorgan/cats_and_dogs/input
aws s3api create-bucket --bucket cats_and_dogs_input --endpoint https://oos.eu-west-2.outscale.com
/usr/bin/s3fs cats_and_dogs_input /home/sdorgan/cats_and_dogs/input -o passwd_file=/home/sdorgan/.config/credentials,use_path_request_style,url=https://oos.eu-west-2.outscale.com

mkdir -p /home/sdorgan/cats_and_dogs/output
aws s3api create-bucket --bucket cats_and_dogs_output --endpoint https://oos.eu-west-2.outscale.com
/usr/bin/s3fs cats_and_dogs_output /home/sdorgan/cats_and_dogs/output -o passwd_file=/home/sdorgan/.config/credentials,use_path_request_style,url=https://oos.eu-west-2.outscale.com
