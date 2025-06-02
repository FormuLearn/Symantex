---
title: Linking
description: Linking projects to your Documentation site with DocuLinkr
slug: /projects/doculinkr/linking
sidebar_position: 3
---
# Linking Your Project to a DocuLinkr Site

All `doculinkr` commands must be run from the **root** of your project’s Git repository.

## 1. Start with Your Repository

Your project repo should look something like:

```
project-repo/
├── src/           # your application code
├── tests/         # your tests
└── (no docs/ yet)
```

## 2. Run the `link` Command

Point your project at an existing DocuLinkr main site:

```bash
cd project-repo
doculinkr link --site https://github.com/YourOrg/MainDocsRepo.git
```

* `--site` accepts a Git URL or local path to the main Docusaurus site.
* This clones (or pulls) that site into a cache folder you shouldn’t edit: `.doculinkr/main/`.

## 3. Inspect the New Structure

After running, your repo root will include:

```
project-repo/
├── src/                   # your application code (unchanged)
├── tests/                 # your tests (unchanged)
├── docs/                  # YOUR project’s Markdown docs
└── .doculinkr/            # internal cache (DO NOT EDIT)
    └── main/              # cloned main Docusaurus site
```

* **`docs/`** is where you write all your documentation in Markdown.
* **`.doculinkr/main/`** holds the cloned main site structure with your docs injected; you should never modify it directly.

## 4. Write or Scaffold Your Docs

* **Write directly:** create or edit `docs/*.md` to author your docs.
* **Use `startdocs`:** in the next section, we'll show you how to use the `doculinkr startdocs` command to create a base structure.
