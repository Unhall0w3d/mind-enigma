#!/bin/bash

# Prompt user to enter the URL of the website
echo "Please enter the URL of the website (without 'https://'):"
read website

# Check if user input is empty
if [ -z "$website" ]; then
    echo "Error: No website URL provided. Please run the script again with a valid URL."
    exit 1
fi

# Create a temporary file
tempfile=$(mktemp)

# Status message
echo "Attempting to connect to $website and download the certificate chain..."

# Attempt to connect to the server and download the certificate chain
echo "QUIT" | openssl s_client -showcerts -servername "$website" -connect "$website":443 > $tempfile 2>/dev/null

# Check if the connection was successful
if ! grep -q "BEGIN CERTIFICATE" "$tempfile"; then
    echo "Error: Failed to connect to $website. Please ensure the URL is correct and the website is up."
    rm "$tempfile"
    exit 1
fi

echo "Connection successful. Extracting certificate chain..."

awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/ {print $0}' $tempfile > chain.pem

# Status message
echo "Moving the certificate to the proper location..."

# Move the certificate to the proper location
sudo mv chain.pem /etc/ca-certificates/trust-source/anchors/"$website".pem

# Status message
echo "Updating the trust database..."

# Update the trust database
sudo trust extract-compat

# Print the result
echo "The certificate chain has been saved to /etc/ca-certificates/trust-source/anchors/$website.pem and trusted."

# Clean up
echo "Cleaning up temporary files..."
rm "$tempfile"

echo "Done!"