echo "This script gets status of the docker containers on the server."
echo IP of server?
read ip
echo Username?
read username
ssh $username@$ip -t "cd /home/${username}/civlab_api && sudo docker-compose ps && sudo docker-compose images"