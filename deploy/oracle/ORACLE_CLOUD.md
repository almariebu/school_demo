# Host School Demo on Oracle Cloud Always Free (ARM)

This guide puts the public demo on a free **VM.Standard.A1.Flex** (Ampere ARM, aarch64) instance
running Ubuntu 22.04 or 24.04, with nginx, MariaDB, supervisor and HTTPS, using
[`setup.sh`](setup.sh). Total time: about 1 hour, of which the script is 20 to 40 minutes.

Oracle's console wording changes now and then. Where this guide names a menu, look for the closest
match if your screen differs.

## 1. Sign up

1. Create an account at https://www.oracle.com/cloud/free/ . A credit or debit card is needed for
   identity verification. You are not charged for Always Free resources; the card may show a small
   temporary authorization that is reversed.
2. **Choose your home region carefully.** It cannot be changed later, and Always Free A1 capacity
   is not equal everywhere. Pick a region close to your visitors, and prefer a large, busy one
   over a tiny one. Always Free compute only exists in your home region.
3. You also get a time-limited trial credit. Ignore it: everything below stays inside Always Free.

Always Free budget for Arm: 4 OCPU and 24 GB RAM in total, and 200 GB of block storage in total
(boot volumes count).

## 2. Network: VCN with internet access

1. Menu, **Networking, Virtual cloud networks, Start VCN Wizard**.
2. Choose **Create VCN with Internet Connectivity**, name it `school-demo-vcn`, keep the default
   CIDR blocks, and finish. This creates a public subnet, an internet gateway and a route table.

## 3. Create the instance

1. Menu, **Compute, Instances, Create instance**. Name: `school-demo`.
2. **Image and shape, Edit**:
   - Image: **Canonical Ubuntu 24.04** (or 22.04). Make sure it is the aarch64 / ARM build.
   - Shape: **Ampere, VM.Standard.A1.Flex**. Recommended **2 OCPU / 12 GB**. If you will not run
     anything else, **4 OCPU / 24 GB** is also free. 1 OCPU / 6 GB works but the first `bench init`
     is slow.
3. **Networking**: select `school-demo-vcn` and the **public subnet**, and keep
   **Assign a public IPv4 address** on (you replace it with a reserved one in step 4).
4. **Add SSH keys**: choose **Paste public keys** or **Generate a key pair for me** and download the
   private key. On your own computer you can create one with `ssh-keygen -t ed25519`, then paste
   the contents of `~/.ssh/id_ed25519.pub`.
5. **Boot volume**: tick **Specify a custom boot volume size** and use **50 to 100 GB**
   (200 GB free in total; leave room for backups).
6. **Create**. Wait for the state to become **Running**.

### "Out of capacity for shape VM.Standard.A1.Flex"

This is common. Things that work, in order:

- Try again every few minutes, and especially at off-peak hours (early morning in the region).
- Try another **Availability Domain** in the same region (the dropdown under Placement), if your
  region has more than one.
- Ask for less: 1 OCPU / 6 GB or 2 / 12 often succeeds when 4 / 24 does not. You can resize
  a A1.Flex instance later (stop it, edit shape).
- Upgrading the account to **Pay As You Go** (see step 12) makes capacity much easier to get, and
  Always Free resources stay free.
- Some people script retries with the OCI CLI or Terraform; that is optional.

## 4. Reserve a public IP

Without this, the IP can change when the instance is recreated.

1. Menu, **Networking, IP management, Reserved public IPs, Reserve public IP address**
   (the free tier includes reserved IPs while they are attached). Name it `school-demo-ip`.
2. Open the instance, **Attached VNICs**, the primary VNIC, **IPv4 addresses**, Edit the
   address, choose **No public IP** (this releases the ephemeral one), then Edit again and pick
   **Reserved public IP** and your `school-demo-ip`.
3. Note the address. Test SSH (the default user is `ubuntu`):

   ```bash
   ssh -i ~/.ssh/id_ed25519 ubuntu@<RESERVED_IP>
   ```

## 5. Open ports 80 and 443 (two places, both required)

Opening only one of them is the most common reason the site "does not load".

### 5a. Oracle VCN Security List

1. **Networking, Virtual cloud networks, school-demo-vcn, Security, Default Security List for
   school-demo-vcn, Add Ingress Rules**.
2. Add two rules: Source CIDR `0.0.0.0/0`, IP Protocol **TCP**, Destination Port Range `80`;
   and the same with `443`. Leave Source Port Range empty. (Port 22 is already there.)

### 5b. The Ubuntu image's own firewall (the gotcha)

Oracle's Ubuntu images ship `/etc/iptables/rules.v4` with a final rule similar to

```
-A INPUT -j REJECT --reject-with icmp-host-prohibited
```

Anything not accepted before that line is rejected, even when the Security List allows it. So an
`ACCEPT` for 80/443 must be **inserted above the REJECT line**; appending with `iptables -A` puts
it after the REJECT and does nothing. Then save so it survives reboots. `setup.sh` does this
automatically; to do it by hand:

```bash
sudo iptables -L INPUT -n --line-numbers          # find the REJECT line number, say 6
sudo iptables -I INPUT 6 -p tcp --dport 80  -m conntrack --ctstate NEW -j ACCEPT
sudo iptables -I INPUT 6 -p tcp --dport 443 -m conntrack --ctstate NEW -j ACCEPT
sudo netfilter-persistent save                     # package: iptables-persistent
```

Verify later from your laptop: `curl -I http://<IP>` should answer (even a 404 or redirect is fine);
"connection timed out" means the Security List, "connection refused/rejected" means iptables.

## 6. Domain name

The **site name must equal the hostname** visitors use (Frappe picks the site from the `Host`
header), for example `demo.example.com`. Choose one:

- **Your own domain:** at your DNS provider create an **A record** `demo` pointing to the reserved
  IP. Use `Proxy: DNS only` first.
- **Free DuckDNS subdomain:** sign in at https://www.duckdns.org , create e.g. `school-demo`, and
  set its **current ip** to the reserved IP. The site name is then `school-demo.duckdns.org`.
  Because the IP is reserved and does not change, no cron updater is needed.
- **Cloudflare (optional):** with your own domain on Cloudflare you may turn the proxy (orange
  cloud) on after the certificate is issued. Set SSL/TLS mode to **Full (strict)**. Keep it
  DNS-only while running setup, since the script compares the DNS answer with the VM's IP before
  asking Let's Encrypt for a certificate (set `FORCE_CERTBOT=1` to skip that check).

Check: `getent hosts demo.example.com` shows the reserved IP.

## 7. Make the repository readable by the VM

`github.com/almariebu/school_demo` is currently **private**, so the VM cannot clone it anonymously.
Pick one:

1. **Make it public** (simplest for a portfolio demo): GitHub, repo Settings, Danger Zone,
   Change visibility. Nothing else is needed.
2. **Deploy key (SSH):** run the script with
   `APP_REPO=git@github.com:almariebu/school_demo.git`. On the first run it creates an SSH key for
   the `frappe` user, prints the public key and stops. Add it at repo Settings, Deploy keys, Add
   deploy key (read-only), then run the script again.
3. **Token (HTTPS):** create a fine-grained personal access token with read-only **Contents**
   access to this one repository and run with `GITHUB_TOKEN=github_pat_...`. The token is stored in
   the app's git remote so `update.sh` can pull; revoke it if you later make the repo public.

## 8. Run the setup script

SSH into the VM and fetch the script (public repo shown; otherwise copy it with
`scp deploy/oracle/setup.sh ubuntu@<IP>:`):

```bash
curl -fsSLO https://raw.githubusercontent.com/almariebu/school_demo/main/deploy/oracle/setup.sh
less setup.sh        # read it before running anything as root
```

Run it (replace the values; use a long unique Administrator password):

```bash
sudo SITE_NAME=demo.example.com \
     ADMIN_PASSWORD='use-a-long-random-password-here' \
     LETSENCRYPT_EMAIL=you@example.com \
     bash setup.sh
```

Leave `ADMIN_PASSWORD` out to have one generated; it is printed once at the end and kept in the
root-only file `/root/.school_demo_secrets` (together with the generated MariaDB root password).
Leave `LETSENCRYPT_EMAIL` out to install HTTP only and add HTTPS later (step 9). Flags work too:
`sudo bash setup.sh --site demo.example.com --email you@example.com`.

What it does, in order (each stage is skipped when already done, so after any failure just run it
again):

1. `apt` packages: build tools, Python 3 (3.10 on Ubuntu 22.04, 3.12 on 24.04; both work for v15),
   MariaDB, nginx, supervisor, certbot, fail2ban, unattended-upgrades.
2. Swap file (4 GB by default, `SWAP_GB=`), `vm.swappiness=10`.
3. MariaDB utf8mb4 config in `/etc/mysql/mariadb.conf.d/99-frappe.cnf`, root password set.
4. Node.js 20 (NodeSource) and yarn; wkhtmltopdf with patched Qt for arm64 when available (not
   fatal if it fails; only PDF printing is affected). The system `redis-server` service is
   disabled because bench runs its own Redis instances under supervisor.
5. User `frappe` and `frappe-bench` in `/home/frappe/.bench-venv`.
6. `bench init --frappe-branch version-15` (the slowest step: 10 to 25 minutes on 2 OCPU).
7. `bench get-app` for `school_demo` (branch `main`).
8. `bench new-site`, `set-config school_demo_seed 1`, `install-app`, seed, `scheduler enable`,
   and demo hardening (step 10).
9. `bench setup production frappe`: supervisor (web, socketio, worker, scheduler, Redis) and nginx.
10. iptables ACCEPT for 80 and 443 above the REJECT rule, saved with `netfilter-persistent`.
11. fail2ban for SSH and automatic security updates.
12. Optional HTTPS with certbot.
13. Smoke test and a summary with the URL.

Everything is logged to `/var/log/school_demo_setup.log`.

## 9. HTTPS

The script (when `LETSENCRYPT_EMAIL` is set and DNS already points to the VM) uses the **certbot
standalone** method: `certbot certonly --standalone`, with a pre hook that stops nginx and a post
hook that starts it, so port 80 is free for the challenge. The certificate is copied to
`/etc/ssl/school_demo/`, the paths are written to the site as `ssl_certificate` and
`ssl_certificate_key`, and `bench setup nginx` regenerates the nginx config with the port 443 server
and the HTTP to HTTPS redirect. I chose this over `bench setup lets-encrypt` and the
`certbot --nginx` plugin because bench regenerates its nginx file (`bench setup nginx` would erase
edits made by the plugin), and standalone needs no changes to that file. Both bench and the plugin
can work, but this path has the fewest moving parts.

**Renewal** is automatic: Ubuntu's `certbot.timer` runs twice a day and renews 30 days before expiry.
The renewal re-uses the stop and start hooks (a few seconds of downtime) and the deploy hook
`/etc/letsencrypt/renewal-hooks/deploy/school_demo.sh` copies the new files and reloads nginx.
Test with `sudo certbot renew --dry-run`.

To add HTTPS after the first run, fix DNS, then run the same `setup.sh` command again with
`LETSENCRYPT_EMAIL` (the rest is skipped), or by hand:

```bash
sudo certbot certonly --standalone -d demo.example.com -m you@example.com --agree-tos \
     --pre-hook 'systemctl stop nginx' --post-hook 'systemctl start nginx'
```

then re-run `setup.sh` so the paths and nginx config are applied.

## 10. Check it works

Replace `demo.example.com` with your site name.

```bash
curl -s https://demo.example.com/api/method/ping          # {"message":"pong"}
curl -sI https://demo.example.com/demo | head -1          # HTTP/2 200
sudo -u frappe -H bash -c 'cd ~/frappe-bench && bench --site demo.example.com scheduler status'
sudo supervisorctl status                                  # all RUNNING
sudo -u frappe -H bash -c "cd ~/frappe-bench && bench --site demo.example.com execute \
   frappe.db.get_all --kwargs \"{'doctype':'Scheduled Job Type','filters':{'method':'school_demo.setup.reset.reset_demo'},'fields':['method','frequency','stopped']}\""
```

In the browser:

1. Open `https://demo.example.com/demo` and sign in with a demo login, for example
   `registrar@demo.local` / `demo1234`, then open the **School Demo** workspace.
2. Sign in at `/login` as **Administrator** with your password.
3. The daily reset (`school_demo.setup.reset.reset_demo`) is a Daily scheduled job and runs
   because the site has `school_demo_seed`. To test it immediately:

   ```bash
   sudo -u frappe -H bash -c "cd ~/frappe-bench && bench --site demo.example.com execute \
      school_demo.setup.reset.reset_demo --kwargs \"{'force': True}\""
   ```

## 11. Demo hardening

`setup.sh` already applies most of these; verify or apply by hand as the `frappe` user inside
`~/frappe-bench`:

| Item | How |
| --- | --- |
| Website signup off | `bench --site SITE execute frappe.db.set_single_value --args "['Website Settings','disable_signup',1]"` |
| Login brute-force limit | System Settings `allow_consecutive_login_attempts` = 5 and `allow_login_after_fail` = 120 (set by the script) |
| No outgoing mail attempts | `bench --site SITE set-config mute_emails 1 --parse` |
| Production mode | `developer_mode` 0 and `allow_tests` 0 (set by the script); never leave developer mode on a public site |
| Administrator password | long, unique, never put on the public page. Change: `bench --site SITE set-admin-password 'NEW'` |
| Demo users' passwords | Frappe has no simple switch to block password change or reset for chosen users. Visitors who change a demo password are undone because `seed()` calls `update_password` for every demo user, and the daily reset runs it. With `mute_emails` on, reset links are never delivered, so visitors cannot lock themselves out for long. |
| SSH brute force | fail2ban `sshd` jail (installed by the script); check with `sudo fail2ban-client status sshd` |
| Updates | unattended-upgrades enabled; reboot occasionally (`sudo reboot`) when `/var/run/reboot-required` exists |
| Swap | 4 GB swap file with swappiness 10 (installed by the script; check with `free -h`) |
| Request rate limits | the login limit above covers password guessing. For general rate limiting, put the site behind Cloudflare (Rate limiting rules) or add `limit_req` to the nginx config. Do not edit `config/nginx.conf` by hand, because `bench setup nginx` overwrites it. |
| SSH keys only | Ubuntu on OCI already disables password SSH login; keep it that way |

## 12. Backups

Daily backups of the database and files (the demo data itself is re-seeded daily, but the site
setup is worth keeping):

```bash
sudo -u frappe crontab -l 2>/dev/null | { cat; echo '30 2 * * * cd /home/frappe/frappe-bench && /home/frappe/.bench-venv/bin/bench --site demo.example.com backup --with-files >> /home/frappe/backup.log 2>&1'; } | sudo -u frappe crontab -
```

Backups land in `~/frappe-bench/sites/demo.example.com/private/backups/`. Copy them off the VM
(for example `scp`, or an Oracle Object Storage bucket, 20 GB free) and prune old ones
(`find ... -mtime +14 -delete`). Also consider a boot volume backup in the Oracle console
(Compute, Boot Volumes, Backups; a few are free).

## 13. Updating the app

After pushing to `main`, on the VM:

```bash
curl -fsSLO https://raw.githubusercontent.com/almariebu/school_demo/main/deploy/oracle/update.sh
sudo bash update.sh --site demo.example.com
```

`update.sh` backs up, pulls, runs `bench --site SITE migrate`, `bench build --app school_demo`, and
restarts supervisor. The manual equivalent is `git -C ~/frappe-bench/apps/school_demo pull`, then
`bench --site SITE migrate`, `bench build --app school_demo`, `bench restart` (or
`sudo supervisorctl restart all`).

## 14. Monitoring and logs

```bash
sudo supervisorctl status
tail -f /home/frappe/frappe-bench/logs/web.error.log /home/frappe/frappe-bench/logs/worker.error.log
tail -f /home/frappe/frappe-bench/logs/scheduler.log
sudo tail -f /var/log/nginx/error.log
sudo journalctl -u mariadb -n 100
free -h; df -h /; uptime
```

In Desk, **Error Log** and **Scheduled Job Log** show app-level failures. An external uptime
checker (UptimeRobot free tier) on `/api/method/ping` also helps.

## 15. Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| Browser times out | Port blocked: check the Security List (5a) and iptables (5b). `sudo iptables -S INPUT` must show the ACCEPT lines before REJECT. |
| 502 Bad Gateway | Gunicorn not running. `sudo supervisorctl status`, then `sudo supervisorctl restart all`; read `logs/web.error.log`. Right after a reboot wait a minute. |
| 404 "does not exist" page for the site | Site name differs from the hostname. `ls ~/frappe-bench/sites`; rename or create the site with the exact hostname, then `bench setup nginx --yes` and reload nginx. |
| Page loads without CSS or JS (assets 404) | `bench build --app school_demo` was not run, or nginx cannot read `/home/frappe`. Run `chmod 755 /home/frappe`, `bench build`, `sudo systemctl reload nginx`. |
| Redis errors (connection refused 11000 / 13000) | The bench Redis programs are down. `sudo supervisorctl restart all`. Do not run the system `redis-server` for bench. |
| `Can't connect to MySQL` / access denied | `sudo systemctl status mariadb`; start it. Check site `db_password` in `sites/SITE/site_config.json`; the root password is in `/root/.school_demo_secrets`. |
| Process killed, OOM in `dmesg` | Add swap (`free -h`), use 12 GB RAM or more, restart. During `bench init` on 1 OCPU / 6 GB, wait it out or temporarily add more swap. |
| certbot fails | DNS not pointing at the VM yet, port 80 closed (5a or 5b), or Cloudflare proxy in front. Fix, then re-run `setup.sh`. Let's Encrypt limits repeated failures to 5 per hour. |
| Scheduler says disabled or inactive | `bench --site SITE scheduler enable`, then `sudo supervisorctl restart all`. |
| Instance stopped or disappeared | **Idle reclamation:** Oracle may reclaim Always Free instances that stay idle (roughly: CPU, network and memory all low for 7 days). A mostly-idle demo can hit this. Mitigations: keep the daily scheduler and an uptime monitor pinging the site, and best of all upgrade the account to **Pay As You Go**. PAYG keeps Always Free resources free (you are charged only for usage above the free limits, so stay within 4 OCPU / 24 GB / 200 GB) and removes the reclamation risk. Set a budget alert in **Billing, Budgets**. |

## 16. Give the portfolio the URL

When `https://demo.example.com/demo` loads and the demo logins work, send the final URL
(`https://<your-site>/demo`) to the portfolio, which should link to it as the live demo. Also paste
a note that the data resets daily.
