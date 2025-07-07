#!/bin/bash
# Start the Django development server using HTTPS.
CERT_FILE="cert.pem"
KEY_FILE="key.pem"

if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo "Generating self-signed certificate..."
    openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
        -keyout "$KEY_FILE" -out "$CERT_FILE" \
        -subj "/CN=localhost"
fi

python manage.py runserver 0.0.0.0:8000 --cert "$CERT_FILE" --key "$KEY_FILE"
