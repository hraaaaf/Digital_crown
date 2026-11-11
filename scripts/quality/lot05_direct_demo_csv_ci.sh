#!/usr/bin/env bash
# LOT05 Step2B — direct, synthetic demo MariaDB -> CSV via GitHub Actions.
# No Open Dental GUI, no patient records, no production network or credentials.
set -Eeuo pipefail
umask 077

: "${RUNNER_TEMP:?RUNNER_TEMP required}"
: "${LOT05_EXPECTED_SHA:?LOT05_EXPECTED_SHA required}"
: "${RUNNER_ENVIRONMENT:?RUNNER_ENVIRONMENT required}"
: "${RUNNER_OS:?RUNNER_OS required}"
if [[ "$RUNNER_ENVIRONMENT" != 'github-hosted' || "$RUNNER_OS" != 'Linux' ]]; then
  echo 'LOT05_HOSTED_LINUX_EXACT_SHA_REQUIRED' >&2
  exit 1
fi
if [[ "$(git rev-parse HEAD)" != "$LOT05_EXPECTED_SHA" ]]; then
  echo 'LOT05_CHECKOUT_SHA_MISMATCH' >&2
  exit 1
fi

command -v docker >/dev/null
command -v python3 >/dev/null
command -v openssl >/dev/null
image='mariadb:10.11'
container="lot05-demo-ci-${GITHUB_RUN_ID:-0}-${GITHUB_RUN_ATTEMPT:-1}"
result_dir="$RUNNER_TEMP/lot05-direct-demo-csv"
raw_dir="$RUNNER_TEMP/lot05-direct-internal"
mkdir -p "$result_dir" "$raw_dir"
chmod 700 "$result_dir" "$raw_dir"

# Secrets exist only for this disposable synthetic container, never in GitHub
# source, logs or artifacts. All SQL readback uses a SELECT-only account.
root_pw="$(openssl rand -hex 24)"
reader_pw="$(openssl rand -hex 24)"
cleanup() {
  docker rm -f "$container" >/dev/null 2>&1 || true
  rm -rf "$raw_dir"
}
trap cleanup EXIT

docker pull "$image" >/dev/null
image_digest="$(docker image inspect --format '{{index .RepoDigests 0}}' "$image")"
if [[ ! "$image_digest" =~ sha256:[0-9a-f]{64}$ ]]; then
  echo 'LOT05_MARIADB_DIGEST_UNAVAILABLE' >&2
  exit 1
fi
# No network device or published ports in the database container. CLI access
# takes place only through docker exec and MariaDB's local UNIX socket.
docker run --detach --name "$container" --network none \
  --env "MARIADB_ROOT_PASSWORD=$root_pw" "$image" >/dev/null
ready=0
for _ in $(seq 1 75); do
  if docker exec -e "MYSQL_PWD=$root_pw" "$container" \
      mariadb --user=root --connect-timeout=3 --batch --skip-column-names \
      --execute='SELECT 1;' >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
if [[ "$ready" -ne 1 ]]; then
  echo 'LOT05_SYNTHETIC_MARIADB_NOT_READY' >&2
  exit 1
fi

# Only disposable synthetic rows. No patient identifiers or media.
docker exec -i -e "MYSQL_PWD=$root_pw" "$container" \
  mariadb --user=root --batch --silent <<SQL
CREATE DATABASE demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE TABLE demo.lot05_synthetic_events (
  event_id INT NOT NULL PRIMARY KEY,
  procedure_group VARCHAR(20) NOT NULL
);
INSERT INTO demo.lot05_synthetic_events (event_id,procedure_group) VALUES
 (1,'PREVENTION'), (2,'PREVENTION'),
 (3,'RESTORATION'), (4,'RESTORATION'), (5,'RESTORATION'),
 (6,'IMAGING');
CREATE USER 'lot05_readonly'@'localhost' IDENTIFIED BY '$reader_pw';
GRANT SELECT ON demo.lot05_synthetic_events TO 'lot05_readonly'@'localhost';
SQL

# Read-only query from the synthetic schema, not an Open Dental native export.
# Raw SQL output stays in a private runner directory, never uploaded.
docker exec -e "MYSQL_PWD=$reader_pw" "$container" \
  mariadb --user=lot05_readonly --database=demo --batch --raw \
  --skip-column-names \
  --execute='SELECT DATABASE(), 1, COUNT(*) FROM lot05_synthetic_events;' \
  > "$raw_dir/query.tsv"

python3 - "$raw_dir/query.tsv" "$result_dir" "$image_digest" <<'PY'
import csv
import hashlib
import json
import os
import pathlib
import sys

raw_file, output, image_digest = sys.argv[1:]
out = pathlib.Path(output)
lines = pathlib.Path(raw_file).read_text(encoding="utf-8").splitlines()
# This exact response must originate in MariaDB. No hardcoded CSV fallback.
if lines != ["demo\t1\t6"]:
    raise SystemExit("LOT05_SQL_QUERY_RESULT_MISMATCH")

csv_path = out / "lot05_direct_demo.csv"
with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["connected_database", "proof", "synthetic_event_count"])
    writer.writerow(lines[0].split("\t"))

with csv_path.open("r", encoding="utf-8", newline="") as handle:
    parsed = csv.DictReader(handle)
    records = list(parsed)
    if parsed.fieldnames != ["connected_database", "proof", "synthetic_event_count"]:
        raise SystemExit("LOT05_CSV_SCHEMA_MISMATCH")
    if records != [{"connected_database": "demo", "proof": "1", "synthetic_event_count": "6"}]:
        raise SystemExit("LOT05_CSV_CONTENT_MISMATCH")
    if any("patient" in column.lower() for column in parsed.fieldnames):
        raise SystemExit("LOT05_CSV_PHI_COLUMN_FOUND")

sha256 = hashlib.sha256(csv_path.read_bytes()).hexdigest()
(out / "lot05_direct_demo.csv.sha256").write_text(
    f"{sha256}  lot05_direct_demo.csv\n", encoding="ascii"
)
evidence = {
    "lot": "LOT05_STEP2B_DIRECT_DEMO_CSV",
    "export_kind": "GITHUB_ACTIONS_SQL_READONLY_TO_CSV_NOT_OPENDENTAL_NATIVE",
    "github_sha": os.environ["LOT05_EXPECTED_SHA"],
    "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
    "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", ""),
    "db_service": "mariadb",
    "db_schema": "demo",
    "db_origin": "isolated_synthetic_CI_fixture_not_vendor_demo",
    "db_container_network": "none",
    "mariadb_image_digest": image_digest,
    "sql_role": "lot05_readonly",
    "sql_permissions": "SELECT_ON_DEMO_LOT05_SYNTHETIC_EVENTS_ONLY",
    "query": "SELECT DATABASE(), 1, COUNT(*) FROM lot05_synthetic_events",
    "synthetic_fixture_rows": 6,
    "csv_rows": 1,
    "csv_columns": ["connected_database", "proof", "synthetic_event_count"],
    "csv_sha256": sha256,
    "csv_parse_verified": True,
    "patient_data_accessed": False,
    "production_database_accessed": False,
    "open_dental_gui_used": False,
    "open_dental_native_export_claimed": False,
}
(out / "lot05_direct_demo_evidence.json").write_text(
    json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print("LOT05_DIRECT_CSV_READONLY=True")
print("LOT05_DIRECT_CSV_CONTENT_VERIFIED=True")
print("LOT05_DIRECT_CSV_SHA256=" + sha256)
print("LOT05_DIRECT_CSV_SYNTHETIC_FIXTURE_ROWS=6")
print("LOT05_DIRECT_CSV_NATIVE_OPENDENTAL=False")
PY
(
  cd "$result_dir"
  sha256sum --check --status lot05_direct_demo.csv.sha256
)
echo 'LOT05_DIRECT_CSV_HASH_VERIFIED=True'
