# Deploying School Demo on Frappe Cloud

Frappe Cloud hosts Frappe sites and manages benches for you. These steps publish the demo as a
Frappe-only site (no ERPNext) with the demo data pre-loaded.

## 1. Push the app to GitHub

The app must be in a GitHub repository that Frappe Cloud can read:

    github.com/almariebu/school_demo   (branch: main)

For a private repository, install the Frappe Cloud GitHub app on it first (Frappe Cloud asks you
to authorise GitHub in step 2).

## 2. Add the app to Frappe Cloud

1. Sign in at https://frappecloud.com/dashboard and open **Apps** (Marketplace / My Apps).
2. Choose **Add App**, then **From GitHub**.
3. Authorise GitHub if asked, select `almariebu/school_demo`, and pick the branch `main`.
4. Frappe Cloud reads `pyproject.toml` and `hooks.py` and registers the app as `school_demo`.

## 3. Create a bench group with Frappe version-15

1. Open **Bench Groups** and choose **New Bench Group**.
2. Select **Version 15** and the **Frappe Framework** app.
3. Add **School Demo** under additional apps. Do not add ERPNext.
4. Create the bench group and wait for the first deploy to finish (the build runs `bench build`).

## 4. Create the site

1. In the bench group, choose **New Site**.
2. Pick a subdomain (for example `school-demo`) and the region, select Version 15 and the
   `school_demo` app, and create the site.
3. If you did not select the app at creation time, open the site, go to **Apps**, and install
   **School Demo**.

## 5. Turn on seeding

1. Open the site, then **Site Config** (or **Config**).
2. Add a key `school_demo_seed` with value `1` (type: Number).
3. Save. This flag has two effects:
   - `after_install` seeds demo data when the app is installed on a site that already has the flag.
   - The daily scheduler job `school_demo.setup.reset.reset_demo` only runs on sites with the flag,
     so a production site is never wiped by accident.

## 6. Run the seed

If the app was installed before the flag was set, load the data manually:

1. Open the site, then **Bench Console** (also called **SSH / Console**).
2. Run:

       bench --site <your-site>.frappe.cloud execute school_demo.setup.demo_data.seed

   If your plan has no shell, open **Desk, Awesomebar, "System Console"** (requires System Manager and
   developer mode) and run:

       from school_demo.setup.demo_data import seed
       seed()

The seed is idempotent. Running it again does not create duplicates.

## 7. Check it

1. Visit `https://<your-site>.frappe.cloud/demo` (public page with the demo logins).
2. Sign in as `registrar@demo.local` / `demo1234` and open the **School Demo** workspace.
3. In **Scheduled Job Type**, confirm `school_demo.setup.reset.reset_demo` is listed as Daily.

## 8. Keep it healthy

- Scheduler: Frappe Cloud runs it for you. If the site was suspended and resumed, check
  **Site, Overview, Scheduler** is on.
- Changing the demo passwords: edit `DEMO_PASSWORD` in `school_demo/setup/demo_constants.py`; the next
  seed or daily reset applies it.
- Updating the app: push to `main`, then in the bench group choose **Update Available** and deploy.
  Schema changes are applied by `bench migrate` as part of the deploy.
- Resetting by hand: `bench --site <site> execute school_demo.setup.reset.reset_demo --kwargs "{'force': True}"`.

## Self-hosting instead

See `deploy/docker-compose.yml` (frappe_docker style, custom image built from `deploy/apps.json`).

Free alternative on your own VM: see [`oracle/ORACLE_CLOUD.md`](oracle/ORACLE_CLOUD.md) (Oracle Cloud Always Free, ARM).
