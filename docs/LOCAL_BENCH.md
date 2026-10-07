# Run School Demo on a local bench (Frappe v15)

Tested on Ubuntu 24.04 with MariaDB 10.11, Python 3.12, Node 22, Frappe `version-15`.
On Windows use WSL2 with an Ubuntu distro and follow the Ubuntu steps inside it.

## 1. System packages (Ubuntu / WSL)

```bash
sudo apt-get update
sudo apt-get install -y git curl build-essential pkg-config python3.12 python3.12-dev python3.12-venv \
    mariadb-server mariadb-client libmariadb-dev redis-server
# Node 22 + yarn (nvm shown; any Node 18-22 works for v15)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
source ~/.bashrc && nvm install 22 && npm i -g yarn
# optional, only for PDF printing: sudo apt-get install -y wkhtmltopdf
```

Python 3.13 is too new for Frappe v15, so use 3.12 explicitly (`--python python3.12` below).

## 2. MariaDB

Add `/etc/mysql/mariadb.conf.d/99-frappe.cnf`:

```ini
[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
```

Start it and set the root password used by `bench new-site`:

```bash
sudo service mariadb start            # WSL without systemd: sudo mysqld_safe &
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED VIA mysql_native_password USING PASSWORD('root'); FLUSH PRIVILEGES;"
```

## 3. Bench

```bash
pip install --user pipx && pipx ensurepath        # or: uv tool install frappe-bench
pipx install frappe-bench --python python3.12
bench init ~/frappe-bench --python python3.12 --frappe-branch version-15
cd ~/frappe-bench
```

`bench init` generates the redis configs and a Procfile; `bench start` launches redis, web, socketio,
scheduler and worker, so do not run a separate redis on ports 11000/13000.

## 4. Site and app

```bash
bench new-site demo.localhost --admin-password admin --mariadb-root-password root
bench get-app school_demo /path/to/school_demo          # or the GitHub URL, branch main
# working on a local clone instead? symlink it so edits are live:
#   ln -s ~/school_demo apps/school_demo && ./env/bin/pip install -e apps/school_demo
#   printf 'school_demo\n' >> sites/apps.txt      (make sure it is listed after frappe)

bench --site demo.localhost set-config school_demo_seed 1
bench --site demo.localhost set-config allow_tests true --parse
bench --site demo.localhost set-config developer_mode 1 --parse
bench --site demo.localhost install-app school_demo      # seeds the demo data because of school_demo_seed
bench --site demo.localhost execute school_demo.setup.demo_data.seed   # optional, idempotent
```

## 5. Run and verify

```bash
bench start                    # http://demo.localhost:8000  (Administrator / admin)
bench --site demo.localhost run-tests --app school_demo      # 49 tests
python3 -m unittest tests.test_logic                          # pure logic, no bench needed
bench build --app school_demo
```

Demo logins (password `demo1234`): `registrar@demo.local`, `dean@demo.local`, `finance@demo.local`,
`cashier@demo.local`, `teacher@demo.local`, `teacher2@demo.local`. The guide page is `/demo`; the
workspace is `/app/school-demo`.

Reset the demo data at any time (also what the daily scheduler job does):

```bash
bench --site demo.localhost execute school_demo.setup.reset.reset_demo --kwargs "{'force': True}"
```

## Troubleshooting

- `*.localhost` resolves to 127.0.0.1 in modern browsers. If yours does not, add `127.0.0.1 demo.localhost`
  to the hosts file (on WSL, edit the Windows hosts file).
- `yarn install` fails fetching `codeload.github.com` tarballs (corporate proxy): point the
  `air-datepicker` entry in `apps/frappe/package.json` at `git+https://github.com/frappe/air-datepicker.git`.
- `Access denied for user 'root'` in `new-site`: the root password step in section 2 was skipped.
- Port 8000, 11000 or 13000 already in use: stop the old bench or redis first.

## macOS differences

```bash
brew install python@3.12 mariadb@10.11 redis node@22 yarn pkg-config
brew services start mariadb@10.11 && brew services start redis
```

Use the same MariaDB config in `$(brew --prefix)/etc/my.cnf.d/`, set the root password with
`sudo mysql` (or `mysql -uroot`) as above, and run every other step unchanged. Apple Silicon needs
`export PATH="$(brew --prefix mariadb@10.11)/bin:$PATH"` so `bench new-site` finds `mysql`. Skip `wkhtmltopdf`
unless you need PDF output.
