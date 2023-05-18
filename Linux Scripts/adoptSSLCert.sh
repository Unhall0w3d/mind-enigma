#!/usr/bin/bash
#####################################
# Script created by Ken Perry, 2023 #
#       NOC THOUGHTS BLOG           #
#    https://www.nocthoughts.com    #
#####################################


# Prompt user to enter the URL of the website
echo "Please enter the URL of the website (without 'https://'):"
read website

# Check if user input is empty
if [ -z "$website" ]; then
    echo "Error: No website URL provided. Please run the script again with a valid URL."
    exit 1
fi

openssl_cnf_path="/etc/ssl/openssl.cnf"

# Detect system and set the path to the openssl.cnf file
if [ -f /etc/debian_version ]; then
    # Debian-based system
    dirpath="/usr/local/share/ca-certificates/"
    command="update-ca-certificates"
elif [ -f /etc/arch-release ]; then
    # Arch-based system
    dirpath="/etc/ca-certificates/trust-source/anchors/"
    command="trust extract-compat"
else
    echo "Error: This script supports only Debian and Arch based systems."
    exit 1
fi

# Create a temporary file
tempfile=$(mktemp)

# Status message
echo "Attempting to connect to $website and download the certificate chain..."

# Attempt to connect to the server and download the certificate chain
output=$(echo "QUIT" | openssl s_client -showcerts -servername "$website" -connect "$website":443 2>&1)
echo "$output" > $tempfile

# Check if the connection was successful
if ! grep -q "BEGIN CERTIFICATE" "$tempfile"; then
    echo "Error: Failed to connect to $website. Please ensure the URL is correct and the website is up."
    rm "$tempfile"
    exit 1
fi

# Check if 'unsafe legacy renegotiation' is supported
if echo "$output" | grep -q "unsafe legacy renegotiation"; then
    # Check and insert options in openssl.cnf if necessary
    echo "Ensuring UnsafeLegacyRenegotiation SSL option is enabled..."

    declare -A options
    options=(["openssl_init"]="ssl_conf = ssl_sect" ["ssl_sect"]="system_default = system_default_sect" ["system_default_sect"]="Options = UnsafeLegacyRenegotiation")

    for category in "${!options[@]}"; do
        if grep -q "^\[$category\]" $openssl_cnf_path; then
            if ! grep -q "^${options[$category]}" $openssl_cnf_path; then
                sudo sed -i "/^\[$category\]/a\\${options[$category]}" $openssl_cnf_path
            fi
        else
            echo "[$category]" | sudo tee -a $openssl_cnf_path
            echo "${options[$category]}" | sudo tee -a $openssl_cnf_path
        fi
    done
else
    echo "Unsafe legacy renegotiation not supported by $website, or enabled locally already. Skipping..."
fi

echo "Connection successful. Extracting certificate chain..."

awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/ {print $0}' $tempfile > chain.pem

# Status message
echo "Moving the certificate to $dirpath..."

# Move the certificate to the proper location
sudo mv chain.pem "$dirpath""$website".pem

# Status message
echo "Updating the trust database..."

# Update the trust database
sudo "$command"

# Print the result
echo "The certificate chain has been saved to $dirpath$website.pem and trusted."

# Clean up
echo "Cleaning up temporary files..."
rm "$tempfile"

echo "Done!"