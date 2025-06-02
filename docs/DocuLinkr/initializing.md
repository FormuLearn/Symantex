---
title: Initializing
description: Initializing your Documentation site with DocuLinkr
slug: /projects/doculinkr/initializing
sidebar_position: 2
---

# Initializing Your DocuLinkr Site

The `init` command scaffolds a fresh Docusaurus site with DocuLinkr integration. All commands must be run from the **root** of a Git repository.

## 1. Run `doculinkr init`

```bash
# From your repo root, choose a site directory name (e.g. "my-docs-site")
doculinkr init my-docs-site
```

* `my-docs-site` will be created as a subfolder containing your new Docusaurus project.
* When prompted, we reccomend you select the 'Javascript' option to build docusaurus, as it is the most rigorously tested.

## 2. Explore the Generated Files

Inside `my-docs-site/`, you’ll find:

* `docs/` – a folder ready for your custom Markdown files.
* `docusaurus.config.js` – site configuration (title, tagline, theme, plugins).
* `src/` – React source:

  * `src/css/custom.css` – add general CSS overrides (site-wide styling).
  * `src/pages/index.js` – customize your homepage layout.
  * `src/components/HomepageFeatures/index.js` – tweak feature cards on the homepage.
* `static/img/` – place custom logos/favicons here.

## 3. Serve & Live-Reload

Start the local dev server with:

```bash
doculinkr serve
```

Ensure that you are still in the root of your git repository for your site.

* This should install all npm requirements by default. If not, try to use `--install` to run `npm install` automatically on first serve.
* Visit `http://localhost:3000/` to see your site.
* Edit files under `src/` or add docs in `docs/`—the site will hot-reload.

## 4. Customize Your Site

* **Appearance:** tweak `src/css/custom.css`, `src/pages/index.js`, and `src/components/HomepageFeatures/index.js`.
* **Assets:** drop images into `static/img/` and reference them in your Markdown or config.
* **Configuration:** update `docusaurus.config.js` to change titles, taglines, URLs, and social links.

## 5. Commit & Push

Once you’re happy:

```bash
git add my-docs-site
git commit -m "Initialize DocuLinkr site"
git push origin main
```

Pushing makes your site repo ready for linking subprojects with `doculinkr link`.
