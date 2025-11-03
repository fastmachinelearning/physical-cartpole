# Lab Operations Cheat Sheet

Quick commands for maintaining the CartPole student lab on GKE. All commands assume you are authenticated with `gcloud` and `kubectl`, and that the namespace is stored in `NS` (e.g. `export NS=lab-test`).

## Persistent Volume
- `kubectl delete pv xilinx-pv`
- `kubectl delete pvc vivado-pvc -n $NS`
- `kubectl apply -f vivado-pv-pvc.yaml`
- `kubectl get pv xilinx-pv`
- `kubectl -n $NS get pvc vivado-pvc`

## Student Pods
- `kubectl -n $NS describe pod -l app=<student-id>-desktop | sed -n '1,200p'`
- `kubectl -n $NS get pods`
- `kubectl -n $NS rollout restart deploy/<student-id>-desktop`
- `kubectl -n $NS delete pod <student-pod-name> --grace-period=0 --force`
- `kubectl -n $NS logs deploy/<student-id>-desktop -c desktop --previous | tail -n 50`

## Bastion Pod
- `kubectl -n $NS get pods -l app=bastion -o wide`
- `kubectl -n $NS get svc bastion-ssh -o yaml | yq '.spec,.status'`
- `kubectl -n $NS get endpoints bastion-ssh -o wide`
- `kubectl -n $NS logs deploy/bastion --tail=200`

## SSH/X11 Usage
1. `ssh-keygen -R <bastion-external-ip>`
2. `ssh -Y lab@<bastion-external-ip>`
3. From the bastion, jump to a student pod:
   ```
   ssh -Y -J lab@<bastion-external-ip> \
     student@<student-id>-ssh.${NS}.svc.cluster.local \
     'echo DISPLAY=$DISPLAY; xauth list | head -1; xclock &'
   ```

## Troubleshooting X11
- `ssh -vvv -Y lab@<bastion-external-ip>`
- `ssh -Y lab@<bastion-external-ip> 'echo BASTION=$DISPLAY; /usr/bin/xauth info'`
- `ssh -Y lab@<bastion-external-ip> 'echo FIRST_HOP=$DISPLAY; which xauth; /usr/bin/xauth info'`
