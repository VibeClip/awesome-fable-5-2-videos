# Dynamic previews

The gallery embeds looping animated WebP images in three-column HTML tables. A preview links to its full video on the original platform. Static poster images are never used as gallery substitutes.

```html
<td width="33%" valign="top">
  <a href="ORIGINAL_FULL_VIDEO">
    <img src="OUR_REPOSITORY_PREVIEW.webp" width="100%" loading="lazy" alt="Video title — creator">
  </a>
  <br><b>Video title</b>
  <br><sub>Creator · duration · date</sub>
  <br>Watch · Source · Prompt / Details
</td>
```

Previews use a 416×234 canvas and preserve the source aspect ratio with padding. They are short excerpts, not full video mirrors. Fresh excerpts use three short portions of the original clip to give a useful view of its motion. Archived excerpts are marked when the primary source is unavailable.

## Before the first push

```sh
python3 scripts/check_previews.py --local
python3 scripts/build.py
python3 scripts/build.py --check
python3 scripts/release_check.py
```

The preview check parses actual RIFF, `ANIM` and `ANMF` chunks. It rejects static images, truncated files, finite loops and missing assets. Evidence records dimensions, animation frames, loop duration and a content hash for every preview.

## After pushing

```sh
python3 scripts/check_previews.py
```

The remote check compares each local animated media object with its exact GitHub blob SHA and confirms the corresponding image is present in GitHub's rendered README. It saves verification metadata to `data/preview-checks.json`. Local checks remain offline; the post-push check uses the authenticated `gh` connection.

Browsers or accessibility settings can pause image animation. The underlying files remain animated, and full-video links provide the original playback route.
