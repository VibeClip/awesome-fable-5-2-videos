#!/usr/bin/env python3
"""从原始视频生成六秒内的循环预览；不保存完整视频到仓库。"""

import argparse
import io
import json
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, FPS = 416, 234, 6
MAX_BYTES = 80 * 1024 * 1024


def download(url, path):
    if urlparse(url).netloc not in ('video.twimg.com', 'video-s.twimg.com'):
        raise ValueError('Use the original platform video URL or provide --input')
    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30) as response, path.open('wb') as output:
        total = 0
        while block := response.read(256 * 1024):
            total += len(block)
            if total > MAX_BYTES:
                raise ValueError('Source exceeds 80 MiB preview budget')
            output.write(block)


def encode(source, output, duration):
    segment = min(1.8, duration)
    positions = [(duration - segment) * value for value in (.08, .42, .76)] if duration > 5 else [0]
    frames = []
    for start in positions:
        filters = (f'fps={FPS},scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,'
                   f'pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:black,setsar=1')
        command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss', str(start), '-i', str(source),
                   '-t', str(segment), '-an', '-vf', filters, '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1']
        raw = subprocess.run(command, check=True, capture_output=True, timeout=60).stdout
        frame_size = WIDTH * HEIGHT * 3
        frames += [Image.frombytes('RGB', (WIDTH, HEIGHT), raw[index:index + frame_size])
                   for index in range(0, len(raw) - frame_size + 1, frame_size)]
    if len(frames) < 2:
        raise ValueError('Not enough animation frames')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.webp.tmp')
    frames[0].save(temporary, format='WEBP', save_all=True, append_images=frames[1:],
                   duration=167, loop=0, quality=52, method=2)
    temporary.replace(output)
    print(f'{output.relative_to(ROOT)}: {len(frames)} frames, {output.stat().st_size} bytes')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('id', help='Existing entry ID in data/videos.json')
    parser.add_argument('--input', type=Path, help='Local original video, when already available')
    args = parser.parse_args()
    videos = json.loads((ROOT / 'data/videos.json').read_text())['videos']
    video = next((entry for entry in videos if entry['id'] == args.id), None)
    if not video:
        raise SystemExit('Unknown entry ID')
    output = ROOT / video['preview_path']
    if output.resolve().parent != (ROOT / 'assets/previews').resolve():
        raise SystemExit('Preview path escapes the asset directory')
    with tempfile.TemporaryDirectory(prefix='fable-preview-') as directory:
        source = args.input or Path(directory) / 'source.mp4'
        if not args.input:
            if urlparse(video['video_url']).netloc in ('www.youtube.com', 'youtube.com'):
                subprocess.run(['yt-dlp', '--no-playlist', '--no-warnings', '--quiet',
                                '-f', 'best[height<=480]/best', '--max-filesize', '80M',
                                '-o', str(source), video['video_url']], check=True, timeout=120)
            else:
                download(video['video_url'], source)
        encode(source, output, float(video['duration_seconds']))


if __name__ == '__main__':
    main()
