# Maintenance

## Local workflow

Use Python 3.10 or newer with the standard library only:

```sh
python3 scripts/build.py
python3 scripts/build.py --check
```

The generator validates unique IDs and sources, categories, model evidence, dates, primary prompt links and all five language keys. It renders the README files, category pages and video details. `--check` fails for stale or missing generated pages and orphaned generated details. This is an offline consistency check; it does not make network requests or certify video quality.

For a removed entry, delete its generated `docs/videos/<language>/<id>.md` files before rebuilding. Keep facts in `data/videos.json`, UI strings in `locales/` and featured IDs in the index. All generated links use repository-root paths so they work from nested detail pages on GitHub.

## Before making the repository public

- Review featured videos visually and confirm each model attribution against its original source. Resolve any `upstream-index` attribution or remove the entry.
- Review translations, creator names, prompt context and media-rights records.
- Check that all original-post links and thumbnail URLs still work; source availability can change after the recorded check date.
- Inspect all five README files on GitHub, including narrow layouts and image loading.
- Run the offline consistency check and confirm CI passes at the commit being released.
- Keep the repository private until the owner chooses to change visibility. No workflow or script changes visibility or schedules a release.

## Cover assets

`assets/cover.png` is the original wide cover used by every README. `assets/social-preview.jpg` is a 1280×640 layout intended for GitHub's repository social preview setting. Merely committing that file does not configure the social preview setting.

The visual direction and generation brief are documented in [assets/README.md](../assets/README.md). Future covers should remain recognizable at README width and must not present illustrative brand art as a model output.
