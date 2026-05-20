#!/usr/bin/env bash
# Register every agent service in docker-compose with restate-server.
# Idempotent: each underlying call uses `force: true`.

set -uo pipefail   # not -e: we want to keep going on per-deployment failures

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

DEPLOYMENTS=(
  "http://echo_agent:9080"
  "http://tour_chat:9081"
  "http://tour_error_handling:9082"
  "http://tour_human_approval:9083"
  "http://tour_human_approval_timeout:9084"
  "http://tour_multi_agent:9085"
  "http://tour_parallel_tools:9086"
  "http://tour_remote_agents:9087"
  "http://tour_sub_workflow:9088"
  "http://tour_workflow_evaluator_optimizer:9089"
  "http://tour_workflow_orchestrator:9090"
  "http://tour_workflow_parallel:9091"
  "http://tour_workflow_sequential:9092"
  "http://solar_au:9093"
  "http://solar_us:9094"
  "http://web_extract:9095"
  "http://page_fetcher:9098"
  "http://page_extractor:9099"
  "http://form_submitter:9100"
  "http://banking77:9096"
)

failed=0
for uri in "${DEPLOYMENTS[@]}"; do
  printf "→ %-60s " "${uri}"
  out=$(DEPLOYMENT_URI="${uri}" ./scripts/register.sh 2>&1)
  if echo "${out}" | grep -q "^OK:"; then
    echo "OK"
  else
    echo "FAIL"
    echo "${out}" | sed 's/^/    /'
    failed=$((failed + 1))
  fi
done

echo "==="
if [ "${failed}" -gt 0 ]; then
  echo "FAIL: ${failed} of ${#DEPLOYMENTS[@]} deployments failed"
  exit 1
fi
echo "PASS: ${#DEPLOYMENTS[@]} deployments registered"
