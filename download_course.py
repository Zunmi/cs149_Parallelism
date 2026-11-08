#!/usr/bin/env python3
"""Download the public CS149 Fall 2025 materials listed in materials.json."""
import hashlib
import concurrent.futures
import json
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import urllib.error
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / 'materials.json'
REPORT = ROOT / 'download_status.json'
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
SOURCE_REPLACEMENTS = {
    'https://awsdocs-neuron.readthedocs-hosted.com/en/latest/nki/tutorials/matrix_multiplication.html':
        'https://awsdocs-neuron.readthedocs-hosted.com/en/v2.26.0/general/nki/tutorials/matrix_multiplication.html',
    'https://awsdocs-neuron.readthedocs-hosted.com/en/latest/tools/neuron-sys-tools/neuron-profile-user-guide.html':
        'https://awsdocs-neuron.readthedocs-hosted.com/en/v2.26.0/tools/neuron-sys-tools/neuron-profile-user-guide.html',
    'https://awsdocs-neuron.readthedocs-hosted.com/en/latest/nki/tutorials':
        'https://awsdocs-neuron.readthedocs-hosted.com/en/v2.26.0/general/nki/tutorials.html',
}


def checked_path(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT) or path == ROOT:
        raise ValueError(f'Unsafe destination: {relative}')
    return path


def validate(path, suffix):
    with path.open('rb') as stream:
        start = stream.read(1024)
        if suffix == '.pdf':
            if not start.startswith(b'%PDF-'):
                raise ValueError('Response is not a PDF')
            stream.seek(max(0, path.stat().st_size - 2048))
            if b'%%EOF' not in stream.read():
                raise ValueError('PDF is incomplete')
        elif suffix == '.html':
            if not re.search(br'<(?:!doctype|html|head|body)\b', start, re.I):
                raise ValueError('Response is not an HTML page')
    if suffix == '.zip':
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f'Corrupt ZIP entry: {bad}')


def sha256(path):
    with path.open('rb') as stream:
        digest = hashlib.sha256()
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(asset):
    target = checked_path(asset['path'])
    if target.exists():
        validate(target, target.suffix)
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        temporary = None
        try:
            url = SOURCE_REPLACEMENTS.get(asset['url'], asset['url'])
            request = urllib.request.Request(url, headers={'User-Agent': 'CS149-Study-Archive/1.0'})
            expected = None
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as output:
                temporary = Path(output.name)
            try:
                with OPENER.open(request, timeout=60) as response, temporary.open('wb') as output:
                    expected = response.headers.get('Content-Length')
                    shutil.copyfileobj(response, output, 1024 * 1024)
            except urllib.error.HTTPError as error:
                if error.code != 403:
                    raise
                subprocess.run(['curl', '--noproxy', '*', '--fail', '-sS', '-L',
                                '--connect-timeout', '15', '--max-time', '120',
                                '--output', str(temporary), '--url', url], check=True)
            if expected and temporary.stat().st_size != int(expected):
                raise ValueError('Incomplete HTTP response')
            validate(temporary, target.suffix)
            temporary.rename(target)
            return target
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def validate_member(name, mode, expected_root):
    parts = PurePosixPath(name)
    if (parts.is_absolute() or '..' in parts.parts or '\\' in name
            or not parts.parts or parts.parts[0] != expected_root
            or stat.S_ISLNK(mode)):
        raise ValueError(f'Unsafe ZIP entry: {name}')


def extract_repo(asset, archive_path):
    destination = checked_path(asset['extract_to'])
    digest = sha256(archive_path)
    marker = destination / '.cs149-archive-sha256'
    if destination.exists():
        if marker.is_file() and marker.read_text().strip() == digest:
            return
        raise ValueError(f'{destination} already exists; refusing to overwrite your work')
    staging = Path(tempfile.mkdtemp(prefix='.cs149-extract-', dir=destination.parent))
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                validate_member(member.filename, member.external_attr >> 16, asset['archive_root'])
            archive.extractall(staging)
            for member in archive.infolist():
                if not member.is_dir() and (member.external_attr >> 16) & 0o111:
                    (staging / member.filename).chmod(0o755)
        extracted = staging / asset['archive_root']
        (extracted / marker.name).write_text(digest + '\n')
        extracted.rename(destination)
    finally:
        shutil.rmtree(staging)


def discover_readings(assets):
    known = {urllib.parse.urldefrag(a['url'])[0] for a in assets}
    hosts = {'ispc.github.io', 'docs.nvidia.com', 'developer.nvidia.com',
             'awsdocs-neuron.readthedocs-hosted.com', 'isocpp.org',
             'triton-lang.org', 'tilelang.com'}
    for markdown in sorted((ROOT / 'programming_assignments').rglob('*.md')):
        for url in re.findall(r'https?://[^\s<>"\x27\x60)]+', markdown.read_text(errors='replace')):
            url = urllib.parse.urldefrag(url.rstrip('.,;'))[0]
            parsed = urllib.parse.urlsplit(url)
            if parsed.hostname not in hosts or url in known:
                continue
            suffix = PurePosixPath(parsed.path).suffix.lower()
            if suffix not in {'', '.html', '.htm', '.pdf'}:
                continue
            known.add(url)
            basename = re.sub(r'[^A-Za-z0-9_.-]', '_', PurePosixPath(parsed.path).name or 'index')
            extension = '.pdf' if suffix == '.pdf' else '.html'
            basename = basename[:100] if basename.endswith(extension) else basename[:100] + extension
            key = hashlib.sha256(url.encode()).hexdigest()[:10]
            assets.append({'category': 'readings', 'title': f'Reference from {markdown.relative_to(ROOT)}',
                           'url': url, 'path': f'readings/references/{key}_{basename}'})


def main():
    assets = json.loads(MANIFEST.read_text())['assets']
    if '--self-test' in sys.argv:
        assert len([a for a in assets if a['category'] == 'lectures']) == 18
        assert len({a['path'] for a in assets}) == len(assets)
        for asset in assets:
            checked_path(asset['path'])
            assert asset['url'].startswith('https://')
        validate_member('repo-main/README.md', stat.S_IFREG, 'repo-main')
        for name, mode in [('repo-main/../escape', stat.S_IFREG), ('/escape', stat.S_IFREG),
                           ('other/README.md', stat.S_IFREG), ('repo-main/link', stat.S_IFLNK)]:
            try:
                validate_member(name, mode, 'repo-main')
            except ValueError:
                continue
            raise AssertionError(name)
        print('Self-check passed: manifest and ZIP path validation.')
        return 0
    records = []
    try:
        with OPENER.open(assets[-1]['url'], timeout=15) as response:
            response.read(1)
    except Exception as error:
        REPORT.write_text(json.dumps({'complete': False, 'network_error': str(error),
                                     'downloaded': 0, 'pending': len(assets)}, ensure_ascii=False, indent=2) + '\n')
        print(f'Network unavailable: {error}\nNo downloads attempted. Check your network/proxy and rerun.', file=sys.stderr)
        return 1
    for directory in ['lectures', 'written_assignments', 'programming_assignments', 'readings', 'course_pages']:
        checked_path(directory).mkdir(exist_ok=True)
    def download(asset):
        record = {'path': asset['path'], 'url': asset['url']}
        try:
            path = fetch(asset)
            if 'extract_to' in asset:
                extract_repo(asset, path)
            record.update(status='ok', bytes=path.stat().st_size, sha256=sha256(path))
        except Exception as error:
            record.update(status='failed', error=str(error))
        return record

    def download_batch(batch):
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            futures = [pool.submit(download, asset) for asset in batch]
            for future in concurrent.futures.as_completed(futures):
                record = future.result()
                records.append(record)
                message = f'[{len(records)}] {record["status"].upper()} {record["path"]}'
                print(message + (': ' + record['error'] if 'error' in record else ''), flush=True)
                REPORT.write_text(json.dumps({'complete': False, 'files': records}, ensure_ascii=False, indent=2) + '\n')

    download_batch([asset for asset in assets if asset['category'] != 'readings'])
    discover_readings(assets)
    download_batch([asset for asset in assets if asset['category'] == 'readings'])
    failed = sum(r['status'] != 'ok' for r in records)
    REPORT.write_text(json.dumps({'complete': not failed, 'files': records}, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(records) - failed} saved/verified; {failed} failed. See download_status.json.')
    return int(bool(failed))


if __name__ == '__main__':
    raise SystemExit(main())
