#!/usr/bin/env bash
# School Demo: one-shot production setup for a fresh Ubuntu 22.04/24.04 (aarch64 or x86_64) VM,
# written for the Oracle Cloud Always Free VM.Standard.A1.Flex shape.
#
# Run as root on the VM:
#   sudo SITE_NAME=demo.example.com ADMIN_PASSWORD='long-secret' LETSENCRYPT_EMAIL=you@example.com \
#        bash setup.sh
# or with flags:
#   sudo bash setup.sh --site demo.example.com --admin-password 'long-secret' --email you@example.com
#
# Idempotent: every stage checks whether it is already done, so you can safely re-run after a failure.
# Full log: /var/log/school_demo_setup.log.   Guide: deploy/oracle/ORACLE_CLOUD.md
set -euo pipefail

# ----------------------------------------------------------------------------------------------
# Settings (environment variables or flags)
# ----------------------------------------------------------------------------------------------
SITE_NAME="${SITE_NAME:-}"                       # required: the public hostname, e.g. demo.example.com
ADMIN_PASSWORD="${ADMIN_PASSWORD:-}"             # Administrator password; generated and printed once if empty
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-}"         # MariaDB root password; generated if empty
APP_REPO="${APP_REPO:-https://github.com/almariebu/school_demo}"
APP_BRANCH="${APP_BRANCH:-main}"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-15}"
LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL:-}"       # optional: set to get an HTTPS certificate at the end
GITHUB_TOKEN="${GITHUB_TOKEN:-}"                 # optional: fine-grained read-only token for a private HTTPS repo
SWAP_GB="${SWAP_GB:-4}"                          # swap file size, 0 to skip
NODE_MAJOR="${NODE_MAJOR:-20}"                   # Node 18 or 20 are fine for Frappe v15
FRAPPE_USER="${FRAPPE_USER:-frappe}"
BENCH_NAME="${BENCH_NAME:-frappe-bench}"
FORCE_CERTBOT="${FORCE_CERTBOT:-0}"              # 1 = request the certificate even if DNS does not match this VM

LOG_FILE=/var/log/school_demo_setup.log
SECRETS_FILE=/root/.school_demo_secrets          # root-only: DB root and Administrator passwords

usage() {
  cat <<EOF
Usage: sudo bash setup.sh --site HOST [--admin-password PW] [--email EMAIL] [--repo URL] [--branch B]
                          [--frappe-branch B] [--swap-gb N]
Environment variables with the same meaning (SITE_NAME, ADMIN_PASSWORD, LETSENCRYPT_EMAIL, APP_REPO,
APP_BRANCH, FRAPPE_BRANCH, DB_ROOT_PASSWORD, GITHUB_TOKEN, SWAP_GB, NODE_MAJOR) also work.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --site) SITE_NAME="${2:?}"; shift 2 ;;
    --admin-password) ADMIN_PASSWORD="${2:?}"; shift 2 ;;
    --db-root-password) DB_ROOT_PASSWORD="${2:?}"; shift 2 ;;
    --email) LETSENCRYPT_EMAIL="${2:?}"; shift 2 ;;
    --repo) APP_REPO="${2:?}"; shift 2 ;;
    --branch) APP_BRANCH="${2:?}"; shift 2 ;;
    --frappe-branch) FRAPPE_BRANCH="${2:?}"; shift 2 ;;
    --swap-gb) SWAP_GB="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

# ----------------------------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------------------------
log()  { printf '\n[%s] === %s\n' "$(date '+%F %T')" "$*"; }
info() { printf '    %s\n' "$*"; }
warn() { printf '    WARNING: %s\n' "$*" >&2; }
die()  { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Run as root: sudo bash $0 ..."
[ -n "$SITE_NAME" ] || { usage >&2; die "SITE_NAME is required (--site). It must equal the public hostname."; }
case "$SITE_NAME" in
  *[!a-zA-Z0-9.-]*|.*|*.|"") die "SITE_NAME '$SITE_NAME' is not a valid hostname." ;;
esac

mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"; chmod 600 "$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1
log "School Demo setup started for ${SITE_NAME} (log: ${LOG_FILE})"

export DEBIAN_FRONTEND=noninteractive
FRAPPE_HOME="/home/${FRAPPE_USER}"
BENCH_DIR="${FRAPPE_HOME}/${BENCH_NAME}"
BENCH_VENV="${FRAPPE_HOME}/.bench-venv"
BENCH_BIN="${BENCH_VENV}/bin/bench"
GENERATED_ADMIN=0

gen_secret() { head -c 64 /dev/urandom | tr -dc 'A-Za-z0-9' | head -c 24; }

# Run a command as the frappe user with a clean login-like environment.
as_frappe() { sudo -H -u "$FRAPPE_USER" env "PATH=${BENCH_VENV}/bin:/usr/local/bin:/usr/bin:/bin" "$@"; }
# Run a bench command inside the bench directory as the frappe user.
bench_cmd() { (cd "$BENCH_DIR" && as_frappe "$BENCH_BIN" "$@"); }

# ----------------------------------------------------------------------------------------------
# Stage 0: secrets (stored root-only so re-runs keep the same passwords)
# ----------------------------------------------------------------------------------------------
log "Stage 0: secrets"
if [ -f "$SECRETS_FILE" ]; then
  info "Reading existing $SECRETS_FILE"
  # shellcheck disable=SC1090
  . "$SECRETS_FILE"
  [ -n "$DB_ROOT_PASSWORD" ] || DB_ROOT_PASSWORD="${SAVED_DB_ROOT_PASSWORD:-}"
  [ -n "$ADMIN_PASSWORD" ] || ADMIN_PASSWORD="${SAVED_ADMIN_PASSWORD:-}"
fi
[ -n "$DB_ROOT_PASSWORD" ] || DB_ROOT_PASSWORD="$(gen_secret)"
if [ -z "$ADMIN_PASSWORD" ]; then
  ADMIN_PASSWORD="$(gen_secret)"
  GENERATED_ADMIN=1
fi
umask 077
{
  printf 'SAVED_DB_ROOT_PASSWORD=%q\n' "$DB_ROOT_PASSWORD"
  printf 'SAVED_ADMIN_PASSWORD=%q\n' "$ADMIN_PASSWORD"
} > "$SECRETS_FILE"
chmod 600 "$SECRETS_FILE"
umask 022

# ----------------------------------------------------------------------------------------------
# Stage 1: apt packages
# ----------------------------------------------------------------------------------------------
log "Stage 1: system packages"
apt-get update -y
apt-get upgrade -y
apt-get install -y \
  git curl wget ca-certificates gnupg sudo cron xz-utils openssl \
  build-essential pkg-config python3 python3-dev python3-venv python3-pip python3-setuptools \
  libffi-dev libssl-dev libmariadb-dev libjpeg-dev zlib1g-dev libxml2-dev libxslt1-dev \
  libcups2-dev fontconfig libxrender1 libxext6 xfonts-75dpi xfonts-base \
  mariadb-server mariadb-client redis-server nginx supervisor \
  iptables iptables-persistent netfilter-persistent \
  fail2ban unattended-upgrades certbot

PY_OK="$(python3 -c 'import sys; print(1 if (3,10) <= sys.version_info[:2] <= (3,12) else 0)')"
[ "$PY_OK" = 1 ] || die "python3 is $(python3 -V 2>&1); Frappe v15 needs Python 3.10 to 3.12 (Ubuntu 22.04 or 24.04)."
info "Python: $(python3 -V)"

# bench starts its own redis on ports 11000/13000 under supervisor; the system one only wastes RAM.
systemctl disable --now redis-server >/dev/null 2>&1 || true

# ----------------------------------------------------------------------------------------------
# Stage 2: swap file
# ----------------------------------------------------------------------------------------------
log "Stage 2: swap (${SWAP_GB} GB)"
if [ "$SWAP_GB" -gt 0 ] 2>/dev/null; then
  if swapon --show=NAME --noheadings | grep -q .; then
    info "Swap already active, skipping."
  else
    if [ ! -f /swapfile ]; then
      fallocate -l "${SWAP_GB}G" /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=$((SWAP_GB * 1024))
      chmod 600 /swapfile
      mkswap /swapfile
    fi
    swapon /swapfile
    grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  fi
  echo 'vm.swappiness=10' > /etc/sysctl.d/99-school-demo-swap.conf
  sysctl -q -p /etc/sysctl.d/99-school-demo-swap.conf || true
else
  info "SWAP_GB=0, skipped."
fi

# ----------------------------------------------------------------------------------------------
# Stage 3: MariaDB (utf8mb4 as Frappe requires) and root password
# ----------------------------------------------------------------------------------------------
log "Stage 3: MariaDB"
MARIA_CNF=/etc/mysql/mariadb.conf.d/99-frappe.cnf
NEW_CNF="$(mktemp)"
cat > "$NEW_CNF" <<'EOF'
[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
innodb_buffer_pool_size = 512M
max_connections = 100

[mysql]
default-character-set = utf8mb4
EOF
if ! cmp -s "$NEW_CNF" "$MARIA_CNF" 2>/dev/null; then
  install -m 644 "$NEW_CNF" "$MARIA_CNF"
  info "Wrote $MARIA_CNF"
  systemctl enable mariadb
  systemctl restart mariadb
else
  systemctl enable --now mariadb
  info "$MARIA_CNF already up to date."
fi
rm -f "$NEW_CNF"

# Passwordless root over the unix socket works on a fresh install; afterwards the saved password does.
if mysql -uroot -e 'SELECT 1' >/dev/null 2>&1; then
  mysql -uroot <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED VIA mysql_native_password USING PASSWORD('${DB_ROOT_PASSWORD}');
FLUSH PRIVILEGES;
EOF
  info "MariaDB root password set."
elif MYSQL_PWD="$DB_ROOT_PASSWORD" mysql -uroot -e 'SELECT 1' >/dev/null 2>&1; then
  info "MariaDB root password already set and matches."
else
  die "Cannot log in to MariaDB as root with the saved password. Pass --db-root-password with the real one."
fi

# ----------------------------------------------------------------------------------------------
# Stage 4: Node.js + yarn + wkhtmltopdf
# ----------------------------------------------------------------------------------------------
log "Stage 4: Node.js ${NODE_MAJOR}, yarn"
NODE_CURRENT="$(node -v 2>/dev/null | sed 's/^v//; s/\..*//' || true)"
if [ "$NODE_CURRENT" = "18" ] || [ "$NODE_CURRENT" = "20" ] || [ "$NODE_CURRENT" = "22" ]; then
  info "Node v${NODE_CURRENT} already installed."
else
  curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash -
  apt-get install -y nodejs
fi
command -v yarn >/dev/null 2>&1 || npm install -g yarn
info "node $(node -v), yarn $(yarn -v)"

log "Stage 4b: wkhtmltopdf (PDF printing; failure is not fatal)"
if wkhtmltopdf --version 2>/dev/null | grep -qi 'with patched qt'; then
  info "Patched wkhtmltopdf already installed."
else
  (
    set +e
    # shellcheck disable=SC1091
    . /etc/os-release
    ARCH="$(dpkg --print-architecture)"
    CODENAME="${VERSION_CODENAME:-jammy}"
    # The upstream packaging project ships patched-qt .debs per distro; there is no noble build, jammy works.
    case "$CODENAME" in jammy|focal|bookworm|bullseye) ;; *) CODENAME=jammy ;; esac
    DEB="wkhtmltox_0.12.6.1-3.${CODENAME}_${ARCH}.deb"
    URL="https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/${DEB}"
    TMP="$(mktemp -d)"
    if curl -fsSL -o "${TMP}/${DEB}" "$URL" && apt-get install -y "${TMP}/${DEB}"; then
      echo "    Installed patched wkhtmltopdf from ${URL}"
    else
      echo "    Patched build unavailable, falling back to the distro wkhtmltopdf." >&2
      apt-get install -y wkhtmltopdf || echo "    WARNING: wkhtmltopdf not installed; PDF print will not work." >&2
    fi
    rm -rf "$TMP"
  ) || warn "wkhtmltopdf step failed; continuing."
fi

# ----------------------------------------------------------------------------------------------
# Stage 5: frappe user and bench CLI
# ----------------------------------------------------------------------------------------------
log "Stage 5: user '${FRAPPE_USER}' and frappe-bench"
if ! id "$FRAPPE_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$FRAPPE_USER"
  info "Created user $FRAPPE_USER"
fi
usermod -aG sudo "$FRAPPE_USER"
echo "${FRAPPE_USER} ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/90-${FRAPPE_USER}"
chmod 440 "/etc/sudoers.d/90-${FRAPPE_USER}"
chmod 755 "$FRAPPE_HOME"          # nginx must be able to traverse it to serve /assets

if [ ! -x "$BENCH_BIN" ]; then
  sudo -H -u "$FRAPPE_USER" python3 -m venv "$BENCH_VENV"
  sudo -H -u "$FRAPPE_USER" "${BENCH_VENV}/bin/pip" install --upgrade pip setuptools wheel
  sudo -H -u "$FRAPPE_USER" "${BENCH_VENV}/bin/pip" install frappe-bench
else
  info "frappe-bench CLI already installed."
fi
ln -sf "$BENCH_BIN" /usr/local/bin/bench

# ----------------------------------------------------------------------------------------------
# Stage 6: bench init (downloads Frappe, builds assets; slowest step, 10 to 25 minutes on A1)
# ----------------------------------------------------------------------------------------------
log "Stage 6: bench init (${FRAPPE_BRANCH})"
if [ -d "${BENCH_DIR}/apps/frappe" ] && [ -x "${BENCH_DIR}/env/bin/python" ]; then
  info "Bench already initialised at $BENCH_DIR"
else
  rm -rf "$BENCH_DIR"   # drop a half-finished attempt
  (cd "$FRAPPE_HOME" && as_frappe "$BENCH_BIN" init --frappe-branch "$FRAPPE_BRANCH" --python python3 "$BENCH_NAME")
fi

# ----------------------------------------------------------------------------------------------
# Stage 7: get-app school_demo (public repo, HTTPS token, or SSH deploy key)
# ----------------------------------------------------------------------------------------------
log "Stage 7: get-app school_demo (${APP_REPO}, ${APP_BRANCH})"
if [ -d "${BENCH_DIR}/apps/school_demo" ]; then
  info "App already fetched."
else
  FETCH_URL="$APP_REPO"
  if [ -n "$GITHUB_TOKEN" ] && [[ "$APP_REPO" == https://github.com/* ]]; then
    FETCH_URL="https://x-access-token:${GITHUB_TOKEN}@${APP_REPO#https://}"
    info "Using GITHUB_TOKEN for the clone (the token is stored in apps/school_demo/.git/config; use a read-only token)."
  fi
  if [[ "$APP_REPO" == git@* || "$APP_REPO" == ssh://* ]]; then
    SSH_DIR="${FRAPPE_HOME}/.ssh"
    sudo -H -u "$FRAPPE_USER" mkdir -p "$SSH_DIR"
    chmod 700 "$SSH_DIR"
    if [ ! -f "${SSH_DIR}/id_ed25519" ]; then
      sudo -H -u "$FRAPPE_USER" ssh-keygen -t ed25519 -N '' -C "school-demo-deploy@${SITE_NAME}" -f "${SSH_DIR}/id_ed25519"
    fi
    sudo -H -u "$FRAPPE_USER" bash -c "ssh-keyscan -t ed25519,rsa github.com >> '${SSH_DIR}/known_hosts' 2>/dev/null; sort -u '${SSH_DIR}/known_hosts' -o '${SSH_DIR}/known_hosts'"
    if ! sudo -H -u "$FRAPPE_USER" ssh -o BatchMode=yes -T git@github.com 2>&1 | grep -qi 'successfully authenticated'; then
      echo
      echo "The repository is private. Add this public key as a read-only DEPLOY KEY at"
      echo "  https://github.com/<owner>/school_demo/settings/keys  (Add deploy key, leave 'write access' off)"
      echo
      cat "${SSH_DIR}/id_ed25519.pub"
      echo
      die "Add the deploy key, then re-run this script (finished stages are skipped)."
    fi
  fi
  bench_cmd get-app --branch "$APP_BRANCH" school_demo "$FETCH_URL"
  if [ "$FETCH_URL" != "$APP_REPO" ]; then
    info "The token stays in the app's git remote so update.sh can pull; revoke it if you make the repo public."
  fi
fi

# ----------------------------------------------------------------------------------------------
# Stage 8: site, app install, demo config
# ----------------------------------------------------------------------------------------------
log "Stage 8: site ${SITE_NAME}"
if [ -d "${BENCH_DIR}/sites/${SITE_NAME}" ]; then
  info "Site already exists."
else
  bench_cmd new-site "$SITE_NAME" --mariadb-root-password "$DB_ROOT_PASSWORD" --admin-password "$ADMIN_PASSWORD"
fi

# Seed flag first so after_install loads the demo data and the daily reset job is active.
bench_cmd --site "$SITE_NAME" set-config school_demo_seed 1 --parse
if bench_cmd --site "$SITE_NAME" list-apps | grep -q '^school_demo'; then
  info "school_demo already installed on the site."
else
  bench_cmd --site "$SITE_NAME" install-app school_demo
fi
# Idempotent; also guarantees the data is present if the install-time seed was skipped.
bench_cmd --site "$SITE_NAME" execute school_demo.setup.demo_data.seed

log "Stage 8b: scheduler and demo hardening"
bench_cmd --site "$SITE_NAME" scheduler enable
bench_cmd --site "$SITE_NAME" set-config mute_emails 1 --parse
bench_cmd --site "$SITE_NAME" set-config developer_mode 0 --parse
bench_cmd --site "$SITE_NAME" set-config allow_tests 0 --parse
bench_cmd --site "$SITE_NAME" set-config host_name "http://${SITE_NAME}"
bench_cmd --site "$SITE_NAME" execute frappe.db.set_single_value --args "['Website Settings','disable_signup',1]" \
  || warn "could not disable website signup; do it in Website Settings."
bench_cmd --site "$SITE_NAME" execute frappe.db.set_single_value --args "['System Settings','allow_consecutive_login_attempts',5]" \
  || warn "could not set login attempt limit."
bench_cmd --site "$SITE_NAME" execute frappe.db.set_single_value --args "['System Settings','allow_login_after_fail',120]" \
  || warn "could not set login lockout seconds."
bench_cmd use "$SITE_NAME"

# ----------------------------------------------------------------------------------------------
# Stage 9: production (supervisor + nginx)
# ----------------------------------------------------------------------------------------------
log "Stage 9: bench setup production"
rm -f /etc/nginx/sites-enabled/default
if [ -e /etc/nginx/conf.d/frappe-bench.conf ] && [ -e /etc/supervisor/conf.d/frappe-bench.conf ]; then
  info "Production config already present; regenerating nginx only."
  bench_cmd setup nginx --yes
else
  (cd "$BENCH_DIR" && "$BENCH_BIN" setup production "$FRAPPE_USER" --yes)
fi
systemctl enable supervisor nginx
nginx -t
systemctl restart supervisor || true
systemctl reload nginx
chmod 755 "$FRAPPE_HOME"

# ----------------------------------------------------------------------------------------------
# Stage 10: firewall (Oracle images ship iptables REJECT rules that block 80/443)
# ----------------------------------------------------------------------------------------------
log "Stage 10: iptables 80/443"
for PORT in 80 443; do
  if iptables -C INPUT -p tcp --dport "$PORT" -m conntrack --ctstate NEW -j ACCEPT 2>/dev/null; then
    info "Port $PORT already accepted."
  else
    # Position of the first REJECT rule in INPUT (iptables -S prints the policy on line 1).
    REJECT_LINE="$(iptables -S INPUT | grep -n -m1 -- '-j REJECT' | cut -d: -f1 || true)"
    if [ -n "$REJECT_LINE" ]; then
      iptables -I INPUT "$((REJECT_LINE - 1))" -p tcp --dport "$PORT" -m conntrack --ctstate NEW -j ACCEPT
    else
      iptables -A INPUT -p tcp --dport "$PORT" -m conntrack --ctstate NEW -j ACCEPT
    fi
    info "Opened port $PORT in iptables."
  fi
done
netfilter-persistent save
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q 'Status: active'; then
  ufw allow 80/tcp; ufw allow 443/tcp
fi
info "Remember: the VCN Security List (or NSG) must also allow ingress TCP 80 and 443 in the Oracle console."

# ----------------------------------------------------------------------------------------------
# Stage 11: fail2ban, unattended upgrades
# ----------------------------------------------------------------------------------------------
log "Stage 11: fail2ban and unattended-upgrades"
cat > /etc/fail2ban/jail.d/school-demo.local <<'EOF'
[sshd]
enabled = true
maxretry = 5
findtime = 10m
bantime = 1h
EOF
systemctl enable --now fail2ban
systemctl restart fail2ban || true
echo 'APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";' > /etc/apt/apt.conf.d/20auto-upgrades
systemctl enable --now unattended-upgrades || true

# ----------------------------------------------------------------------------------------------
# Stage 12: HTTPS with certbot (optional)
# ----------------------------------------------------------------------------------------------
SCHEME=http
if [ -n "$LETSENCRYPT_EMAIL" ]; then
  log "Stage 12: Let's Encrypt for ${SITE_NAME}"
  CERT_DIR="/etc/letsencrypt/live/${SITE_NAME}"
  SSL_DIR="/etc/ssl/school_demo"
  mkdir -p "$SSL_DIR" /etc/letsencrypt/renewal-hooks/deploy
  chmod 755 "$SSL_DIR"

  # Hook run after every issue and renewal: copy to a path the bench user can stat, reload nginx.
  cat > /etc/letsencrypt/renewal-hooks/deploy/school_demo.sh <<EOF
#!/bin/sh
set -e
install -m 644 "${CERT_DIR}/fullchain.pem" "${SSL_DIR}/fullchain.pem"
install -m 640 -g ${FRAPPE_USER} "${CERT_DIR}/privkey.pem" "${SSL_DIR}/privkey.pem"
nginx -t && systemctl reload nginx
EOF
  chmod 755 /etc/letsencrypt/renewal-hooks/deploy/school_demo.sh

  if [ ! -d "$CERT_DIR" ]; then
    PUBLIC_IP="$(curl -4 -fsS --max-time 10 https://api.ipify.org 2>/dev/null || true)"
    DNS_IP="$(getent ahostsv4 "$SITE_NAME" | awk 'NR==1{print $1}' || true)"
    if [ "$FORCE_CERTBOT" != 1 ] && [ -n "$PUBLIC_IP" ] && [ "$PUBLIC_IP" != "$DNS_IP" ]; then
      warn "${SITE_NAME} resolves to '${DNS_IP:-nothing}' but this VM is ${PUBLIC_IP}. Fix the DNS A record (or use"
      warn "FORCE_CERTBOT=1 if you are behind a proxy) and re-run; skipping the certificate for now."
    else
      # Standalone challenge on port 80; nginx is stopped only for those few seconds (also on renewal).
      if certbot certonly --standalone -d "$SITE_NAME" -m "$LETSENCRYPT_EMAIL" --agree-tos --non-interactive \
           --pre-hook 'systemctl stop nginx' --post-hook 'systemctl start nginx'; then
        :
      else
        warn "certbot failed (DNS not pointing here yet, or port 80 closed in the Oracle Security List?)."
      fi
      systemctl start nginx || true
    fi
  else
    info "Certificate already exists."
  fi

  if [ -d "$CERT_DIR" ]; then
    /etc/letsencrypt/renewal-hooks/deploy/school_demo.sh
    bench_cmd --site "$SITE_NAME" set-config ssl_certificate "${SSL_DIR}/fullchain.pem"
    bench_cmd --site "$SITE_NAME" set-config ssl_certificate_key "${SSL_DIR}/privkey.pem"
    bench_cmd --site "$SITE_NAME" set-config host_name "https://${SITE_NAME}"
    bench_cmd setup nginx --yes
    nginx -t
    systemctl reload nginx
    SCHEME=https
    systemctl enable --now certbot.timer 2>/dev/null || true
    certbot renew --dry-run || warn "certbot renew --dry-run failed; check /var/log/letsencrypt/letsencrypt.log"
  fi
else
  log "Stage 12: skipped (no LETSENCRYPT_EMAIL). Re-run with --email you@example.com once DNS points here."
fi

# ----------------------------------------------------------------------------------------------
# Stage 13: smoke test and summary
# ----------------------------------------------------------------------------------------------
log "Stage 13: smoke test"
sleep 5
PING="$(curl -fsS --max-time 20 -H "Host: ${SITE_NAME}" http://127.0.0.1/api/method/ping 2>/dev/null || true)"
DEMO_CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 -H "Host: ${SITE_NAME}" http://127.0.0.1/demo || true)"
info "ping: ${PING:-no response}   /demo HTTP: ${DEMO_CODE}   (301 to https is fine when a certificate is installed)"
info "scheduler: $(bench_cmd --site "$SITE_NAME" scheduler status 2>&1 | tail -1)"
supervisorctl status || true

echo
echo "============================================================"
echo " School Demo is set up."
echo "   URL:            ${SCHEME}://${SITE_NAME}/demo"
echo "   Administrator:  /app  (user Administrator)"
if [ "$GENERATED_ADMIN" = 1 ]; then
  echo "   Admin password: ${ADMIN_PASSWORD}   <-- generated, shown only now; also in ${SECRETS_FILE}"
else
  echo "   Admin password: the one you supplied (saved root-only in ${SECRETS_FILE})"
fi
echo "   DB root pw:     in ${SECRETS_FILE}"
echo "   Demo logins:    see /demo (password demo1234), reset daily by the scheduler"
echo "   Log:            ${LOG_FILE}"
echo "============================================================"
