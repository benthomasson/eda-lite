Generate certs and move them here.

    mkcert -install
    mkcert example.com "*.example.com" example.test localhost 127.0.0.1 ::1
    mv example.com+5-key.pem certs/localhost.key
    mv example.com+5.pem certs/localhost.crt


