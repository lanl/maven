#!/bin/bash
# Generates (idempotently) a throwaway local CA and a leaf certificate for
# api.github.com, signed by that CA. Used only to let a local fake-GitHub
# HTTPS server present a cert that `truststore` (and thus the unmodified
# updater.py) will trust once the CA is added to the macOS System keychain.
#
# This is a freshly generated, single-purpose CA -- never a real machine's
# installed root or any corporate/proxy cert. It must never be committed;
# the output directory is gitignored.
#
# Usage: gen_local_ca.sh <ca_dir>
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "usage: $0 <ca_dir>" >&2
    exit 1
fi

ca_dir="$1"
mkdir -p "$ca_dir"

ca_key="$ca_dir/ca.key"
ca_cert="$ca_dir/ca.pem"
leaf_key="$ca_dir/leaf.key"
leaf_cert="$ca_dir/leaf.pem"
leaf_csr="$ca_dir/leaf.csr"
leaf_ext="$ca_dir/leaf.ext"

if [ -f "$ca_cert" ] && [ -f "$ca_key" ] && [ -f "$leaf_cert" ] && [ -f "$leaf_key" ]; then
    echo "==> Local CA + leaf cert already exist in $ca_dir, reusing"
    exit 0
fi

echo "==> Generating local CA"
openssl req -x509 -newkey rsa:2048 -days 7 -nodes \
    -keyout "$ca_key" -out "$ca_cert" \
    -subj "/CN=maven-local-update-test-CA" \
    -addext "basicConstraints=critical,CA:TRUE" \
    -addext "keyUsage=critical,keyCertSign,cRLSign" \
    >/dev/null 2>&1

echo "==> Generating leaf key + CSR for api.github.com"
openssl req -newkey rsa:2048 -nodes \
    -keyout "$leaf_key" -out "$leaf_csr" \
    -subj "/CN=api.github.com" \
    >/dev/null 2>&1

cat > "$leaf_ext" <<'EOF'
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:api.github.com
EOF

echo "==> Signing leaf cert with local CA"
openssl x509 -req -in "$leaf_csr" -CA "$ca_cert" -CAkey "$ca_key" \
    -CAcreateserial -days 7 -extfile "$leaf_ext" \
    -out "$leaf_cert" >/dev/null 2>&1

rm -f "$leaf_csr" "$leaf_ext" "$ca_dir/ca.srl"

echo "==> Generated CA at $ca_cert, leaf cert at $leaf_cert (both valid 7 days)"
