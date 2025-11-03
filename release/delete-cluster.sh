#!/usr/bin/env bash
set -euo pipefail

PROJECT="${1:?Usage: ./delete-cluster.sh <gcp-project> <cluster-name> <zone>}"
CLUSTER="${2:?}"
ZONE="${3:-us-central1-a}"

echo "Deleting cluster $CLUSTER ..."
gcloud container clusters delete "$CLUSTER" \
  --project "$PROJECT" \
  --zone "$ZONE" \
  --quiet

# Usage: ./delete-cluster.sh student-desktop-dev lab-cluster us-central1-a