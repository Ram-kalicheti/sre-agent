# PodPending

## Severity
P2

## Symptoms
- Pod stuck in `Pending` state in `kubectl get pods`
- No node assignment shown in the `NODE` column
- Pod has been pending longer than 2 minutes — scheduler cannot place it

## Root Causes
- Insufficient cluster resources — CPU or memory requested exceeds available capacity
- Node selector or affinity rules have no matching nodes
- Taint on all nodes with no matching toleration on the pod
- PersistentVolumeClaim not bound — storage class unavailable or quota exceeded
- Resource quota in the namespace is exhausted

## Diagnosis Steps
1. Get scheduling failure reason:
   ```
   kubectl describe pod <pod-name> -n <namespace>
   ```
   Read the `Events` section at the bottom — scheduler emits the exact reason.

2. Check node capacity and allocatable resources:
   ```
   kubectl describe nodes | grep -A5 'Allocatable:'
   kubectl top nodes
   ```

3. Check namespace resource quota:
   ```
   kubectl describe resourcequota -n <namespace>
   ```

4. Check PVC status if pod mounts a volume:
   ```
   kubectl get pvc -n <namespace>
   kubectl describe pvc <pvc-name> -n <namespace>
   ```

5. List node taints and compare with pod tolerations:
   ```
   kubectl get nodes -o json | jq '.items[].spec.taints'
   kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.tolerations}'
   ```

## Remediation Steps
1. If resource exhaustion — scale up the node group (AWS):
   ```
   aws autoscaling set-desired-capacity \
     --auto-scaling-group-name <asg-name> \
     --desired-capacity <current+1>
   ```

2. If node selector mismatch — patch pod spec or label the target node:
   ```
   kubectl label node <node-name> environment=production
   ```

3. If PVC not bound — check StorageClass exists and has available provisioner:
   ```
   kubectl get storageclass
   kubectl describe storageclass <class-name>
   ```

4. If quota exhausted — either increase quota or remove unused resources:
   ```
   kubectl delete pod <completed-pod> -n <namespace>
   kubectl edit resourcequota <quota-name> -n <namespace>
   ```

## Post-Mortem Checklist
- [ ] Root cause confirmed (resources / affinity / taint / PVC / quota)
- [ ] Cluster Autoscaler or Karpenter configured and verified for future spikes
- [ ] Resource requests and limits reviewed — over-requesting is a common cause
- [ ] PVC retention policy reviewed — avoid orphaned volumes consuming quota
- [ ] Alert on `kube_pod_status_phase{phase="Pending"} > 0` for longer than 3 min
