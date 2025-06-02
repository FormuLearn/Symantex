---
title: Merging into your main site
description: Merging 
slug: /projects/doculinkr/merge-main
sidebar_position: 7
---
# Merging Subproject Docs into the Main Site

When you manage a primary documentation repository that aggregates multiple subprojects, use the **main-site merge** command to pull in each project’s `docs/` content.

## Configuring `doculinkr.yaml`

Before merging, edit your `doculinkr.yaml` (usually generated from `init`) at the root of your main-site repo. By default it looks like:

```yaml
site_name: FormuLearn Docs
projects:
  # Example project entry; delete or replace after initial setup
  - name: ExampleProject      # (list item) a unique identifier for the project
    path: docs/ExampleProject # where to copy its docs into this site
    git_path: https://github.com/your-org/ExampleProject.git  # repo URL or local path

docusaurus:
  template: classic           # which Docusaurus template to use
```

* **`site_name`**: the title shown in your site header.
* **`projects:`**: a YAML list (each item starts with `-`) of subprojects to include.

  * `name`: identifies the project; also used for front-matter if needed.
  * `path`: the relative location under `docs/` where its Markdown files will live.
  * `git_path`: the Git repository URL or local path to clone/pull.
* **`docusaurus.template`**: (optional) specifies the scaffold theme

> **Tip:** You’ll see one example entry by default (`ExampleProject`). Replace or remove it when you add your own projects.

## Usage

Run from the **root** of your main-site Git repository (where `docusaurus.config.js` and `doculinkr.yaml` live):

```bash
doculinkr merge
```

* Reads your updated `doculinkr.yaml` configuration.
* Clones or pulls each listed subproject into a temporary folder.
* Copies their `docs/` directories into your main site’s `docs/` folder at the specified `path`.

After merging, and if it isn't already running, serve the site to preview all your documentation in one place:

```bash
doculinkr serve
```

Now, all your subprojects’ docs will appear alongside any core docs in the main site.
