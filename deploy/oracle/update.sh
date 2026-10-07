#!/usr/bin/env bash
# Update the School Demo app on the Oracle VM: pull, migrate, build, restart.
# Run as root (sudo) or as the frappe user:   sudo bash update.sh --site demo.example.com
set -euo pipefail

SITE_NAME="${SITE_NAME:-}"
FRAPPE_USER="${FRAPPE_USER:-frappe}"
BENCH_DIR="${BENCH_DIR:-/home/${FRAPPE_USER}/frappe-bench}"
APP_BRANCH="${APP_BRANCH:-main}"
BACKUP_FIRST="${BACKUP_FIRST:-1}"

while [ $# -gt 0 ]; do
  case "$1" in
    --site) SITE_NAME="${2:?}"; shift 2 ;;
    --branch) APP_BRANCH="${2:?}"; shift 2 ;;
    --no-backup) BACKUP_FIRST=0; shift ;;
    -h|--help) echo "Usage: update.sh --site HOST [--branch main] [--no-backup]"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done
[ -n "$SITE_NAME" ] || { echo "SITE_NAME is required (--site)." >&2; exit 2; }
[ -d "$BENCH_DIR/apps/school_demo" ] || { echo "No app at $BENCH_DIR/apps/school_demo" >&2; exit 1; }

run() {
  if [ "$(id -un)" = "$FRAPPE_USER" ]; then "$@"; else sudo -H -u "$FRAPPE_USER" "$@"; fi
}
BENCH="/home/${FRAPPE_USER}/.bench-venv/bin/bench"
[ -x "$BENCH" ] || BENCH="$(command -v bench)"

cd "$BENCH_DIR"
if [ "$BACKUP_FIRST" = 1 ]; then
  echo "==> Backup"
  run "$BENCH" --site "$SITE_NAME" backup
fi
echo "==> Pull school_demo ($APP_BRANCH)"
run git -C "$BENCH_DIR/apps/school_demo" fetch origin "$APP_BRANCH"
run git -C "$BENCH_DIR/apps/school_demo" checkout "$APP_BRANCH"
run git -C "$BENCH_DIR/apps/school_demo" pull --ff-only origin "$APP_BRANCH"
echo "==> Python deps"
run "$BENCH_DIR/env/bin/pip" install -q -e "$BENCH_DIR/apps/school_demo"
echo "==> Migrate"
run "$BENCH" --site "$SITE_NAME" migrate
echo "==> Build assets"
run "$BENCH" build --app school_demo
echo "==> Restart"
if [ "$(id -u)" -eq 0 ]; then
  supervisorctl restart all
else
  sudo supervisorctl restart all
fi
echo "Done. Check: curl -s https://${SITE_NAME}/api/method/ping"
