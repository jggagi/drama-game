#!/usr/bin/env python3
"""Resume Qwen Next auditions without placing signed URLs or keys in Git.

Default runs recover the paid narrator before synthesizing remaining lines.
--new-probe explicitly permits a new narrator only if its cache is missing or
has a known expired URL, after a key-free OSS connectivity check. All responses,
WAVs and metadata belong in --work-dir, outside the project and this script.
Technical decoding never certifies the transcript or character voice.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

MODEL = 'qwen-audio-3.1-tts-next'
ENDPOINT = 'https://ws-zf7l1ljexja2bd6z.cn-beijing.maas.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer'
DOWNLOAD_HOST = 'dashscope-result-bj.oss-cn-beijing.aliyuncs.com'


class Stop(Exception):
    pass


def emit(**values):
    print(json.dumps(values, ensure_ascii=False), flush=True)


def stop(reason, **values):
    emit(status='stopped', reason=reason, **values)
    raise Stop()


def read_json(path):
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        stop('missing_or_invalid_json', file=path.name)
    return data


def write_json(path, data):
    temp = path.with_name(path.name + '.part')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temp.chmod(0o600)
    temp.replace(path)


def digest(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def validate_request(payload, row, require_direction=True):
    if not isinstance(payload, dict) or payload.get('model') != MODEL:
        stop('wrong_request_model', id=row['id'])
    inp = payload.get('input', {})
    prompt = inp.get('text_prompt', '')
    if not isinstance(prompt, str) or row['text'] not in prompt:
        stop('original_text_missing', id=row['id'])
    if require_direction and row['direction'] not in prompt:
        stop('direction_missing', id=row['id'])
    if require_direction:
        original = prompt.rsplit('<原台词>', 1)[-1].split('</原台词>', 1)[0]
        if '<原台词>' not in prompt or '</原台词>' not in prompt or original != row['text']:
            stop('tagged_original_text_mismatch', id=row['id'])
    if any(k in inp for k in ('voice', 'instructions')):
        stop('old_model_fields_present', id=row['id'])
    if any(inp.get(k) != v for k, v in {'format': 'wav', 'sample_rate': 24000,
                                      'channels': 1, 'volume': 50, 'rate': 1.0}.items()):
        stop('unexpected_audio_request_settings', id=row['id'])
    if not isinstance(inp.get('seed'), int) or 'http://' in prompt or 'https://' in prompt:
        stop('unsafe_or_invalid_request', id=row['id'])


def fetch(url, payload=None):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
        stop('unsafe_url', host=parts.hostname)
    headers = {}
    body = None
    if payload is not None:
        key = os.environ.get('DASHSCOPE_API_KEY')
        if not key:
            stop('DASHSCOPE_API_KEY_missing')
        headers = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}
        body = json.dumps(payload, ensure_ascii=False).encode()
    request = urllib.request.Request(url, data=body, headers=headers)
    # urllib inherits proxy settings and performs normal CA/TLS verification.
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as error:
        return error.code, error.read(), dict(error.headers)
    except (urllib.error.URLError, OSError) as error:
        stop('network_error', host=parts.hostname, error_type=type(error).__name__,
             proxy_connect_denied='403' in str(error))


def check_download_access():
    status, body, headers = fetch('https://' + DOWNLOAD_HOST + '/')
    server = next((v for k, v in headers.items() if k.lower() == 'server'), '')
    oss = 'aliyunoss' in server.lower() or (
        b'<RequestId>' in body and b'<HostId>' in body and
        (b'<Code>AccessDenied</Code>' in body or b'<Code>BucketAccessDenied</Code>' in body))
    if status not in (200, 403) or not oss:
        stop('download_host_not_confirmed_reachable', host=DOWNLOAD_HOST,
             http_status=status, aliyun_oss=oss)
    emit(stage='download_host_check', host=DOWNLOAD_HOST, http_status=status,
         aliyun_oss=True, authorization_sent=False)


def decode(path):
    for binary in ('ffmpeg', 'ffprobe'):
        if not shutil.which(binary):
            stop('required_tool_missing', tool=binary)
    result = subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path),
                             '-f', 'null', '-'], capture_output=True)
    if result.returncode:
        stop('audio_decode_failed', file=path.name)
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                             '-of', 'json', str(path)], capture_output=True, text=True)
    if result.returncode:
        stop('audio_probe_failed', file=path.name)
    data = json.loads(result.stdout)
    stream = next((s for s in data.get('streams', []) if s.get('codec_type') == 'audio'), {})
    duration = float(data.get('format', {}).get('duration', 0))
    if stream.get('sample_rate') != '24000' or stream.get('channels') != 1 or not .3 < duration < 60:
        stop('unexpected_audio_format_or_duration', file=path.name)
    return duration


def successful(data):
    output = data.get('output') if isinstance(data, dict) else None
    if not isinstance(output, dict) or not isinstance(output.get('audio'), dict):
        return False
    url = output['audio'].get('url')
    return output.get('finish_reason') == 'stop' and isinstance(url, str) and bool(url)


def expired(data):
    audio = data.get('output', {}).get('audio', {})
    expires = audio.get('expires_at')
    if expires is None:
        expires = urllib.parse.parse_qs(urllib.parse.urlsplit(audio.get('url', '')).query).get('Expires', [None])[0]
    try:
        return float(expires) <= time.time()
    except (ValueError, TypeError):
        try:
            return datetime.datetime.fromisoformat(str(expires).replace('Z', '+00:00')).timestamp() <= time.time()
        except (ValueError, TypeError):
            return False  # Unknown expiry never authorizes paid replacement.


def synthesize(row, payload, response_file):
    if not os.environ.get('DASHSCOPE_API_KEY'):
        stop('DASHSCOPE_API_KEY_missing')
    pending = response_file.with_suffix('.pending.json')
    if pending.exists():
        stop('unresolved_previous_synthesis', id=row['id'],
             action='Inspect pending request before any further paid call')
    write_json(pending, {'id': row['id'], 'requestSha256': digest(payload),
                         'state': 'request_may_have_been_sent'})
    write_json(response_file.with_suffix('.request.json'), payload)
    status, body, _ = fetch(ENDPOINT, payload)
    try:
        data = json.loads(body)
    except ValueError:
        data = {'_http_status': status, '_non_json_response': True}
    if not isinstance(data, dict):
        data = {'_http_status': status, '_invalid_json_structure': True}
    data['_http_status'] = status
    data['_request_sha256'] = digest(payload)
    write_json(response_file, data)
    pending.unlink()
    if status != 200 or not successful(data):
        stop('synthesis_failed_cached_no_automatic_retry', id=row['id'], http_status=status)
    return data


def metadata(row, payload, data, wav, duration, source):
    usage = data.get('usage', {})
    if not isinstance(usage, dict):
        usage = {}
    request_id = data.get('request_id')
    if not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', request_id):
        request_id = None
    return {'id': row['id'], 'speaker': row['speaker'], 'model': MODEL,
            'actualRequest': payload, 'requestSha256': digest(payload), 'requestSource': source,
            'requestId': request_id, 'finishReason': 'stop',
            'duration': duration, 'wavSha256': hashlib.sha256(wav.read_bytes()).hexdigest(),
            'usage': {k: v for k, v in usage.items() if isinstance(v, (int, float))},
            'technicalVerification': 'decode, sample rate, channels and duration only',
            'contentVerification': 'pending actual listening',
            'voiceConsistencyVerification': 'pending actual listening'}


def recover_wav(row, prepared, wav, meta_file, first=False):
    if not wav.exists() or not meta_file.exists():
        return None
    meta = read_json(meta_file)
    if not isinstance(meta, dict) or meta.get('requestSource') not in (
            'prepared', 'legacy_narrator_probe_actual_request', 'prepared_explicit_new_probe'):
        stop('invalid_safe_metadata', id=row['id'])
    payload = meta.get('actualRequest', {})
    legacy = first and meta['requestSource'] == 'legacy_narrator_probe_actual_request'
    validate_request(payload, row, require_direction=not legacy)
    if meta.get('requestSha256') != digest(payload) or (not legacy and digest(payload) != digest(prepared)):
        stop('cached_request_hash_mismatch', id=row['id'])
    if meta.get('model') != MODEL or meta.get('wavSha256') != hashlib.sha256(wav.read_bytes()).hexdigest():
        stop('cached_wav_metadata_mismatch', id=row['id'])
    duration = decode(wav)
    emit(stage='recovered_wav', id=row['id'], seconds=duration,
         content_verified=False, voice_consistency_verified=False)
    # Rebuild an allowlisted safe record; never propagate a URL from metadata.
    return metadata(row, payload, {'request_id': meta.get('requestId'),
                                  'usage': meta.get('usage', {})},
                    wav, duration, meta['requestSource'])


def finish_download(row, payload, data, wav, meta_file, source):
    if data.get('_http_status', 200) != 200 or not successful(data):
        stop('incomplete_or_failed_cache_no_automatic_retry', id=row['id'])
    if source != 'legacy_narrator_probe_actual_request' and data.get('_request_sha256') != digest(payload):
        stop('cached_response_request_hash_mismatch', id=row['id'])
    if not wav.exists():
        url = data['output']['audio']['url']
        status, body, _ = fetch(url)  # No Authorization on downloads.
        if status != 200:
            stop('audio_download_failed_keep_paid_response', id=row['id'],
                 host=urllib.parse.urlsplit(url).hostname, http_status=status,
                 expired=expired(data))
        temp = wav.with_suffix('.wav.part')
        temp.write_bytes(body)
        decode(temp)
        temp.replace(wav)
    duration = decode(wav)
    meta = metadata(row, payload, data, wav, duration, source)
    write_json(meta_file, meta)
    emit(stage='audio_ready', id=row['id'], seconds=duration,
         content_verified=False, voice_consistency_verified=False)
    return meta


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-dir', type=pathlib.Path, default=pathlib.Path('/workspace/menwai-site'))
    parser.add_argument('--work-dir', type=pathlib.Path, default=pathlib.Path('/workspace/scratch/qwen-next-audition'))
    parser.add_argument('--requests-dir', type=pathlib.Path, default=pathlib.Path(__file__).resolve().parent / 'prepared')
    parser.add_argument('--validate-only', action='store_true')
    parser.add_argument('--probe-only', action='store_true')
    parser.add_argument('--new-probe', action='store_true')
    args = parser.parse_args(argv)
    work = args.work_dir.resolve()
    for protected in (args.project_dir.resolve(), pathlib.Path(__file__).resolve().parent):
        if work == protected or protected in work.parents:
            stop('work_dir_must_be_outside_project_and_handoff')
    selection = read_json(args.project_dir / 'review/qwen-audition/selection.json')
    if not isinstance(selection, list) or len(selection) != 20 or len({r.get('id') for r in selection}) != 20:
        stop('expected_20_unique_selection_rows')
    payloads = []
    for row in selection:
        payload = read_json(args.requests_dir / (row['id'] + '.json'))
        validate_request(payload, row)
        payloads.append(payload)
    if args.validate_only:
        emit(status='request_validation_passed', count=20, model=MODEL,
             api_calls_made=False, audio_content_verified=False,
             voice_consistency_verified=False)
        return
    wavs, responses, metas = (work / x for x in ('wavs', 'responses', 'metadata'))
    for directory in (wavs, responses, metas):
        directory.mkdir(parents=True, exist_ok=True)
    reports = []
    for index, (row, prepared) in enumerate(zip(selection, payloads)):
        first = index == 0
        wav = wavs / (row['id'] + '.wav')
        meta_file = metas / (row['id'] + '.json')
        restored = recover_wav(row, prepared, wav, meta_file, first=first)
        if restored:
            if first and args.new_probe:
                stop('new_probe_refused_existing_verified_wav', id=row['id'])
            reports.append(restored)
        else:
            response_file = responses / (row['id'] + '.json')
            request_file = response_file.with_suffix('.request.json')
            source = 'prepared'
            if first and not response_file.exists() and (work / 'narrator-probe-response.json').exists():
                response_file = work / 'narrator-probe-response.json'
                request_file = work / 'narrator-probe-request.json'
                source = 'legacy_narrator_probe_actual_request'
            data = read_json(response_file) if response_file.exists() else None
            if first and args.new_probe:
                if data is not None and (not successful(data) or not expired(data)):
                    stop('new_probe_refused_cache_not_missing_or_known_expired', id=row['id'])
                if wav.exists() or (work / 'narrator-probe.wav').exists():
                    stop('new_probe_refused_existing_wav', id=row['id'],
                         action='Restore metadata or verify existing WAV first')
                # Do not overwrite even expired responses; preserve paid-call evidence.
                target = responses / (row['id'] + '.json')
                if target.with_suffix('.pending.json').exists():
                    stop('unresolved_previous_synthesis', id=row['id'])
                check_download_access()
                if not os.environ.get('DASHSCOPE_API_KEY'):
                    stop('DASHSCOPE_API_KEY_missing')
                if target.exists():
                    archive = target.with_name(target.stem + '.expired-' + str(time.time_ns()) + '.json')
                    target.replace(archive)
                    old_request = target.with_suffix('.request.json')
                    if old_request.exists():
                        old_request.replace(archive.with_suffix('.request.json'))
                payload = prepared
                response_file = target
                data = synthesize(row, payload, response_file)
                source = 'prepared_explicit_new_probe'
            elif data is not None:
                payload = read_json(request_file)
                legacy = first and source == 'legacy_narrator_probe_actual_request'
                validate_request(payload, row, require_direction=not legacy)
                if not legacy and digest(payload) != digest(prepared):
                    stop('cached_request_hash_mismatch', id=row['id'])
            elif first:
                stop('narrator_cache_missing_no_paid_call',
                     action='Restore cache or explicitly use --new-probe --probe-only')
            else:
                if wav.exists():
                    stop('wav_without_verifiable_metadata_or_response', id=row['id'])
                payload = prepared
                data = synthesize(row, payload, response_file)
            if first and source == 'legacy_narrator_probe_actual_request' and not wav.exists() and (work / 'narrator-probe.wav').exists():
                shutil.copyfile(work / 'narrator-probe.wav', wav)
            reports.append(finish_download(row, payload, data, wav, meta_file, source))
        write_json(work / 'generation-report-safe.json', {
            'count': len(reports), 'model': MODEL, 'lines': reports,
            'contentVerification': 'pending actual listening',
            'voiceConsistencyVerification': 'pending actual listening'})
        if first and args.probe_only:
            emit(status='probe_ready_technical_checks_only', count=1, model=MODEL)
            return
    emit(status='all_audio_ready_technical_checks_only', count=len(reports), model=MODEL)


if __name__ == '__main__':
    try:
        main()
    except Stop:
        sys.exit(2)
    except (OSError, ValueError, KeyError, TypeError) as error:
        emit(status='stopped', reason='invalid_local_state', error_type=type(error).__name__)
        sys.exit(2)
