# Maintenance

## Content updates

The maintained index is `data/videos.json`. Keep the coverage baseline in `data/reference.json`, with only original-creator source links. Five-language UI strings live in `locales/`; video titles live alongside their facts. Do not hand-edit generated README, category or detail pages. Preserve the opening Awesome badge, original cover, full introduction, six-category navigation and technique/use-case keyword index in all five languages. Public prompts belong in expandable panels on their works; do not reintroduce a duplicate prompt list at the bottom. Keep broad search vocabulary natural, and only attach specific tool claims to an entry when the creator disclosed them.

Each entry needs a stable ID, creator, original post, model evidence, current source status and a local `assets/previews/<id>.webp` asset. Use original platform URLs for full-video playback. An unavailable source stays visibly marked and is not featured as a playable full video. Native media IDs prevent reposts being counted as new works.

## Prepare a preview

Offline validation needs Python 3.10+ and its standard library. Creating new previews additionally needs FFmpeg and the packages in `scripts/media-requirements.txt`; YouTube originals can use yt-dlp. Use an interpreter with those dependencies and a valid system CA bundle.

```sh
python3 scripts/make_preview.py ENTRY_ID
python3 scripts/check_previews.py --local
python3 scripts/build.py
python3 scripts/build.py --check
python3 scripts/release_check.py
```

`make_preview.py` downloads a bounded temporary source, extracts short sections, preserves the aspect ratio and encodes an infinite-loop animated WebP. It cleans up the full temporary source automatically. `--input /absolute/path/video.mp4` uses an already available original video.

After pushing, run `python3 scripts/check_previews.py` to match animated assets to their actual GitHub objects and verify the README includes them. Commit updated verification metadata, then check CI at that resulting commit. The remote check is distinct from compilation or a browser playback test.

## Curation and momentum

Search beyond the baseline. Discover original posts using several languages and creator threads; verify model attribution and a real video attachment. Separate generated films, scene recordings, interactive demos and mixed-tool workflows. Exclude generic model news, reposts and content from older model versions from the additional-video count.

Record engagement with UTC timestamps. Only repeated observations establish measured growth. A single observation can support an age-adjusted estimate, but cannot be described as an observed increase. Keep the selection reason and unresolved evidence in the discovery review. Do not create artificial trending labels from cumulative likes alone.

## Link and commit review

The gallery and index use only this repository's preview URLs and original creator/platform URLs. Do not copy promotional wrappers, collection-site links, referral parameters, ads, third-party hosting destinations or discount offers. The external comparison source is configured in the scheduled task, not in the public catalog.

`release_check.py` checks outgoing destinations, promotional parameters, local media URLs and commit-message wording. Use short result-oriented commit messages. Retain any still-applicable license notice in the centralized notice file; removing a promotional link is different from removing a required notice.

## Release and ongoing updates

- Confirm complete baseline coverage, additional unique discoveries and no duplicate native media IDs.
- Inspect animated previews and verify source-status labels, translations, creator names and prompt context.
- Resolve or clearly mark uncertain model/media records. Do not silently drop baseline entries.
- Run animation, generation, promotion and commit checks; confirm CI passes at the release commit.
- The owner authorized public release on 2026-11-10. Keep the repository public during ongoing updates; no script or scheduled task changes visibility automatically.

Cover and optional social-preview artwork remain in `assets/`. Committing a social-preview file does not upload it to the repository's social-preview setting.
