#!/usr/bin/env bash
set -euo pipefail

PROJECT="${1:?Usage: ./create-cluster.sh <gcp-project> <cluster-name> <zone>}"
CLUSTER="${2:?}"
ZONE="${3:-us-central1-a}"

echo "Enabling GKE API in $PROJECT ..."
gcloud services enable container.googleapis.com --project "$PROJECT"

echo "Creating cluster $CLUSTER in $ZONE ..."
gcloud container clusters create "$CLUSTER" \
  --project "$PROJECT" \
  --zone "$ZONE" \
  --machine-type "e2-standard-4" \
  --num-nodes "1" \
  --enable-autoscaling --min-nodes "0" --max-nodes "10"

echo "Getting kubeconfig ..."
gcloud container clusters get-credentials "$CLUSTER" \
  --zone "$ZONE" --project "$PROJECT"


# Usage ./create-cluster.sh student-desktop-dev lab-cluster us-central1-a
