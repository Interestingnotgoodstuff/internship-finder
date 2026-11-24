# Internship Finder + Recruiting Hub

Checks the job boards of finance firms every morning, keeps only internships,
judges whether a **May 2028 graduate** can apply, and shows everything on a
dashboard. You also get an email when something new appears.

- **Dashboard:** `https://<your-github-username>.github.io/internship-finder/`
- **Runs:** every day around 6:15 a.m. Central, plus any time you click "Run workflow"
- **Covers:** firms using Workday, Greenhouse, Lever, or Ashby (most banks,
  ratings agencies, credit funds, and many boutiques). Firms with custom career
  sites (Goldman, J.P. Morgan, Moelis) are still covered by the Monday Claude sweep.

## One-time setup (about 15 minutes)

### 1. Put the code on GitHub
1. Create a free account at github.com if you don't have one.
2. Click **New repository**, name it `internship-finder`, choose **Public**, and
   don't add a README. (Public is required for free GitHub Pages. The repo holds
   only job postings, no personal info. Your email password lives in a secret.)
3. Upload the files: Claude can push them for you, or you can drag the unzipped
   folder onto the repo page ("uploading an existing file"). Make sure the hidden
   `.github` folder comes along.

### 2. Turn on the dashboard
Repo → **Settings** → **Pages** → *Build and deployment*: Source **Deploy from a branch**,
Branch **main**, folder **/docs** → **Save**. About a minute later the dashboard is live.

### 3. Let the daily run save results
Repo → **Settings** → **Actions** → **General** → *Workflow permissions*:
choose **Read and write permissions** → **Save**.

### 4. Set up email alerts (optional, recommended)
1. In your Google account, turn on 2-Step Verification, then search the settings
   for **App passwords** and create one called "Internship Finder". Copy the
   16-character password.
2. Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**. Add:
   - `SMTP_USER`: your Gmail address
   - `SMTP_PASS`: the 16-character app password
   - `ALERT_TO`: where to send alerts (can be the same Gmail, or comma-separated addresses)

### 5. First run
Repo → **Actions** → **Daily internship scan** → **Run workflow**. When it finishes
(5 to 15 minutes), refresh the dashboard. The first run marks everything as
new, so the first email will be long.

## The hub tabs
- **Jobs:** click **Apply** to open the posting. When you come back, the card asks
  "Did you submit it?" Click **Yes** and it's logged as applied with today's date.
  **People + messages** shows LinkedIn searches for alumni and analysts at that firm,
  plus message drafts with the firm and role filled in. Nothing about contacts is saved.
- **Tracker:** every application, its status (OA, interview, superday, offer…),
  and the next step. Add applications you found elsewhere.
- **Technicals:** about 100 original interview questions with flashcards. Missed ones come back sooner.
- **Excel:** shortcut and function quizzes, plus model-building drills checked against the answer.
- **Sync:** sign in with a GitHub token (Gist permission only) to sync progress
  between computers. Progress is stored in a private Gist in your account.

## Daily use
- **Dashboard defaults:** Eligible + Unclear, US only, finance roles only.
- **Unclear** means it's a summer 2027 role that doesn't state graduation dates.
  Usually fine; open the posting to confirm.
- **Process:** apply, then message a contact at that firm within 24 hours, and log it
  in your networking tracker.

## Adding firms
Open any posting on the firm's careers site and look at the URL:

| URL looks like | Add to `config/companies.yaml` |
|---|---|
| `https://bmo.wd3.myworkdayjobs.com/Campus/job/...` | `{name: "BMO", category: "...", ats: workday, tenant: bmo, wd: wd3, site: Campus}` |
| `https://job-boards.greenhouse.io/liontree/jobs/...` | `{name: "LionTree", category: "...", ats: greenhouse, token: liontree}` |
| `https://jobs.lever.co/dadavidson/...` | `{name: "D.A. Davidson", category: "...", ats: lever, slug: dadavidson}` |
| `https://jobs.ashbyhq.com/maca/...` | `{name: "MACA", category: "...", ats: ashby, org: maca}` |

Not sure? Add the firm under `candidates` with some guesses, then run
**Actions → Discover job boards**. The run's Summary page shows which guesses
work, with the exact line to copy.

## Checking that it's working
At the bottom of the dashboard, **Job boards checked** lists every firm. A red
error usually means the firm changed its site name. Fix the entry, or ask Claude to.

## How eligibility is decided
`finder/classify.py` reads each posting's title and description:
- **Eligible:** a graduation window that includes May 2028, "class of 2028",
  or "penultimate year" / junior / rising senior.
- **Not eligible:** summer 2028 programs (class of 2029), MBA / summer associate
  roles, class-of-2027 full-time roles, or windows that exclude May 2028.
- **Unclear:** anything else. Each posting shows the reason on the dashboard.

## Running it yourself (optional)
```
pip install -r requirements.txt
python -m finder.main          # real scan
python -m finder.main --demo   # sample data to preview the dashboard
python -m pytest -q            # tests
```
