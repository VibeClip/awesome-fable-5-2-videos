#!/usr/bin/env python3
"""从单一索引生成多语言动态画廊；--check 检查数据和生成文件是否同步。"""

import argparse
from datetime import date, datetime
import html
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
LANGS = ('en', 'zh-CN', 'ja', 'ko', 'es')
CATEGORIES = ('short-films', 'motion', '3d', 'product', 'explainers', 'interactive')
REPO = 'https://github.com/VibeClip/awesome-fable-5-2-videos'


def document(path):
    return f'{REPO}/blob/main/{path}'


def readme_path(lang):
    return 'README.md' if lang == 'en' else f'README.{lang}.md'


def load():
    data = json.loads((ROOT / 'data/videos.json').read_text())
    strings = {lang: json.loads((ROOT / f'locales/{lang}.json').read_text()) for lang in LANGS}
    assert data['schema_version'] == 3, 'Unsupported schema'
    date.fromisoformat(data['updated_on'])
    ids, sources, media_ids = set(), set(), set()
    for video in data['videos']:
        identifier = video['id']
        assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', identifier), identifier
        assert identifier not in ids and video['source_url'] not in sources, 'Duplicate video'
        ids.add(identifier)
        sources.add(video['source_url'])
        if video.get('native_media_id'):
            assert video['native_media_id'] not in media_ids, 'Duplicate native media'
            media_ids.add(video['native_media_id'])
        assert set(video['titles']) == set(LANGS), f'Missing translation: {identifier}'
        assert all(isinstance(title, str) and title.strip() for title in video['titles'].values())
        assert video['category'] in CATEGORIES
        assert isinstance(video['duration_seconds'], (int, float)) and 0 < video['duration_seconds'] < 3600
        assert video['model'] == 'Claude Fable 5.2'
        assert video['model_evidence'] in ('primary-post', 'upstream-index')
        assert video['creator']['name'] and video['media_rights']
        datetime.fromisoformat(video['published_at'].replace('Z', '+00:00'))
        source_check = video['source_check']
        date.fromisoformat(source_check['checked_on'])
        assert source_check['availability'] in ('available', 'unconfirmed')
        if source_check['availability'] == 'available':
            assert re.fullmatch(r'[a-f0-9]{64}', source_check['post_sha256'])
        if video['model_evidence'] == 'primary-post':
            assert source_check['availability'] == 'available' and source_check['model_named']
        urls = [video[key] for key in ('source_url', 'preview_url', 'video_url')]
        if video.get('thumbnail_url'):
            urls.append(video['thumbnail_url'])
        urls.append(video['creator']['url'])
        assert all(urlparse(url).scheme == 'https' and urlparse(url).netloc for url in urls)
        assert urlparse(video['source_url']).netloc in ('x.com', 'www.youtube.com')
        expected = f'{REPO}/raw/main/{video["preview_path"]}'
        assert video['preview_url'] == expected
        path = ROOT / video['preview_path']
        assert path.resolve().parent == (ROOT / 'assets/previews').resolve()
        assert path.is_file(), 'Missing preview asset'
        prompt = video['prompt']
        if prompt['text']:
            assert prompt['source_url'].startswith(video['creator']['url'] + '/status/'), 'Prompt needs creator primary source'
        if prompt['source_url']:
            assert urlparse(prompt['source_url']).scheme == 'https'
    assert set(data['featured_ids']) <= ids
    assert len(set(data['featured_ids'])) == len(data['featured_ids'])
    for lang, values in strings.items():
        assert set(values) == set(strings['en']), f'Missing UI translation: {lang}'
        assert len(values['categories']) == len(values['category_descriptions']) == len(CATEGORIES)
        assert len(values['tool_labels']) == len(values['tool_keywords'])
    report = json.loads((ROOT / 'data/preview-checks.json').read_text())
    datetime.fromisoformat(report['checked_at'])
    verified = {item['id']: item for item in report['previews']}
    assert len(verified) == len(report['previews']) and set(verified) == ids, 'Preview report must cover every video exactly once'
    for video in data['videos']:
        proof = verified[video['id']]
        assert proof['preview_url'] == video['preview_url'], 'Preview changed: rerun animation check'
        assert proof['status'] == 'animated' and proof['frames'] > 1
        assert proof['loop_count'] == 0 and proof['duration_ms'] > 0
        assert proof['width'] * 9 == proof['height'] * 16
        assert proof['file_sha256'] == hashlib.sha256((ROOT / video['preview_path']).read_bytes()).hexdigest()
    baseline = json.loads((ROOT / 'data/reference.json').read_text())
    by_id = {video['id']: video for video in data['videos']}
    for entry in baseline['entries']:
        assert entry['id'] in by_id, 'Coverage baseline entry missing'
        assert by_id[entry['id']]['source_url'].lower() == entry['source_url'].lower(), 'Coverage source changed'
    return data, strings


def duration(video):
    seconds = round(video['duration_seconds'])
    return f'{seconds // 60}:{seconds % 60:02d}'


def escape(value):
    return html.escape(value, quote=True)


def language_nav(strings):
    return ' · '.join(f'<a href="{document(readme_path(lang))}">{escape(strings[lang]["language"])}</a>' for lang in LANGS)


def detail_url(video, lang):
    return document(f'docs/videos/{lang}/{video["id"]}.md')


def prompt_panel(video, strings):
    prompt = video['prompt']
    if not prompt['source_url']:
        return ''
    if prompt['text']:
        body = '<blockquote>' + escape(prompt['text']).replace('\n', '<br>') + '</blockquote>'
    else:
        body = '<p>' + escape(strings['prompt_at_source']) + '</p>'
    return (f'<details><summary>{strings["prompt_expand"]}</summary>' + body +
            f'<p><a href="{escape(prompt["source_url"])}">{strings["prompt_source"]}</a></p></details>')


def card(video, lang, strings):
    title = escape(video['titles'][lang])
    author = escape(video['creator']['name'])
    watch = escape(video['video_url'])
    date_text = video['published_at'][:10]
    state = video.get('momentum', {}).get('state')
    badge = f'<b>{strings[state]}</b> · ' if state in ('rising', 'new') else ''
    archived = video['video_url'] == video['source_url'] and video['source_check']['availability'] == 'unconfirmed'
    preview_target = detail_url(video, lang) if archived else watch
    playback = strings['archived'] if archived else f'<a href="{watch}">▶ {strings["watch"]}</a>'
    return (f'<td width="33%" valign="top">\n'
            f'<a href="{preview_target}"><img src="{escape(video["preview_url"])}" '
            f'alt="{title} — @{author}" width="100%" loading="lazy"></a><br>\n'
            f'<b>{title}</b><br>\n'
            f'<sub>{badge}<a href="{escape(video["creator"]["url"])}">@{author}</a> · '
            f'{duration(video)} · {date_text}</sub><br>\n'
            f'{playback} · '
            f'<a href="{escape(video["source_url"])}">{strings["source_short"]}</a> · '
            f'<a href="{detail_url(video, lang)}">{strings["details"]}</a>\n'
            + prompt_panel(video, strings) + '\n</td>')


def gallery(videos, lang, strings):
    rows = ['<table>']
    for index in range(0, len(videos), 3):
        cells = [card(video, lang, strings) for video in videos[index:index + 3]]
        cells += ['<td width="33%"></td>'] * (3 - len(cells))
        rows.append('<tr>\n' + '\n'.join(cells) + '\n</tr>')
    return '\n'.join(rows + ['</table>'])


def category_sections(videos, lang, strings):
    sections = []
    for category, label, description in zip(CATEGORIES, strings['categories'], strings['category_descriptions']):
        entries = sorted((video for video in videos if video['category'] == category),
                         key=lambda video: video['published_at'], reverse=True)
        sections.append(f'<a id="{category}"></a>\n\n## {label} · {len(entries)}\n\n{description}\n\n'
                        + gallery(entries, lang, strings))
    return '\n\n'.join(sections)


def render(data, strings):
    outputs = {}
    videos = data['videos']
    by_id = {video['id']: video for video in videos}
    for lang, values in strings.items():
        readme = readme_path(lang)
        prompt_count = sum(bool(video['prompt']['source_url']) for video in videos)
        badges = (f'<a href="{REPO}/stargazers"><img alt="GitHub stars" '
                  f'src="https://img.shields.io/github/stars/VibeClip/awesome-fable-5-2-videos?style=flat&amp;color=c8ff00&amp;label=Star"></a> '
                  f'<img alt="{len(videos)} videos" src="https://img.shields.io/badge/videos-{len(videos)}-c8ff00"> '
                  f'<img alt="{prompt_count} prompt sources" src="https://img.shields.io/badge/prompts-{prompt_count}-a78bfa"> '
                  f'<a href="{document("LICENSE")}"><img alt="MIT" src="https://img.shields.io/badge/license-MIT-blue"></a>')
        badges = f'<a href="https://awesome.re"><img alt="Awesome" src="https://awesome.re/badge.svg"></a> ' + badges
        content = (f'<!-- Generated by scripts/build.py; edit data/ and locales/. -->\n\n'
                   f'<p align="center">{badges}</p>\n\n'
                   f'![Fable in Motion — Claude Fable 5.2 video showcase]({document("assets/cover.png")})\n\n'
                   f'<div align="center">\n<h1>Fable in Motion · Claude Fable 5.2 Videos</h1>\n'
                   f'<p><b>{escape(values["intro"])}</b></p>\n'
                   f'<p>{language_nav(strings)}</p>\n</div>\n\n'
                   f'{values["about"]}\n\n'
                   f'{values["guide_intro"].format(videos=len(videos))}\n\n')
        for highlight in values['highlights']:
            content += '- ' + highlight.format(prompts=prompt_count) + '\n'
        content += f'\n**{values["preview_hint"]}**\n\n'
        content += (f'[{values["featured"]}](#featured) · '
                    f'[{values["tools_title"]}](#techniques) · '
                    f'[{values["faq_link"]}](#guide) · '
                    f'[{values["discover_link"]}]({document("docs/DISCOVERIES.md")}) · '
                    f'[{values["submit"]}]({REPO}/issues/new?template=submit-video.yml)\n\n'
                    f'## {values["browse"]}\n\n')
        content += f'| {values["category_column"]} | {values["examples_column"]} | {values["find_column"]} |\n| :-- | --: | :-- |\n'
        for category, label, description in zip(CATEGORIES, values['categories'], values['category_descriptions']):
            total = sum(video['category'] == category for video in videos)
            content += f'| [{label}](#{category}) | {total} | {description} |\n'
        content += f'\n<a id="featured"></a>\n\n## {values["featured"]}\n\n'
        content += gallery([by_id[key] for key in data['featured_ids']], lang, values)
        content += f'\n\n**{values["cta"]}**\n\n'
        content += f'<a id="techniques"></a>\n\n## {values["tools_title"]}\n\n{values["tools_note"]}\n\n'
        content += f'| {values["tool_columns"][0]} | {values["tool_columns"][1]} |\n| :-- | :-- |\n'
        for label, keywords in zip(values['tool_labels'], values['tool_keywords']):
            content += f'| {label} | {keywords} |\n'
        content += '\n' + category_sections(videos, lang, values)
        content += f'\n\n<a id="guide"></a>\n\n## {values["faq_title"]}\n\n'
        for question, answer in values['faq']:
            content += f'### {question}\n\n{answer}\n\n'
        content += (f'[{values["contribute"]}]({document("CONTRIBUTING.md")}) · '
                    f'[JSON]({document("data/videos.json")})\n\n'
                    f'---\n\n{values["note_text"]}\n\n'
                    f'[{values["provenance"]}]({document("docs/SOURCES.md")}) · '
                    f'[{values["license"]}]({document("docs/MEDIA-RIGHTS.md")}) · '
                    f'{values["updated"]}: {data["updated_on"]}\n')
        outputs[readme] = content
        outputs[f'docs/collections/{lang}.md'] = (
            f'<!-- Generated by scripts/build.py. -->\n\n# {values["all"]}\n\n'
            f'[{values["back"]}]({document(readme)})\n\n'
            f'{values["preview_hint"]}\n\n' + category_sections(videos, lang, values) + '\n')
        for video in videos:
            evidence = values['primary'] if video['model_evidence'] == 'primary-post' else values['secondary']
            check = video['source_check']
            availability = values['available'] if check['availability'] == 'available' else values['unconfirmed']
            archived = video['video_url'] == video['source_url'] and check['availability'] == 'unconfirmed'
            image = f'![{escape(video["titles"][lang])}]({video["preview_url"]})'
            image = image if archived else f'[{image}]({video["video_url"]})'
            playback = f'**{values["archived"]}**' if archived else f'**[▶ {values["watch"]}]({video["video_url"]})**'
            text = (f'<!-- Generated by scripts/build.py. -->\n\n# {video["titles"][lang]}\n\n'
                    f'[{values["back"]}]({document(readme)})\n\n'
                    f'{image}\n\n'
                    f'{playback} · '
                    f'[{values["source"]}]({video["source_url"]})\n\n'
                    f'[{video["creator"]["name"]}]({video["creator"]["url"]}) · '
                    f'{duration(video)} · {video["published_at"][:10]}\n\n'
                    f'## {values["prompt"]}\n\n')
            prompt = video['prompt']
            if prompt['text']:
                text += values['prompt_note'] + '\n\n'
                text += '\n'.join('> ' + line for line in prompt['text'].splitlines()) + '\n\n'
            elif prompt['source_url']:
                text += values['prompt_at_source'] + '\n\n'
            else:
                text += values['no_prompt'] + '\n\n'
            if prompt['source_url']:
                text += f'[{values["prompt_source"]}]({prompt["source_url"]})\n\n'
            text += (f'<details>\n<summary>{values["source_notes"]}</summary>\n\n'
                     f'- {values["evidence"]}: {evidence}\n'
                     f'- {values["checked"]}: {check["checked_on"]} — {availability}\n\n'
                     f'{values["not_reproduced"]}\n\n'
                     f'[{values["license"]}]({document("docs/MEDIA-RIGHTS.md")})\n\n</details>\n')
            outputs[f'docs/videos/{lang}/{video["id"]}.md'] = text
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data, strings = load()
    outputs = render(data, strings)
    stale = []
    for name, content in outputs.items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_text() != content:
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    for path in (*ROOT.glob('docs/videos/*/*.md'), *ROOT.glob('docs/collections/*.md')):
        if path.relative_to(ROOT).as_posix() not in outputs:
            stale.append(str(path.relative_to(ROOT)))
    if stale:
        raise SystemExit('Generated files out of sync: ' + ', '.join(stale))
    print(f'{len(data["videos"])} videos; {len(LANGS)} languages; {len(outputs)} generated pages: OK')


if __name__ == '__main__':
    main()
