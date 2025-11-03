# CartPole Lab Deployment Bundle

- `deploy-lab.sh` – orchestrates per-student workloads and the bastion; keep this script in the repo root or under `scripts/`.
- `create-cluster.sh` / `delete-cluster.sh` / `delete-lab.sh` – helper scripts for cluster lifecycle and namespace cleanup.
- `vivado-pv-pvc.yaml` – static GCE PersistentVolume and PVC manifest that mounts the preloaded Vivado/Vitis disk read-only.
- `students-template.csv` – roster template consumed by `deploy-lab.sh` (`github` column is required, `id` is optional).
- `operator-cheatsheet.md` – quick reference for PV maintenance, troubleshooting, and SSH/X11 jumping through the bastion.
- `cloud-lab.md` – full walkthrough (GCP bootstrap, GitHub workflow setup, Kubernetes deployment).


When publishing, strip any private key material and set the `XILINXD_LICENSE_FILE` value through environment or Secret, not hard-coded files.
