# Cloud Lab Deployment

This guide explains how to reproduce the Google Cloud–hosted environment prepared for the Physical CartPole student lab. The automation lives in `release/` and ships with helper scripts for GKE, Kubernetes manifests, and a reference operator cheat sheet.

## Overview
- A GitHub workflow builds the student workstation image (`release/Dockerfile`) and pushes it to Artifact Registry (e.g. `us-central1-docker.pkg.dev/<project>/docker-repo/student-desktop:latest`).
- The Vitis/Vivado installation is stored on a pre-populated GCE Persistent Disk that is mounted read-only into every pod through `release/vivado-pv-pvc.yaml`.
- `release/deploy-lab.sh` provisions one pod per student, configures SSH access via a bastion, and applies a NetworkPolicy so only the bastion can reach student pods.
- Students connect through the bastion using SSH with X11 forwarding for GUI workflows that require Vivado/Vitis.

## Starting From Scratch
Follow these steps if you are bootstrapping a new Google Cloud + GitHub environment.

### 1. Create or select a Google Cloud project
```bash
PROJECT_ID=<new-project-id>
gcloud projects create "$PROJECT_ID"
gcloud config set project "$PROJECT_ID"
```
Enable the required APIs:
```bash
gcloud services enable \
  artifactregistry.googleapis.com \
  container.googleapis.com \
  compute.googleapis.com
```

### 2. Create the Artifact Registry repository
```bash
gcloud artifacts repositories create docker-repo \
  --project "$PROJECT_ID" \
  --location us-central1 \
  --repository-format docker \
  --description "Physical CartPole student images"
```
If you use a different region or repository name, update both `release/deploy-lab.sh` and `.github/workflows/docker-build.yml`.

### 3. Service account for GitHub Actions
Create a service account that can push images:
```bash
gcloud iam service-accounts create cartpole-ci \
  --display-name "CartPole CI"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member "serviceAccount:cartpole-ci@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/artifactregistry.writer
```
Export a JSON key and store it as the repository secret `GCP_SA_KEY`:
```bash
gcloud iam service-accounts keys create sa-key.json \
  --iam-account "cartpole-ci@${PROJECT_ID}.iam.gserviceaccount.com"
```
Upload `sa-key.json` to GitHub → Settings → Secrets and variables → Actions → New repository secret.

Add a repository variable named `GCP_PROJECT_ID` (matches the value referenced in `docker-build.yml`).

### 4. Self-hosted GitHub runner
`runs-on: fastml` in `.github/workflows/docker-build.yml` assumes a self-hosted runner with enough RAM to build the image (GitHub’s free runners frequently OOM).

1. Provision a GCE VM (e.g. `e2-standard-8`, 100 GB boot disk, Ubuntu 20.04).
2. Install dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install -y git docker.io
   sudo usermod -aG docker "$USER"
   sudo systemctl enable --now docker
   ```
3. Register the runner using the instructions from GitHub → Settings → Actions → Runners. Download the runner tarball, configure it, then launch with `./run.sh` or install as a service (`sudo ./svc.sh install && sudo ./svc.sh start`).

If you have access to larger enterprise-hosted runners with sufficient memory, you can update `runs-on` accordingly and skip the self-hosted setup.

### 5. Populate the Vivado/Vitis disk
1. Create a 500 GB persistent disk (or larger as needed):
   ```bash
   gcloud compute disks create vivado-vitis-2020-1 \
     --size=500GB \
     --type=pd-standard \
     --zone=us-central1-a
   ```
2. Attach the disk to a VM, mount it (e.g. at `/mnt/xilinx`), and install Vivado 2020.1 + Vitis 2020.1 into `/mnt/xilinx/Xilinx`.
3. Detach the disk from the VM; do **not** delete it. `release/vivado-pv-pvc.yaml` references this disk by name and mounts it read-only into every student pod.

Keep the disk in the same zone as your GKE nodes. If you change the disk name or namespace, update `vivado-pv-pvc.yaml`.

### 6. Verify workflow configuration
- Push to `main` (or trigger manually) to confirm the GitHub workflow builds and publishes to Artifact Registry.
- Check the Artifact Registry repository for `student-desktop:<commit-sha>` and `student-desktop:latest`.
- When rotating the service-account key, upload the fresh JSON as `GCP_SA_KEY`; the workflow pulls credentials on every run.
- Any branch push that hits the workflow will generate a new image tag for that commit and refresh the `latest` tag used by the lab deployment.

## Prerequisites
1. **Google Cloud project** with the GKE API enabled.
2. **Artifact Registry** repository containing the student image produced by the CartPole GitHub workflow.
3. **Preloaded Vivado/Vitis disk** (ext4) in the same zone as the GKE node pool; update `vivado-pv-pvc.yaml` with the disk name.
4. **Xilinx license server** set via `XILINXD_LICENSE_FILE`; this can be exported before running `deploy-lab.sh` or injected as a Kubernetes Secret.
5. `gcloud` and `kubectl` installed locally and authenticated against the target project.

## Deployment Workflow
1. **Create the cluster**
   ```bash
   ./release/create-cluster.sh <gcp-project> <cluster-name> <zone>
   ```
   The script enables the GKE API, provisions an `e2-standard-4` pool with autoscaling 0–10 nodes, and updates your kubeconfig.

2. **Bind the Vivado/Vitis disk**
   ```bash
   kubectl apply -f release/vivado-pv-pvc.yaml
   ```
   Adjust the namespace in the PVC (`metadata.namespace`) if you are deploying somewhere other than `lab-test`.

3. **Prepare the student roster**
   Copy `release/students-template.csv`, fill the `github` column, and optionally assign stable IDs:
   ```csv
   github,id
   student-handle,s01
   another-handle,s02
   ```

4. **Deploy the lab**
   ```bash
   ./release/deploy-lab.sh <namespace> <students.csv> <gcp-project>
   ```
   The script will:
   - Create the namespace if missing.
   - Generate a throwaway SSH key that the bastion uses to reach pods.
   - Deploy per-student `Deployment` + `Service` pairs with the shared Vivado PV mounted at `/mnt/xilinx`.
   - Stand up a bastion `Deployment` with a public `LoadBalancer` service.
   - Restrict pod ingress to the bastion via a NetworkPolicy.

5. **Hand out access instructions**
   - Students add their GitHub SSH keys; the script pulls keys from GitHub and injects them into the bastion.
   - To connect: `ssh -Y lab@<bastion-ip>` then `ssh -Y student@<student-id>-ssh.<namespace>.svc.cluster.local`.

6. **Operate and troubleshoot**
   - `release/operator-cheatsheet.md` documents the kubectl commands that were useful during testing (pod restarts, bastion inspection, X11 diagnostics).
   - `release/delete-lab.sh <namespace>` removes the namespace when the lab ends.
   - `release/delete-cluster.sh <gcp-project> <cluster-name> <zone>` tears down the GKE cluster.

## Headless Vitis Automation
`run_vitis_cartpole.sh` modernizes the Vitis automation for non-GUI environments:
- Launches `xsct` under Xvfb with Java 8 and GTK2 to avoid SWT crashes.
- Reads `generate_vitis_project.tcl` by default and surfaces logs from the workspace (`Firmware/VitisProjects`).
- Optionally installs runtime dependencies on Ubuntu 20.04 when `RUN_DEPS=1`.

This script is compatible with the student container image and the GKE pods created by `deploy-lab.sh`. Use it when a pod needs to regenerate BOOT.bin without an interactive desktop session.

## Known Considerations
- Ensure the PV disk and the node pool are in the same zone; otherwise the PVC never binds.
- The default node type (`e2-standard-4`) keeps resource costs low; increase for concurrent Vivado workloads.
- GitHub key retrieval happens at deploy time; students must keep a valid key uploaded to GitHub.
- GUI workloads rely on X11 forwarding through the bastion; test with `xclock` before starting Vivado.
