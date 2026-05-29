# HighCPUThrottling

## Severity
P2

## Symptoms
- Application response latency increases without obvious load spike
- Prometheus metric `container_cpu_cfs_throttled_seconds_total` rising
- CPU usage in `kubectl top pods` appears below the limit but throttling is occurring
- Requests timing out intermittently under normal traffic

## Root Causes
- CPU limit set too low — kernel CFS throttles the container within each 100ms window
- CPU request too low relative to limit — container gets poor scheduling priority
- Burstable QoS class with no guaranteed CPU — node-level contention
- Spike workloads (GC, connection pool warm-up) hitting limit during burst

## Diagnosis Steps
1. Check current CPU usage vs limits:
   ```
   kubectl top pods -n <namespace>
   kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].resources}'
   ```

2. Query throttling ratio in Prometheus:
   ```
   rate(container_cpu_cfs_throttled_seconds_total{pod="<pod-name>"}[5m])
   /
   rate(container_cpu_cfs_periods_total{pod="<pod-name>"}[5m])
   ```
   Throttling ratio above 25% is a problem.

3. Check QoS class assigned to the pod:
   ```
   kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.qosClass}'
   ```

4. Check node-level CPU pressure:
   ```
   kubectl describe node <node-name> | grep -A3 'Conditions:'
   ```

## Remediation Steps
1. Increase CPU limit — this immediately reduces throttling:
   ```
   kubectl set resources deployment <deployment-name> \
     -n <namespace> \
     --limits=cpu=1000m \
     --requests=cpu=500m
   ```

2. For bursty workloads — set request equal to limit to get Guaranteed QoS:
   ```
   kubectl set resources deployment <deployment-name> \
     -n <namespace> \
     --limits=cpu=500m \
     --requests=cpu=500m
   ```

3. If node is under pressure — cordon and drain to redistribute:
   ```
   kubectl cordon <node-name>
   kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
   ```

4. Trigger HPA scale-out if horizontal scaling is available:
   ```
   kubectl scale deployment <deployment-name> -n <namespace> --replicas=<current+2>
   ```

## Post-Mortem Checklist
- [ ] Throttling ratio confirmed below 10% after remediation
- [ ] CPU limits updated in Helm values and committed
- [ ] HPA configured with CPU utilization target — prevents manual intervention next time
- [ ] Alert threshold set: throttling ratio > 25% for 5 min triggers P2 page
- [ ] QoS class reviewed — critical services should be Guaranteed
