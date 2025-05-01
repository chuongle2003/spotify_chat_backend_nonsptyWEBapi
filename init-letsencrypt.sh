   #!/bin/bash

   if ! [ -x "\" ]; then
     echo 'Error: docker-compose is not installed.' >&2
     exit 1
   fi

   domains=(spotifybackend.shop www.spotifybackend.shop)
   rsa_key_size=4096
   data_path="./certbot"
   email="chuongle.nt1@gmail.com" # Thay đổi email này

   if [ -d "\" ]; then
     read -p "Existing data found for \. Continue and replace existing certificate? (y/N) " decision
     if [ "\" != "Y" ] && [ "\" != "y" ]; then
       exit
     fi
   fi

   if [ ! -d "\/conf/live/\" ]; then
     mkdir -p "\/conf/live/\"
   fi

   echo "### Creating dummy certificate for \ ..."
   mkdir -p "\/conf/live/\"
   docker-compose run --rm --entrypoint "\
     openssl req -x509 -nodes -newkey rsa:\ -days 1\
       -keyout '/etc/letsencrypt/live/\/privkey.pem' \
       -out '/etc/letsencrypt/live/\/fullchain.pem' \
       -subj '/CN=localhost'" certbot

   echo "### Starting nginx ..."
   docker-compose up --force-recreate -d nginx

   echo "### Deleting dummy certificate for \ ..."
   docker-compose run --rm --entrypoint "\
     rm -Rf /etc/letsencrypt/live/\ && \
     rm -Rf /etc/letsencrypt/archive/\ && \
     rm -Rf /etc/letsencrypt/renewal/\.conf" certbot

   echo "### Requesting Let's Encrypt certificate for \ ..."
   domain_args=""
   for domain in "\"; do
     domain_args="\ -d \"
   done

   docker-compose run --rm --entrypoint "\
     certbot certonly --webroot -w /var/www/certbot \
       \ \
       --email \ \
       --rsa-key-size \ \
       --agree-tos \
       --force-renewal" certbot

   echo "### Reloading nginx ..."
   docker-compose exec nginx nginx -s reload