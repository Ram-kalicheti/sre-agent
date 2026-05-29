# NodeNotReady

## Severity
P1

## Symptoms
- `kubectl get nodes` shows a node in `NotReady` status
- Pods on the affected node begin evicting after `pod-eviction-timeout` (default 5 min)
- Node conditions show `MemoryPressure`, `DiskPressure`, or `NetworkUnavailable` as True
- New pods scheduled to the node are stuck in Pending or Terminating

## Root Causes
- kubelet process crashed or stopped on the node
- Node ran out of disk space — kubelet cannot write logs or pull images
- Node memory pressure — system OOM killer targeted kubelet or critical process
- Network partition — node cannot reach API server
- EC2 instance health check failure (AWS) — underlying hardware issue

## Diagnosis Steps
1. Check node conditions:
   ```
   kubectl describe node <node-name>
   ```
   Focus on `Conditions` section — `Ready`, `MemoryPressure`, `DiskPressure`, `PIDPressure`.

2. Check how long the node has been NotReady:
   ```
   kubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type=="Ready")].lastTransitionTime}'
   ```

3. SSH to the node if accessible and check kubelet:
   ```
   systemctl status kubelet
   journalctl -u kubelet -n 100 --no-pager
   ```

4. Check disk usage on the node:
   ```
   df -h
   du -sh /var/lib/docker/* | sort -rh | head -10
   ```

5. For AWS — check EC2 instance status:
   ```
   aws ec2 describe-instance-status \
     --instance-ids <instance-id> \
     --region us-east-1
   ```

## Remediation Steps
1. If kubelet is stopped — restart it:
   ```
   systemctl restart kubelet
   ```
   Then watch node recover:
   ```
   kubectl get nodes --watch
   ```

2. If disk pressure — clean up dangling images and containers:
   ```
   docker system prune -f
   crictl rmi --prune
   ```

3. If node is unrecoverable — cordon, drain, and terminate (AWS):
   ```
   kubectl cordon <node-name>
   kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data --force
   aws ec2 terminate-instances --instance-ids <instance-id>
   ```

4. Verify pod rescheduling on healthy nodes:
   ```
   kubectl get pods -n <namespace> -o wide
   ```

## Post-Mortem Checklist
- [ ] Node failure cause confirmed (kubelet / disk / memory / network / hardware)
- [ ] Node replaced and cluster back to full capacity
- [ ] Disk eviction thresholds reviewed in kubelet config — default is 10% free
- [ ] CloudWatch EC2 health check alarm verified — should fire before NodeNotReady
- [ ] Node group min size reviewed — single-AZ deployments are vulnerable to AZ failure
