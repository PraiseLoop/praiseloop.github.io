# PraiseLoop public website

The public website for PraiseLoop, served at <https://praiseloop.ca> by GitHub Pages.

This is a separate repository from the PraiseLoop app. It holds static files only: no
JavaScript, no framework, no build step and no npm. Every page works offline from the
files in this repository, and nothing is loaded from another site.

## What is here

| Path | Purpose |
| --- | --- |
| `index.html` | Home page |
| `404.html` | Page shown for a missing URL |
| `privacy/index.html` | Privacy policy (directory URL `/privacy/`) |
| `terms/index.html` | Terms of service (directory URL `/terms/`) |
| `styles.css` | The only stylesheet, for every page, light and dark |
| `assets/favicon.svg` | Browser icon |
| `assets/logo.svg` | Standalone wordmark on a light background, for print or profile use |
| `CNAME` | Custom domain: `praiseloop.ca` |
| `.nojekyll` | Tells GitHub Pages to serve the files as they are |
| `robots.txt` | Allows all crawlers and points at the sitemap |
| `sitemap.xml` | Public URLs and their last-modified date |
| `check_site.py` | Local checks, standard library only |

Pages use directory URLs (`/privacy/` is `privacy/index.html`) and root-relative links.
The header, footer and skip link are shared markup, styled in `styles.css`.

## How GitHub Pages serves this

GitHub Pages publishes the repository's `main` branch from the repository root. There is
no build: the committed files are the site. `CNAME` sets the custom domain to
`praiseloop.ca`, and `.nojekyll` turns off Jekyll processing. HTTPS is provided by
GitHub Pages once the custom domain is verified and a certificate has been issued.

## One-time setup (the owner does this, not an agent)

1. Create a GitHub account or organization for PraiseLoop. Use a different account from
   the app repository, as planned.
2. Create a new **public** repository for this site (for example `praiseloop-site`).
   Do not initialise it with a README.
3. Commit the files in this directory and push the `main` branch to that repository.
4. In the repository, open **Settings → Pages**. Under **Build and deployment**, set
   **Source** to **Deploy from a branch**, choose branch **main** and folder **/ (root)**,
   then save. Wait for the first deployment to finish.
5. Under **Custom domain**, enter `praiseloop.ca` and save. The `CNAME` file already
   contains this value, so GitHub should show the domain as set.
6. Add the DNS records in Cloudflare (next section).
7. Wait for GitHub to verify the domain and issue the certificate. This can take up to a
   day. Avoid removing and re-adding the domain while it is pending.
8. When GitHub offers **Enforce HTTPS**, tick it. Then check
   `https://praiseloop.ca/`, `https://www.praiseloop.ca/`, `/privacy/`, `/terms/` and a
   deliberately missing URL.

## DNS records in Cloudflare

The domain already sends and receives mail. **Do not change or remove the existing MX,
SPF, DKIM or Resend records.** The Pages records below are additions at the apex (`@`).
They do not affect mail, which uses MX and TXT records.

| Type | Name | Content | Proxy status |
| --- | --- | --- | --- |
| A | `@` | `185.199.108.153` | DNS only (grey cloud) |
| A | `@` | `185.199.109.153` | DNS only (grey cloud) |
| A | `@` | `185.199.110.153` | DNS only (grey cloud) |
| A | `@` | `185.199.111.153` | DNS only (grey cloud) |
| CNAME | `www` | `<account>.github.io` | DNS only (grey cloud) |

- Replace `<account>` with the GitHub account or organization that owns the site
  repository. The target is the Pages hostname, not the repository name.
- Keep the records on **DNS only** until GitHub has issued the certificate and
  **Enforce HTTPS** is ticked.
- The apex must use the four A records. Do not point the apex at the `www` CNAME.
- Leave the existing Zoho mail records (MX, SPF, DKIM) and the Resend records in place.
  The root domain may have only one SPF TXT record; do not add a second one for Pages.

## Mailboxes

The site links to `hello@praiseloop.ca` and `privacy@praiseloop.ca`. Both must exist as
aliases in the Zoho Mail admin console and deliver to a mailbox someone reads. Do not
publish any other address.

## Checks

Run these from the repository root:

```sh
python3 check_site.py
python3 check_site.py --strict
```

`check_site.py` uses only the Python standard library. It checks every `.html` file for
`lang="en-CA"`, exactly one `<h1>`, a `<title>` and a meta description. It rejects
external `src`/`href` URLs (the canonical link is the only exception; `mailto:` links are
allowed), and it checks that every root-relative link and asset resolves to a real file
or directory index. It checks that `CNAME` contains exactly `praiseloop.ca` and that the
shared shell links (`/privacy/`, `/terms/`, `mailto:hello@praiseloop.ca`) appear on every
page. Without `--strict` it prints the remaining `TODO(owner)` markers; with `--strict`
it fails while any remain in a published HTML file.

Exit code 0 means every check passed. No browser or network access is used.

## Before publishing

- [ ] Every `TODO(owner)` marker is resolved. `python3 check_site.py` lists them.
- [ ] A lawyer has reviewed `/privacy/` and `/terms/`.
- [ ] `python3 check_site.py --strict` exits 0.
- [ ] The Pages deployment is green, the custom domain is verified and **Enforce HTTPS**
      is ticked.
- [ ] `hello@` and `privacy@` receive mail from an outside address.
- [ ] `/`, `/privacy/`, `/terms/` and a missing URL all load over HTTPS.
- [ ] The home page is readable at 320px wide with no horizontal scroll, and in both
      light and dark mode.
- [ ] The browser's network panel shows no requests to other sites.

## Editing

Edit the HTML or CSS directly, then run the checks and commit. There is nothing to build.
Keep to these rules:

- Static HTML and CSS only. No JavaScript, frameworks, analytics, embeds, web fonts or
  remote images.
- System fonts only.
- Root-relative links (`/privacy/`, `/styles.css`).
- No invented claims, testimonials, logos, statistics or prices.
- Use `hello@praiseloop.ca` for general contact and `privacy@praiseloop.ca` for privacy
  requests.
- When a public page is added, update `sitemap.xml` and `robots.txt` if needed.

## Known placeholders

One marker is in the published HTML today:

- `index.html`: the legal company name in the "Who runs it?" answer.

The legal pages carry their own markers (effective date, legal entity and address,
retention period, mail host and backup provider, Google review-reuse permission, and
provider processing countries). `check_site.py --strict` lists all of them.
