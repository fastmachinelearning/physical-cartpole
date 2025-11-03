#!/usr/bin/env bash
set -euo pipefail

# Usage: ./deploy-lab.sh <namespace> <students.csv> <gcp-project>
# CSV headers: github,id   (id optional; will auto-s01,s02,... if omitted)

NS="${1:?Usage: ./deploy-lab.sh <namespace> <students.csv> <gcp-project>}"
CSV="${2:?students.csv required}"
PROJECT="${3:?gcp project id}"

IMAGE="us-central1-docker.pkg.dev/${PROJECT}/docker-repo/student-desktop:latest"
LIC="${XILINXD_LICENSE_FILE:-2100@licenseserver.example.com}"
BASTION_USER="lab"

echo "==> Namespace"
kubectl get ns "$NS" >/dev/null 2>&1 || kubectl create ns "$NS"

echo "==> Generate bastion→pod SSH keypair (throwaway for this lab)"
TMP_DIR="$(mktemp -d)"
ssh-keygen -t ed25519 -f "${TMP_DIR}/bastion_to_pod" -N '' -q

echo "==> Secrets: bastion outbound key"
kubectl -n "$NS" delete secret bastion-outbound-key >/dev/null 2>&1 || true
kubectl -n "$NS" create secret generic bastion-outbound-key \
  --from-file=id_ed25519="${TMP_DIR}/bastion_to_pod" \
  --from-file=id_ed25519.pub="${TMP_DIR}/bastion_to_pod.pub"

# Build bastion authorized_keys as we loop students
: > "${TMP_DIR}/bastion_authorized_keys"

echo "==> Deploy students"
i=1
tail -n +2 "$CSV" | while IFS=, read -r gh id || [[ -n "${gh:-}${id:-}" ]]; do
  gh="${gh//$'\r'/}"; id="${id//$'\r'/}"
  [[ -z "${gh:-}" ]] && continue
  [[ -z "${id:-}" ]] && id=$(printf "s%02d" "$i")
  echo " -> $gh -> ${id}"

  # (1) sshd_config (pods listen on 2222; service maps 22->2222)
  kubectl -n "$NS" apply -f - <<YAML
apiVersion: v1
kind: ConfigMap
metadata: { name: ${id}-sshd-cfg }
data:
  sshd_config: |
    Port 2222
    PasswordAuthentication no
    PermitRootLogin no
    PubkeyAuthentication yes
    AuthorizedKeysFile /home/student/.ssh/authorized_keys
    X11Forwarding yes
    X11UseLocalhost no
    XAuthLocation /usr/bin/xauth
    AddressFamily inet
    AllowTcpForwarding yes
    PermitTTY yes
    UsePAM no
    StrictModes yes
    Subsystem sftp internal-sftp
YAML

  # (2) authorized_keys secret (we'll copy it in initContainer)
  kubectl -n "$NS" delete secret "${id}-authorized" >/dev/null 2>&1 || true
  kubectl -n "$NS" create secret generic "${id}-authorized" \
    --from-file=authorized_keys="${TMP_DIR}/bastion_to_pod.pub"

  # (3) Deployment + Service
  kubectl -n "$NS" apply -f - <<YAML
apiVersion: apps/v1
kind: Deployment
metadata: { name: ${id}-desktop }
spec:
  replicas: 1
  selector: { matchLabels: { app: ${id}-desktop } }
  template:
    metadata: { labels: { app: ${id}-desktop } }
    spec:
      # --- Prepare ~/.ssh with correct ownership/perms from Secret ---
      initContainers:
      - name: setup-ssh
        image: ubuntu:22.04
        command: ["/bin/bash","-lc"]
        args:
          - |
            set -e
            mkdir -p /work
            cp /secret/authorized_keys /work/authorized_keys
            chmod 700 /work
            chmod 600 /work/authorized_keys
            chown 1000:1000 /work /work/authorized_keys  # student UID/GID
        volumeMounts:
        - name: student-ssh
          mountPath: /work
        - name: student-auth
          mountPath: /secret
          readOnly: true
        securityContext:
          runAsUser: 0

      containers:
      - name: desktop
        image: ${IMAGE}
        env:
        - name: XILINXD_LICENSE_FILE
          value: "${LIC}"
        ports:
        - containerPort: 2222
          name: ssh
        command: ["/bin/bash","-lc"]
        args:
          - |
            # Ensure account is unlocked even if image drifted
            usermod -U student && passwd -d student || true
            # Generate host keys if missing
            if [ ! -f /etc/ssh/ssh_host_ed25519_key ] || [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
              ssh-keygen -A
              chmod 600 /etc/ssh/ssh_host_*_key
              chmod 644 /etc/ssh/ssh_host_*_key.pub
            fi
            # Conservative perms for home and .ssh
            chmod 700 /home/student || true
            chmod 700 /home/student/.ssh || true
            chmod 600 /home/student/.ssh/authorized_keys || true
            chown -R student:student /home/student/.ssh || true
            # Start sshd using the mounted config
            exec /usr/sbin/sshd -D -e
        volumeMounts:
        - name: vivado
          mountPath: /mnt/xilinx
          readOnly: true
        - name: sshd-cfg
          mountPath: /etc/ssh/sshd_config
          subPath: sshd_config
          readOnly: true
        - name: student-ssh
          mountPath: /home/student/.ssh
          readOnly: false
        readinessProbe:
          tcpSocket: { port: 2222 }
          initialDelaySeconds: 3
          periodSeconds: 3
        livenessProbe:
          tcpSocket: { port: 2222 }
          initialDelaySeconds: 10
          periodSeconds: 10

      volumes:
      - name: vivado
        persistentVolumeClaim: { claimName: vivado-pvc }
      - name: sshd-cfg
        configMap: { name: ${id}-sshd-cfg }
      - name: student-auth
        secret: { secretName: ${id}-authorized, defaultMode: 0400 }
      - name: student-ssh
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata: { name: ${id}-ssh }
spec:
  selector: { app: ${id}-desktop }
  ports:
  - name: ssh
    port: 22          # external/bastion connects to 22
    targetPort: 2222  # pod listens on 2222
YAML

  # (4) Bastion authorized_keys entry for this student (uses their GitHub key)
  KEYS="$(curl -fsSL "https://github.com/${gh}.keys" || true)"
  if [[ -z "$KEYS" ]]; then
    echo "    WARN: No GitHub keys found for ${gh}" | tee -a "${TMP_DIR}/missing-keys.log"
  else
    while read -r key; do
      [[ -z "$key" ]] && continue
      cat >> "${TMP_DIR}/bastion_authorized_keys" <<EOF
command="/bin/sh -lc 'export DISPLAY=\$DISPLAY; export XAUTHORITY=/home/${BASTION_USER}/.Xauthority; \
exec ssh -Y -tt -i /home/${BASTION_USER}/.ssh/id_ed25519 \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  -o XAuthLocation=/usr/bin/xauth \
  student@${id}-ssh.${NS}.svc.cluster.local'" ${key}
EOF
    done <<< "$KEYS"
  fi

  ((i++))
done

# (5) Bastion authorized_keys Secret
echo "==> Bastion authorized_keys Secret"
kubectl -n "$NS" delete secret bastion-ssh >/dev/null 2>&1 || true
kubectl -n "$NS" create secret generic bastion-ssh \
  --from-file=authorized_keys="${TMP_DIR}/bastion_authorized_keys"

# (6) Bastion Deployment and Service
echo "==> Bastion"
kubectl -n "$NS" apply -f - <<YAML
apiVersion: apps/v1
kind: Deployment
metadata: { name: bastion }
spec:
  replicas: 1
  selector: { matchLabels: { app: bastion } }
  template:
    metadata: { labels: { app: bastion } }
    spec:
      containers:
      - name: bastion
        image: ubuntu:22.04
        env:
        - { name: BASTION_USER, value: "${BASTION_USER}" }
        - { name: DEBIAN_FRONTEND, value: "noninteractive" }
        ports:
        - { containerPort: 2222, name: ssh }
        volumeMounts:
        - { name: ssh-keys,  mountPath: /secrets/authorized_keys, subPath: authorized_keys, readOnly: true }
        - { name: bastion-key, mountPath: /secrets/id_ed25519,     subPath: id_ed25519,     readOnly: true }
        command: ["/bin/sh","-c"]
        args:
          - |
            set -e
            # Retry to survive transient apt mirror issues (or prebuild a bastion image)
            n=0; until [ \$n -ge 5 ]; do
              (apt-get update && apt-get install -y --no-install-recommends openssh-server xauth ca-certificates) && break
              n=\$((n+1)); echo "apt retry \$n"; sleep 3
            done

            useradd -m -s /bin/bash "${BASTION_USER}" || true
            mkdir -p "/home/${BASTION_USER}/.ssh" /var/run/sshd

            cp /secrets/authorized_keys "/home/${BASTION_USER}/.ssh/authorized_keys"
            cp /secrets/id_ed25519 "/home/${BASTION_USER}/.ssh/id_ed25519"

            chown -R "${BASTION_USER}:${BASTION_USER}" "/home/${BASTION_USER}/.ssh"
            chmod 700 "/home/${BASTION_USER}/.ssh"
            chmod 600 "/home/${BASTION_USER}/.ssh/authorized_keys"
            chmod 400 "/home/${BASTION_USER}/.ssh/id_ed25519"

            touch "/home/${BASTION_USER}/.Xauthority"
            chown "${BASTION_USER}:${BASTION_USER}" "/home/${BASTION_USER}/.Xauthority"
            chmod 600 "/home/${BASTION_USER}/.Xauthority"

            {
              echo '# LAB OVERRIDES';
              echo 'Port 2222';
              echo 'PasswordAuthentication no';
              echo 'PermitRootLogin no';
              echo 'X11Forwarding yes';
              echo 'X11UseLocalhost no';
              echo 'XAuthLocation /usr/bin/xauth';
              echo 'AddressFamily inet';
              echo 'AllowTcpForwarding yes';
              echo 'PermitTTY yes';
              echo 'UsePAM no';
            } >> /etc/ssh/sshd_config

            ssh-keygen -A
            exec /usr/sbin/sshd -D -e
        readinessProbe:
          tcpSocket: { port: 2222 }
          initialDelaySeconds: 2
          periodSeconds: 2
        livenessProbe:
          tcpSocket: { port: 2222 }
          initialDelaySeconds: 10
          periodSeconds: 10
      volumes:
      - name: ssh-keys
        secret: { secretName: bastion-ssh, defaultMode: 0600 }
      - name: bastion-key
        secret: { secretName: bastion-outbound-key, defaultMode: 0600 }
---
apiVersion: v1
kind: Service
metadata: { name: bastion-ssh }
spec:
  type: LoadBalancer
  selector: { app: bastion }
  ports:
  - name: ssh
    port: 22
    targetPort: 2222
YAML

# (7) NetworkPolicy (allow bastion -> students on 2222 only)
echo "==> NetworkPolicy"
kubectl -n "$NS" apply -f - <<'YAML'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: student-isolation }
spec:
  podSelector:
    matchExpressions:
      - key: app
        operator: NotIn
        values: ["bastion"]
  policyTypes: ["Ingress"]
  ingress:
  - from:
    - podSelector: { matchLabels: { app: bastion } }
    ports:
    - { protocol: TCP, port: 2222 }
YAML

echo "==> Bastion external IP (watching...)"
kubectl -n "$NS" get svc bastion-ssh -w
