---
title: Serving
description: Locally serving your Documentation site with DocuLinkr
slug: /projects/doculinkr/serving
sidebar_position: 5
---

# `doculinkr serve`

Serve your merged Docusaurus site locally with live-reloading.

## Usage

Run from the **root** of your Git repository (main site or linked subproject):

```bash
doculinkr serve [--install] [--site-name SITE_NAME]
```

* By default, if `node_modules/` is missing, dependencies are installed automatically.
* Use `--install` to force running `npm install` before starting.
* If you are in a subproject, you will need to use `--site-name <site-name>`, where site-name is the name you initialized your main site with. You can also view this name under `.doculinkr/main`

## Features

* **Live Reload**: Edits to `docs/`, `src/`, or configuration files instantly refresh the browser.
* **Unified Serve**: Works in both main-site mode and subproject mode. In subproject mode, you **as of version 0.1.0**, must specify the site-name. If you don't remember it, you can see the site name under `.doculinkr/main` (run `ls .doculinkr/main` to see the options).  

Now visit `http://localhost:3000/` to preview your documentation as you edit files.
