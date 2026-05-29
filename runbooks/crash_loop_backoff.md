# CrashLoopBackOff

## Severity
P1

## Symptoms
- Pod status shows `CrashLoopBackOff` in `kubectl get pods`
- RESTARTS counter incrementing on a backoff schedule (10s to 20s to 40s to 5min cap)
- Container exits immediately after start — logs may be empty or show startup failure

## Root Causes
- Application startup failure — missing env var, bad config, failed DB connection
- Entrypoint or command is wrong in the container spec
- Liveness probe too aggressive — killing container before app is ready
- OOMKilled on startup — container never reaches ready state
- Dependency service unavailable at startup (DB, secrets manager, external API)

## Diagnosis Steps
1. Get the exit reason and last termination message:
   ```
   kubectl describe pod <pod-name> -n <namespace>
   ```
   Check `Last State`, `Exit Code`, and `Message` fields.

2. Read logs from the previous (crashed) container instance:
   ```
   kubectl logs <pod-name> -n <namespace> --previous
   ```

3. If logs are empty, exec into a running instance immediately after restart:
   ```
   kubectl exec -it <pod-name> -n <namespace> -- /bin/sh
   ```

4. Check if env vars are populated:
   ```
   kubectl exec <pod-name> -n <namespace> -- env | grep -E 'DB_|API_|SECRET_'
   ```

5. Inspect liveness and readiness probe config:
   ```
   kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].livenessProbe}'
   ```

## Remediation Steps
1. If missing env var or secret — patch the deployment with the correct value:
   ```
   kubectl set env deployment/<deployment-name> \
     -n <namespace> \
     MY_VAR=value
   ```

2. If liveness probe is killing the container too early — increase `initialDelaySeconds`:
   ```
   kubectl patch deployment <deployment-name> -n <namespace> \
     --type='json' \
     -p='[{"op":"replace","path":"/spec/template/spec/containers/0/livenessProbe/initialDelaySeconds","value":60}]'
   ```

3. If dependency is unavailable — confirm dependency health before restarting pod:
   ```
   kubectl get svc,endpoints -n <namespace>
   ```

4. Force a fresh rollout after fix:
   ```
   kubectl rollout restart deployment/<deployment-name> -n <namespace>
   ```

## Post-Mortem Checklist
- [ ] Root cause identified and documented (config / probe / dependency / OOM)
- [ ] Fix applied in Helm values or manifest — not just patched in cluster
- [ ] Startup probe added if liveness was the cause — use `startupProbe` for slow-starting apps
- [ ] Dependency health check added to readiness probe
- [ ] Alert added for `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"} > 0`
