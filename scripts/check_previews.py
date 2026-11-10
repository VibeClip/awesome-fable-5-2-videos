#!/usr/bin/env python3
"""验证本仓库短预览的动画帧，并核对 GitHub 上保存的媒体对象。"""

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = 'VibeClip/awesome-fable-5-2-videos'


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'img':
            self.sources.extend(values.get(key, '') for key in ('src', 'data-canonical-src'))


def inspect_webp(content):
    if content[:4] != b'RIFF' or content[8:12] != b'WEBP':
        raise ValueError('Expected WebP bytes')
    if int.from_bytes(content[4:8], 'little') + 8 != len(content):
        raise ValueError('Incomplete RIFF file')
    offset, frames, duration_ms = 12, 0, 0
    loop_count, width, height = None, None, None
    while offset + 8 <= len(content):
        kind = content[offset:offset + 4]
        size = int.from_bytes(content[offset + 4:offset + 8], 'little')
        chunk = content[offset + 8:offset + 8 + size]
        if len(chunk) != size:
            raise ValueError('Truncated WebP chunk')
        if kind == b'VP8X' and len(chunk) >= 10:
            width = int.from_bytes(chunk[4:7], 'little') + 1
            height = int.from_bytes(chunk[7:10], 'little') + 1
        if kind == b'ANIM' and len(chunk) >= 6:
            loop_count = int.from_bytes(chunk[4:6], 'little')
        if kind == b'ANMF' and len(chunk) >= 16:
            frames += 1
            duration_ms += int.from_bytes(chunk[12:15], 'little')
        offset += 8 + size + (size % 2)
    if frames < 2 or loop_count != 0 or duration_ms <= 0 or not width or not height:
        raise ValueError('Expected multiple frames and an infinite animation loop')
    return dict(frames=frames, duration_ms=duration_ms, width=width, height=height,
                loop_count=loop_count, bytes=len(content))


def github_blob_sha(content):
    header = f'blob {len(content)}\0'.encode()
    return hashlib.sha1(header + content).hexdigest()


def github(path, accept=None):
    command = ['gh', 'api']
    if accept:
        command += ['-H', 'Accept: ' + accept]
    return subprocess.check_output(command + [path], text=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local', action='store_true', help='Check local bytes before the first push')
    args = parser.parse_args()
    remote, rendered = {}, None
    if not args.local:
        tree = json.loads(github(f'repos/{REPO}/git/trees/main?recursive=1'))
        if tree.get('truncated'):
            raise SystemExit('GitHub tree is truncated')
        remote = {item['path']: item['sha'] for item in tree['tree'] if item['type'] == 'blob'}
        rendered = Images()
        rendered.feed(github(f'repos/{REPO}/readme', 'application/vnd.github.html+json'))
    videos = json.loads((ROOT / 'data/videos.json').read_text())['videos']
    results, failures = [], []
    for video in videos:
        result = {'id': video['id'], 'preview_url': video['preview_url']}
        try:
            path = ROOT / video['preview_path']
            if path.resolve().parent != (ROOT / 'assets/previews').resolve():
                raise ValueError('Preview path escapes its asset directory')
            content = path.read_bytes()
            result.update(inspect_webp(content))
            result['file_sha256'] = hashlib.sha256(content).hexdigest()
            result['blob_sha'] = github_blob_sha(content)
            if not args.local:
                if remote.get(video['preview_path']) != result['blob_sha']:
                    raise ValueError('GitHub media object does not match checked local bytes')
                if not any(video['preview_path'] in source for source in rendered.sources):
                    raise ValueError('Animated preview is missing from GitHub-rendered README')
            result['status'] = 'animated'
        except Exception as error:
            result.update(status='failed', error=str(error))
            failures.append(result)
        results.append(result)
    method = 'Local WebP RIFF ANIM/ANMF chunks' if args.local else 'WebP animation bytes matched to GitHub blob SHA and rendered README images'
    (ROOT / 'data/preview-checks.json').write_text(json.dumps({
        'checked_at': datetime.now(timezone.utc).isoformat(), 'method': method,
        'previews': results}, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(results) - len(failures)}/{len(results)} previews: animated, infinite loop, matching media objects')
    for item in failures:
        print(item['id'], item['error'])
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
