---
title: Getting Started
description: Quickstart guide for DocuLinkr
slug: /projects/doculinkr/getting-started
sidebar_position: 1
---

## Getting Started

> **Note:** All `doculinkr` commands must be run from the **root** of a Git repository.

1. **Install** from PyPI:

   ```bash
   pip install doculinkr
   ```

2. **Initialize** a new Docusaurus site (from your repo root):

   ```bash
   doculinkr init my-docs-site
   ```

   This creates a fresh Docusaurus scaffold with DocuLinkr wired in, plus an example `docs/` folder.

3. **Link** your subproject (also from its Git repo root) into an existing site:

   ```bash
   cd my-docs-site
   doculinkr link --site https://github.com/YourOrg/MainDocsRepo.git
   ```

   This renders a `docs/` folder in your initialized site where you can add or edit your project’s documentation. Try to only write documentation for the project in it's associated git repository to avoid anything from being overwritten when merging.

4. **Serve** the site for live preview (run from the repo root of either a main site or a linked subproject):

   ```bash
   doculinkr serve
   ```

   Open `http://localhost:3000/` in your browser to view and hot‑reload as you edit the `docs/` files.

5. **Write** your custom docs in the generated `docs/` folder of your project —everything you save there will appear in your merged site.

6. **Configure** your doculinkr.yaml to list all subprojects (run from the main site’s Git repo root):

    ```yaml
    projects:
    - name: ExampleProject
        path: docs/ExampleProject
        git_path: https://github.com/YourOrg/ExampleProject.git
    - name: AnotherProject
        path: docs/AnotherProject
        git_path: ../AnotherRepo
    ```

    After saving doculinkr.yaml, run:

    ```bash
    doculinkr merge
    ```

    This reads your updated configuration and pulls each project’s docs/ into the main site.

That's all—you now have a Git-root–based workflow for initializing, linking, serving, authoring, and merging documentation with DocuLinkr.—you now have a Git-root–based workflow for initializing, linking, serving, authoring, and merging documentation with DocuLinkr.
