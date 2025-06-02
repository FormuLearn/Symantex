---
title: Merging into subprojects
description: Merging 
slug: /projects/doculinkr/merge-sub
sidebar_position: 6
---

---

id: merge-sub
title: Subproject Merge (`--site`)
----------------------------------

# Merging Updates from the Main Site into a Subproject

When you’ve linked a subproject and want to pull in the latest styling, layout, or index-page updates from the main DocuLinkr site, use the **subproject merge** command.

## Usage

Run from the **root** of your linked project repository:

```bash
doculinkr merge --site https://github.com/YourOrg/MainDocsRepo.git
```

* `--site` can be a Git URL or local path to the main site.
* This command refreshes `.doculinkr/main/` with any new commits from the main repository.
* It re-injects the symlink-docs plugin and re-links your `docs/` folder, so you see up-to-date styles, homepage tweaks, and configuration.

If you aren't already, serve locally to preview the changes:

```bash
doculinkr serve --site-name <your-site-name>
```

To see more about serving, see [Serving](/docs/projects/doculinkr/serving)

Your local project will now reflect any updates (CSS, index page components, config changes) made in the main site.

---

Ready to merge your own docs back into the main site? See the main-site merge guide.
