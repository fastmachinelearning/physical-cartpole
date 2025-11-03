#!/usr/bin/env bash
set -euo pipefail

NS="${1:?Usage: ./destroy-lab.sh <namespace>}"

echo "Deleting lab namespace: $NS"
kubectl delete ns "$NS" --ignore-not-found

# Usage: ./delete-lab.sh lab-test