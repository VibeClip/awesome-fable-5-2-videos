# Contributing

Share videos worth watching. Original films, motion graphics, product videos and visual explainers made with **Claude Fable 5.2** belong here. A playable game, static website or API tutorial alone does not.

## Suggest a video

[Open a video submission](https://github.com/VibeClip/awesome-fable-5-2-videos/issues/new?template=submit-video.yml) with the original creator's post, model evidence, category and an optional public prompt. Creator self-submissions are welcome. Do not upload someone else's video or screenshots to the issue.

## Add an entry by pull request

1. Add the facts to `data/videos.json`. Keep one entry per original video and use a stable lowercase ID. Copy the shape of an existing entry.
2. Write concise titles in English, Simplified Chinese, Japanese, Korean and Spanish. Translate the description; keep creator names and quoted prompts in their original language. If you need translation help, open a submission instead.
3. Link the original creator and original post. Verify the post contains a video and record the check date. An official X oEmbed response can verify a post; FxTwitter can supply video metadata. Record the model as `primary-post` only when the primary post explicitly names it. Otherwise use `upstream-index` and explain the outstanding check.
4. Supply a local looping WebP `preview_path`/`preview_url` and an original-platform `video_url`. A static thumbnail is metadata, not the gallery preview. Keep full videos at their original platform and preserve creator credits. Follow [the preview checks](docs/PREVIEWS.md); each new preview needs recorded animation evidence before it passes CI. Never invent missing prompts, generation times, costs or reproduction results.
5. Run the animation check, then `python3 scripts/build.py` and `python3 scripts/build.py --check`. Commit the index and generated pages together. No Python packages are needed.

## Translate

UI text lives in `locales/<language>.json`; video titles live alongside their facts in `data/videos.json`. For a new language, add it to `LANGS` in `scripts/build.py` and provide all titles and UI strings. Generated Markdown is not edited by hand.

## Correct or remove a listing

[Open a correction or removal request](https://github.com/VibeClip/awesome-fable-5-2-videos/issues/new?template=correction.yml). Link the entry and explain the correction. Creators may request that their thumbnail or entry be removed. Maintainers can remove the entry from the index, delete its generated detail pages and rebuild.
