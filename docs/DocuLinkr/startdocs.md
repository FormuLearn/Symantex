---
title: Startdocs
description: Scaffolding documentation with doculinkr startdocs
slug: /projects/doculinkr/startdocs
sidebar_position: 4
---

# `doculinkr startdocs`

Use this command to quickly scaffold a documentation folder for a new subproject under your `docs/` directory. It saves you from creating boilerplate files and lets you focus on writing content.

## Usage

Run from the **root** of your project’s Git repository:

```bash
doculinkr startdocs --proj-name YourProjectName
```

* `--proj-name` (or `-n`) specifies the folder name under `docs/`.

## What It Does

1. **Ensures** `docs/` exists (creates it if missing).
2. **Creates** `docs/YourProjectName/` unless it already exists.
3. **Renders** two markdown templates into that folder:

   * `index.md` with front-matter and a brief introduction.
   * `getting_started.md` outlining basic installation and usage.

## After Scaffolding

* You can immediately edit the generated `docs/YourProjectName/index.md` and `getting_started.md` to add project-specific details.
* Add additional markdown files in `docs/YourProjectName/` as needed.

Example directory structure after running:

```
project-repo/
└── docs/
    └── YourProjectName/
        ├── index.md
        └── getting_started.md
```

Now, when you run `doculinkr merge` from your main site, these pages will be included automatically.

**In the next section, we'll show you how to use `doculinkr serve` to locally serve your site from both the main site, and your local projects**
