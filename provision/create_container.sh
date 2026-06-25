#!/usr/bin/env bash
# Provision the demo database + container on an Azure Cosmos DB for NoSQL account.
#
# Prerequisites:
#   * az login
#   * The target account must have the capabilities:
#       EnableNoSQLVectorSearch, EnableNoSQLFullTextSearch
#     (create one with, e.g.:
#       az cosmosdb create -n <account> -g <rg> --locations regionName=<region> \
#         --capabilities EnableServerless EnableNoSQLVectorSearch EnableNoSQLFullTextSearch )
#
# Usage:
#   COSMOS_ACCOUNT=<account> COSMOS_RG=<resource-group> ./provision/create_container.sh
#   # or pass as args:
#   ./provision/create_container.sh <account> <resource-group> [database] [container]
set -euo pipefail

ACC="${1:-${COSMOS_ACCOUNT:?Set COSMOS_ACCOUNT or pass account name as arg 1}}"
RG="${2:-${COSMOS_RG:?Set COSMOS_RG or pass resource group as arg 2}}"
DB="${3:-${COSMOS_DATABASE:-docusign_demo}}"
CONT="${4:-${COSMOS_CONTAINER:-agreements}}"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Provisioning ${DB}/${CONT} on account '${ACC}' (rg '${RG}')…"

az cosmosdb sql database create -a "$ACC" -g "$RG" -n "$DB" 1>/dev/null
echo "  database '$DB' ready"

az cosmosdb sql container create -a "$ACC" -g "$RG" -d "$DB" -n "$CONT" \
  --partition-key-path "/accountId" \
  --idx              @"$DIR/idx.json" \
  --vector-embeddings @"$DIR/vec.json" \
  --full-text-policy  @"$DIR/ft.json" 1>/dev/null
echo "  container '$CONT' ready (DiskANN vector index + full-text index/policy + composite index)"
echo "Done. Now run:  python build_index.py"
