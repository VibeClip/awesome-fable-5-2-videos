#!/usr/bin/env python3
"""检查展示链接、推广参数和提交说明，防止聚合页面混入外部导流。"""

import html
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = '/VibeClip/awesome-fable-5-2-videos'
ALLOWED_HOSTS = {
    'github.com', 'x.com', 'twitter.com', 'www.youtube.com', 'youtube.com',
    'video.twimg.com', 'video-s.twimg.com', 'pbs.twimg.com', 'img.shields.io',
    'api.fxtwitter.com', 'publish.twitter.com', 'higgsfield.ai',
}
TEXT_SUFFIXES = {'.md', '.json', '.py', '.yml', '.yaml'}


def main():
    issues, total = [], 0
    for path in ROOT.rglob('*'):
        if '.git' in path.parts or path.suffix not in TEXT_SUFFIXES:
            continue
        content = path.read_text()
        for raw in re.findall(r'https?://[^\s<>"\')`]+', content):
            url = html.unescape(raw).rstrip('.,;')
            if path.suffix == '.py' and ('{' in url or '}' in url):
                continue
            parsed = urlparse(url)
            total += 1
            if parsed.netloc not in ALLOWED_HOSTS:
                issues.append(f'{path.relative_to(ROOT)}: unexpected host {parsed.netloc}')
            if parsed.netloc == 'github.com' and not parsed.path.startswith(REPOSITORY + '/') and parsed.path != REPOSITORY:
                issues.append(f'{path.relative_to(ROOT)}: unrelated GitHub destination')
            keys = {key.lower() for key in parse_qs(parsed.query)}
            if any(key.startswith('utm_') for key in keys) or keys & {'affiliate', 'referral', 'aff', 'coupon', 'promo_code'}:
                issues.append(f'{path.relative_to(ROOT)}: promotional tracking parameter')
    videos = json.loads((ROOT / 'data/videos.json').read_text())['videos']
    for video in videos:
        expected = f'https://github.com{REPOSITORY}/raw/main/{video["preview_path"]}'
        if video['preview_url'] != expected:
            issues.append(video['id'] + ': preview must be hosted by this repository')
        if video['video_url'] == video['source_url'] and video['source_check']['availability'] == 'unconfirmed':
            continue
        if urlparse(video['video_url']).netloc not in ('video.twimg.com', 'video-s.twimg.com', 'www.youtube.com', 'youtube.com'):
            issues.append(video['id'] + ': full video must point to the original platform')
    messages = subprocess.check_output(['git', 'log', '--all', '--format=%B'], cwd=ROOT, text=True)
    if re.search(r'yihui|evolink|scrap|crawl|抓取|爬取|参考仓库|other repositor', messages, re.IGNORECASE):
        issues.append('Commit message contains collection-method or external-repository wording')
    if issues:
        raise SystemExit('\n'.join(sorted(set(issues))[:40]) + f'\n{len(set(issues))} unique issues')
    print(f'{len(videos)} entries; {total} links; promotion and commit-message checks: OK')


if __name__ == '__main__':
    main()
