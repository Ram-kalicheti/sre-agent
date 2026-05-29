# OOMKilled

## Severity
P1

## Symptoms
- Pod status shows `OOMKilled` in `kubectl get pods`
- Container restarts incrementally — check `RESTARTS` column
- Application logs cut off abruptly with no error — process terminated by kernel

## Root Causes
- Memory request set too low relative to actual usage
- Memory leak in application code — heap grows unbounded
- Sudden traffic spike exceeding steady-state memory footprint
- JVM or runtime not respecting container memory limits

## Diagnosis Steps
1. Confirm the kill reason:
   ```
   kubectl describe pod <pod-name> -n <namespace>
   ```
   Look for `OOMKilled` under `Last State` and `Reason`.

2. Check current memory usage across pods in the namespace:
   ```
   kubectl top pods -n <namespace>
   ```

3. Compare usage against configured limits:
   ```
   kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].resources}'
   ```

4. Pull recent memory metrics from Prometheus:
   ```
   container_memory_working_set_bytes{pod="<pod-name>"}
   ```

5. Check for restart pattern — frequent restarts indicate leak vs. spike:
   ```
   kubectl get pod <pod-name> -n <namespace> --watch
   ```

## Remediation Steps
1. Immediate — increase memory limit to stop restart loop:
   ```
   kubectl set resources deployment <deployment-name> \
     -n <namespace> \
     --limits=memory=512Mi \
     --requests=memory=256Mi
   ```

2. If leak suspected — roll back to last stable image:
   ```
   kubectl rollout undo deployment/<deployment-name> -n <namespace>
   ```

3. Verify rollout completes:
   ```
   kubectl rollout status deployment/<deployment-name> -n <namespace>
   ```

4. Set a VPA (Vertical Pod Autoscaler) recommendation policy if not already present.

## Post-Mortem Checklist
- [ ] Root cause confirmed: misconfigured limits vs. memory leak vs. traffic spike
- [ ] Memory limit updated in Helm values or deployment manifest and committed
- [ ] Prometheus alert threshold adjusted to fire at 80% of new limit
- [ ] Load test run to confirm new limits hold under peak traffic
- [ ] Ticket opened if leak suspected — heap profiling scheduled
