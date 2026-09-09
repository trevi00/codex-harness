"""Shared runtime record reference semantics for publication and collection."""

import ast
import hashlib
import io
import json
import re
import tokenize
import tomllib
from urllib.parse import urlsplit

PATTERN = re.compile(r"(?<!spec-)sha256:[0-9a-f]{64}(?![0-9a-f])")
POTENTIAL_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
NATIVE_FRAGMENT = re.compile(r'(?<!\\)\\*"currentHash\\*"\s*:\s*\\*"(sha256:[0-9a-f]{64})\\*"')
IMAGE_CONTEXT = {'candidate', 'checks', 'source_binding', 'image_hashes', 'source_hashes', 'runner', 'Service', 'final_canaries', 'reader_output_characters', 'loaded_source', 'woken'}
LEGACY_IMAGE_DIAGNOSTIC = 'OCI image digests in immutable execution receipts are traversed as artifact dependencies'


def potential_references(value):
    """Conservative handles for retention/fencing, without metadata exclusions."""
    found, pending = set(), [value]
    while pending:
        current = pending.pop()
        if isinstance(current, dict):
            pending.extend(current.keys())
            pending.extend(current.values())
        elif isinstance(current, (list, tuple)):
            pending.extend(current)
        elif isinstance(current, str):
            found.update(POTENTIAL_PATTERN.findall(current))
            # Over-retention is safe. Decode ASCII escapes conservatively even
            # in malformed diagnostic strings, without interpreting metadata.
            for _ in range(8):
                if '\\u00' not in current:
                    break
                decoded = re.sub(r'\\+u00([0-9a-fA-F]{2})', lambda m: chr(int(m[1], 16)), current)
                if decoded == current:
                    break
                current = decoded
                found.update(POTENTIAL_PATTERN.findall(current))
    return found


def potential_record_references(bucket, key, body):
    return set() if bucket == 'artifact_tombstones' else potential_references([bucket, key, body])


def _download_record(value):
    if not isinstance(value, dict) or not isinstance(value.get('url'), str):
        return False
    try:
        address = urlsplit(value['url'])
    except ValueError:
        return False  # Malformed source metadata must retain potential evidence.
    return address.scheme in {'https', 'http'} and bool(address.netloc)


def _without_toml_download_hash(line):
    stripped = re.sub(r'^\d+:\s*', '', line.strip())
    if not ('hash' in stripped and 'url' in stripped and '=' in stripped):
        return line
    try:
        if stripped.startswith('{'):
            entry = tomllib.loads('_entry = ' + stripped.rstrip(','))['_entry']
        elif stripped.startswith('sdist ='):
            entry = tomllib.loads(stripped)['sdist']
        else:
            return line
    except (ValueError, KeyError):
        return line
    digest = entry.get('hash') if isinstance(entry, dict) else None
    if not _download_record(entry) or not isinstance(digest, str) or not PATTERN.fullmatch(digest):
        return line
    # Only the integrity scalar is excluded. Comments and ref fields survive.
    return re.sub(r'(\bhash\s*=\s*")' + re.escape(digest) + r'(")',
                  lambda match: match[1] + 'DOWNLOAD_DIGEST' + match[2], line, count=1)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Ambiguous duplicate JSON key')
        result[key] = value
    return result


def _docker_inspection(argv):
    """Return operands and format only for a fully recognized inspection argv."""
    if (not isinstance(argv, list) or not all(isinstance(arg, str) for arg in argv)
            or len(argv) < 3 or argv[0] != 'docker'):
        return None
    if argv[1:3] == ['image', 'inspect']:
        index = 3
    elif argv[1] == 'inspect':
        index = 2
    else:
        return None
    operands, options = [], {}
    while index < len(argv):
        value = argv[index]
        if value in {'--format', '-f', '--type'}:
            name = '--format' if value == '-f' else value
            if (name in options or index + 1 >= len(argv)
                    or not argv[index + 1] or argv[index + 1].startswith('-')):
                return None
            options[name] = argv[index + 1]
            index += 2
        elif value.startswith('-') or not value:
            return None
        else:
            operands.append(index)
            index += 1
    if not operands or options.get('--type', 'image') not in {'image', 'container'}:
        return None
    return operands, options.get('--format')


def _docker_image_slots(argv):
    """Recognize only the Docker command shapes emitted by harness adapters."""
    if not isinstance(argv, list) or len(argv) < 3 or argv[0] != 'docker':
        return set()
    if argv[1:3] == ['image', 'inspect'] or argv[1] == 'inspect':
        inspection = _docker_inspection(argv)
        return {i for i in inspection[0] if PATTERN.fullmatch(argv[i])} if inspection else set()
    if argv[1] != 'run':
        return set()
    switches = {'--rm', '-d', '--init', '--read-only', '--privileged', '-i', '-t', '-it', '--tty'}
    values = {'--name', '--memory', '--cpus', '--entrypoint', '--mount', '-v', '--volume',
              '-w', '--workdir', '-e', '--env', '--network', '--user', '--pids-limit',
              '--tmpfs', '--security-opt', '--cap-drop', '--cap-add', '--label', '-p',
              '--publish', '--memory-swap', '--ulimit'}
    index = 2
    while index < len(argv) and isinstance(argv[index], str):
        value = argv[index]
        if not value.startswith('-'):
            return {index} if PATTERN.fullmatch(value) else set()
        if value in switches:
            index += 1
        elif value in values:
            index += 2
        elif '=' in value and value.partition('=')[0] in values:
            index += 1
        else:
            return set()  # Unknown syntax stays conservative, never drops a reference.
    return set()


def _image_identity_output(argv, value):
    if not isinstance(argv, list) or not isinstance(value, str) or not value.strip():
        return False
    inspection = _docker_inspection(argv)
    return bool(inspection and inspection[1] in {'{{.Id}}', '{{.Image}}'}
                and all(PATTERN.fullmatch(line.strip()) for line in value.splitlines()))


def _python_runner_references(body):
    """Exclude only single literal image tokens in a valid retained runner."""
    if len(body) > 1_000_000:
        return set(PATTERN.findall(body))
    # Match Python's universal-newline handling before computing byte positions.
    body = body.replace('\r\n', '\n').replace('\r', '\n')
    try:
        tree = ast.parse(body)
    except (SyntaxError, ValueError, RecursionError):
        return set(PATTERN.findall(body))
    data = body.encode('utf-8')
    offsets, cursor = [], 0
    # AST columns count UTF-8 bytes, using the normalized source lines above.
    for line in data.split(b'\n'):
        offsets.append(cursor)
        cursor += len(line) + 1
    spans = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.List) or any(isinstance(item, ast.Starred) for item in node.elts):
            continue
        values = [item.value if isinstance(item, ast.Constant) and isinstance(item.value, str)
                  else None for item in node.elts]
        for index in _docker_image_slots(values):
            item = node.elts[index]
            start = offsets[item.lineno - 1] + item.col_offset
            end = offsets[item.end_lineno - 1] + item.end_col_offset
            try:
                tokens = list(tokenize.generate_tokens(io.StringIO(data[start:end].decode('utf-8')).readline))
            except (tokenize.TokenError, IndentationError):
                continue  # A valid parenthesized expression may not tokenize in isolation.
            significant = [token for token in tokens if token.type not in {
                tokenize.NEWLINE, tokenize.NL, tokenize.ENDMARKER}]
            # INV-RESOURCE-001: concatenated strings can contain evidence comments.
            if len(significant) == 1 and significant[0].type == tokenize.STRING:
                spans.add((start, end))
    for start, end in sorted(spans, reverse=True):
        data = data[:start] + b'"OCI_IMAGE"' + data[end:]
    # Do not reinterpret comments or other literals as diagnostic JSON/OCI fields.
    return set(PATTERN.findall(data.decode('utf-8')))


def _without_buildkit_identities(line):
    # BuildKit labels are OCI identities, including the image's constituent blobs.
    # Anchor the whole emitted progress line; adjacent evidence text is retained.
    exporting = re.fullmatch(
        r'#\d+ exporting (?:config|manifest(?: list)?|attestation manifest) '
        r'sha256:[0-9a-f]{64}(?: [\d.]+s)? done', line.strip())
    if exporting:
        return ''
    return re.sub(r'(?<=@)sha256:[0-9a-f]{64}', 'OCI_DIGEST', line) if re.fullmatch(
        r'#\d+ (?:\[[^\]]+\] FROM|resolve) [\w./:-]+@sha256:[0-9a-f]{64}(?: [\d.]+s done)?',
        line.strip()) else line


def _coalesced_events(events):
    """Only coalesce streams corroborated by the completed command output."""
    streams, completed = {}, {}
    for event in events:
        params = event.get('params') if isinstance(event, dict) else None
        if not isinstance(params, dict):
            continue
        item = params.get('item')
        if (event.get('method') == 'item/completed' and isinstance(item, dict)
                and item.get('type') == 'commandExecution'
                and isinstance(item.get('aggregatedOutput'), str)
                and all(isinstance(value, str) for value in (params.get('threadId'), params.get('turnId'), item.get('id')))):
            key = (params.get('threadId'), params.get('turnId'), item.get('id'))
            completed[key] = item['aggregatedOutput']
        if (isinstance(params, dict) and event.get('method') == 'item/commandExecution/outputDelta'
                and isinstance(params.get('delta'), str)
                and all(isinstance(params.get(k), str) for k in ('itemId', 'threadId', 'turnId'))):
            key = tuple(params[k] for k in ('threadId', 'turnId', 'itemId'))
            streams.setdefault(key, []).append(params['delta'])
    verified = {}
    for key, parts in streams.items():
        if key not in completed:
            continue
        body, cursor = completed[key], 0
        for part in parts:
            offset = body.find(part, cursor)
            if offset < 0:
                break
            cursor = offset + len(part)
        else:
            # Missing deltas may leave gaps. Use the actual completed bytes;
            # never concatenate fragments across a gap into invented output.
            verified[key] = body
    retained = []
    for event in events:
        params = event.get('params') if isinstance(event, dict) else None
        if (isinstance(params, dict) and event.get('method') == 'item/commandExecution/outputDelta'
                and all(isinstance(params.get(k), str) for k in ('threadId', 'turnId', 'itemId'))
                and tuple(params.get(k) for k in ('threadId', 'turnId', 'itemId')) in verified):
            retained.append({**event, 'params': {k: v for k, v in params.items() if k != 'delta'}})
        else:
            retained.append(event)
    return retained, list(verified.values())


def _typed_metadata_fragments(text, native_identities=None):
    """Decode complete scalar metadata objects inside clipped/escaped log pages."""
    if 'currentHash' not in text and 'trusted_hash' not in text and not ('hash' in text and 'url' in text):
        return text, set()
    start, cursor, pieces, references = None, 0, [], set()
    for match in re.finditer(r'[{}]', text):
        if match[0] == '{':
            start = match.start()
            continue
        if start is None or match.end() - start > 16384:
            start = None
            continue
        leaf = text[start:match.end()]
        decoded = None
        for _ in range(8):
            try:
                decoded = json.loads(leaf, object_pairs_hook=_unique_object)
                break
            except ValueError:
                try:
                    decoded = tomllib.loads('_entry = ' + leaf)['_entry']
                    break
                except (ValueError, KeyError):
                    pass
                try:
                    leaf = json.loads('"' + leaf + '"')
                except ValueError:
                    break
        if isinstance(decoded, dict):
            native = (decoded.get('handlerType') == 'command'
                      and isinstance(decoded.get('command'), str)
                      and isinstance(decoded.get('eventName'), str)
                      and isinstance(decoded.get('currentHash'), str))
            prefix = text[max(0, start - 160):start].replace('\\', '')
            trust = (re.search(r'config\.toml:session_start:\d+:\d+"\s*:\s*$', prefix)
                     and isinstance(decoded.get('enabled'), bool)
                     and isinstance(decoded.get('trusted_hash'), str)
                     and PATTERN.fullmatch(decoded['trusted_hash']))
            download = (_download_record(decoded) and isinstance(decoded.get('hash'), str)
                        and PATTERN.fullmatch(decoded['hash']))
            if native or trust or download:
                if native and native_identities is not None and PATTERN.fullmatch(decoded['currentHash']):
                    native_identities.add(decoded['currentHash'])
                if trust:
                    decoded = {k: v for k, v in decoded.items() if k != 'trusted_hash'}
                references.update(artifact_references(decoded))
                pieces.extend((text[cursor:start], 'TYPED_METADATA'))
                cursor = match.end()
        start = None
    pieces.append(text[cursor:])
    return ''.join(pieces), references


def _docker_argv_fragments(text, image_identities=None):
    """Decode complete argv arrays within escaped or headed diagnostic output."""
    cursor, pieces, references = 0, [], set()
    space = r'(?:\s|\\+[nr])*'
    starts = re.finditer(r'\[' + space + r'\\*"docker\\*"' + space + ',' + space
                         + r'\\*"(?:run|inspect|image)\\*"', text)
    for start in starts:
        if start.start() < cursor:
            continue
        window = text[start.start():start.start() + 16384]
        for attempt, closing in enumerate(re.finditer(r'\]', window)):
            if attempt >= 32:
                break
            fragment = window[:closing.end()]
            decoded = None
            for _ in range(8):
                try:
                    decoded = json.loads(fragment, object_pairs_hook=_unique_object)
                    break
                except ValueError:
                    try:
                        fragment = json.loads('"' + fragment + '"')
                    except ValueError:
                        break
            if isinstance(decoded, list) and _docker_image_slots(decoded):
                if image_identities is not None:
                    image_identities.update(decoded[i] for i in _docker_image_slots(decoded))
                references.update(artifact_references(decoded))
                pieces.extend((text[cursor:start.start()], 'DOCKER_ARGV'))
                cursor = start.start() + closing.end()
                break
    pieces.append(text[cursor:])
    return ''.join(pieces), references


def _ambiguous_json_references(text):
    """Fence duplicate objects locally, including truncated objects."""
    original = text
    for _ in range(8):
        stack, spans = [], []
        for token in re.finditer(r'"(?:[^"\\]|\\.)*"|[{}\[\]]', text):
            value = token[0]
            if value in {'{', '['}:
                # INV-RESOURCE-001: malformed prefixes cannot disable key tracking.
                # Empty source braces have no observed keys to fence.
                keys = set() if value == '{' else None
                stack.append([value, token.start(), keys, False])
            elif value in {'}', ']'}:
                if stack:
                    scope = stack[-1]
                    if (value == '}') != (scope[0] == '{'):
                        # INV-RESOURCE-001: mismatched nesting must not hide
                        # references in a recognized enclosing JSON object.
                        for enclosing in stack:
                            if enclosing[2]:
                                enclosing[3] = True
                        discarded = stack.pop()
                        if not stack and discarded[3]:
                            spans.append((discarded[1], len(text)))
                        continue
                    stack.pop()
                    if scope[2] and not any(parent[2] for parent in stack):
                        try:
                            json.loads(text[scope[1]:token.end()], object_pairs_hook=_unique_object)
                        except (ValueError, RecursionError):
                            scope[3] = True
                    if scope[3]:
                        spans.append((scope[1], token.end()))
            elif stack and stack[-1][2] is not None:
                if not re.compile(r'\s*:').match(text, token.end()):
                    continue
                try:
                    key = json.loads(value)
                except ValueError:
                    stack[-1][3] = True
                    continue
                if key in stack[-1][2]:
                    stack[-1][3] = True
                stack[-1][2].add(key)
        spans.extend((scope[1], len(text)) for scope in stack if scope[3] or scope[2])
        if spans:
            # INV-RESOURCE-001: ambiguous scopes retain every potential edge;
            # a separate complete log receipt must still receive typed decoding.
            pieces, found, cursor = [], set(), 0
            for start, end in sorted(spans):
                found.update(potential_references(text[start:end]))
                if start >= cursor:
                    pieces.extend((text[cursor:start], 'AMBIGUOUS_JSON'))
                cursor = max(cursor, end)
            pieces.append(text[cursor:])
            return ''.join(pieces), found
        try:
            unescaped = json.loads('"' + text + '"')
        except (ValueError, RecursionError):
            return text, set()
        if unescaped == text:
            return text, set()
        text = unescaped
    return '', potential_references([original, text])


def artifact_references(value, *, source: str = '', cache: dict | None = None) -> set[str]:
    """Keep artifact edges; OCI image fields and Docker image operands are typed data."""
    if source == 'baldrix-budget-probe-runner' and isinstance(value, str):
        return _python_runner_references(value)
    if source == 'migration-claim-document' and isinstance(value, str):
        # Retained Markdown migration reports label the test container separately
        # from receipts. Only the complete image declaration has OCI semantics.
        value = re.sub(r'(?m)^Image: `sha256:[0-9a-f]{64}`\.[ \t]*$',
                       'Image: OCI_DIGEST.', value)
    if re.fullmatch(r'https://github\.com/[\w.-]+/[\w.-]+/blob/[0-9a-f]{40}/[^?#]+', source):
        # Pinned upstream bytes are inert source material in another namespace.
        # Their code literals cannot address this harness's local artifact store.
        return set()
    found, pending = set(), [(value, 0, False)]
    native_identities, image_identities = set(), set()
    unresolved_native, unresolved_images = set(), set()
    while pending:
        current, depth, output_fragment = pending.pop()
        if isinstance(current, dict):
            if cache is not None and not output_fragment and {'id', 'message', 'status'} <= current.keys():
                # Immutable metric snapshots repeat complete task/decision rows.
                # Cache by complete content, never by mutable task identity.
                key = hashlib.sha256(json.dumps(current, sort_keys=True, separators=(',', ':')).encode()).digest()
                if key not in cache:
                    if len(cache) >= 2048:
                        cache.pop(next(iter(cache)))
                    cache[key] = frozenset(artifact_references(current))
                found.update(cache[key])
                continue
            argv = current.get('argv', current.get('command'))
            merge = current.get('merge')
            image_record = (bool(IMAGE_CONTEXT.intersection(current)) or {'id', 'revision'} <= current.keys()
                            or {'service', 'name', 'state'} <= current.keys()
                            or (isinstance(current.get('service'), str)
                                and isinstance(current.get('state'), str)
                                and isinstance(current.get('cli_version'), str)
                                and type(current.get('cli_exit_code')) is int)
                            or {'revision', 'exit_code', 'result'} <= current.keys()
                            or bool(_docker_image_slots(argv))
                            or (isinstance(merge, dict) and isinstance(merge.get('merged'), bool)
                                and isinstance(merge.get('revision'), str))
                            or current.get('kind') == 'oci_image')
            # The historical operator preflight called an explicitly identified
            # OCI value "missing_digest". Decode that exact legacy schema only;
            # ordinary missing-evidence diagnostics must still fail closed.
            image_diagnostic = (current.get('root_cause') == LEGACY_IMAGE_DIAGNOSTIC
                                and current.get('status') == 'collection_deferred'
                                and isinstance(current.get('evidence_parent_refs'), list)
                                and bool(current['evidence_parent_refs']))
            for key, child in current.items():
                found.update(PATTERN.findall(str(key)))
                if (key == 'unavailable_evidence_handles' and isinstance(child, list)
                        and all(isinstance(item, str) and PATTERN.fullmatch(item) for item in child)
                        and isinstance(current.get('document'), str)
                        and isinstance(current.get('document_ref'), str)
                        and PATTERN.fullmatch(current['document_ref'])
                        and isinstance(current.get('origin'), str)
                        and isinstance(current.get('retained_evidence_refs'), list)):
                    # Migration claim ledgers explicitly distinguish absent
                    # handles from retained evidence. Absence is a finding,
                    # never a claim that the unavailable body was inspected.
                    continue
                if key == 'events' and isinstance(child, list):
                    events, streams = _coalesced_events(child)
                    pending.extend((stream, depth + 1, True) for stream in streams)
                    pending.append((events, depth + 1, False))
                    continue
                if (isinstance(key, str) and re.search(r'config\.toml:session_start:\d+:\d+$', key)
                        and isinstance(child, dict) and isinstance(child.get('enabled'), bool)
                        and isinstance(child.get('trusted_hash'), str)
                        and PATTERN.fullmatch(child['trusted_hash'])):
                    pending.append(({k: v for k, v in child.items() if k != 'trusted_hash'}, depth + 1, False))
                    continue  # Exact native hook trust-map identity, not a blob handle.
                if image_record and key in {'image', 'Image', 'image_id', 'image_digest', 'container_image'} and isinstance(child, str) and PATTERN.fullmatch(child):
                    image_identities.add(child)
                    continue
                if image_diagnostic and key == 'missing_digest' and isinstance(child, str) and PATTERN.fullmatch(child):
                    continue
                if key == 'hash' and _download_record(current) and isinstance(child, str) and PATTERN.fullmatch(child):
                    continue
                if key == 'currentHash' and isinstance(child, str) and PATTERN.fullmatch(child) and current.get('handlerType') == 'command' and isinstance(current.get('command'), str) and isinstance(current.get('eventName'), str):
                    native_identities.add(child)
                    continue  # Native hook identity, not an artifact address.
                image_slots = _docker_image_slots(child) if key in {'argv', 'command'} else set()
                if image_slots:
                    image_identities.update(child[i] for i in image_slots)
                    pending.extend((item, depth + 1, False) for i, item in enumerate(child) if i not in image_slots)
                elif key == 'stdout' and _image_identity_output(argv, child):
                    continue  # Exact image identity output, not an evidence handle.
                else:
                    pending.append((child, depth + 1, output_fragment or key in {'aggregatedOutput', 'stdout', 'stderr', 'output', 'delta'}))
        elif isinstance(current, list):
            image_slots = _docker_image_slots(current)
            image_identities.update(current[i] for i in image_slots)
            pending.extend((item, depth + 1, output_fragment) for i, item in enumerate(current)
                           if i not in image_slots)
        elif isinstance(current, str):
            if 'sha256' not in current and '\\u' not in current:
                continue
            # INV-RESOURCE-001: establish complete JSON boundaries before probing
            # malformed fragments. A valid escaped log is not an ambiguous object.
            if depth < 128:
                try:
                    complete = json.loads(current, object_pairs_hook=_unique_object)
                except (ValueError, RecursionError):
                    complete = None
                if isinstance(complete, (dict, list, str)):
                    pending.append((complete, depth + 1, output_fragment))
                    continue
            current, ambiguous = _ambiguous_json_references(current)
            found.update(ambiguous)
            if output_fragment and re.fullmatch(r'actual runner image: sha256:[0-9a-f]{64}', current.strip()):
                continue
            current = re.sub(
                r'(trusted handler hash:(?:\s|\\+n|\+|`)*)(sha256:[0-9a-f]{64})',
                lambda match: match[1] + 'NATIVE_HANDLER_DIGEST', current)
            if depth < 128:
                try:
                    decoded = json.loads(current, object_pairs_hook=_unique_object)
                except (ValueError, RecursionError):
                    decoded = None
                    if current.startswith('hooks='):
                        try:
                            decoded = tomllib.loads(current)
                        except ValueError:
                            pass
                if isinstance(decoded, (dict, list, str)):
                    pending.append((decoded, depth + 1, output_fragment))
                    continue
                current, argv_refs = _docker_argv_fragments(current, image_identities)
                found.update(argv_refs)
                if len(current) <= 32768:
                    # Commands often print a heading followed by a JSON receipt.
                    # Only fully decoded structures are interpreted; surrounding
                    # prose and malformed fragments retain every potential edge.
                    decoder = json.JSONDecoder(object_pairs_hook=_unique_object)
                    for attempt, match in enumerate(re.finditer(r'[\[{]', current)):
                        if attempt >= 1:
                            break
                        try:
                            decoded, end = decoder.raw_decode(current, match.start())
                        except (ValueError, RecursionError):
                            continue
                        if isinstance(decoded, (dict, list)):
                            pending.extend((part, depth + 1, output_fragment) for part in (
                                current[:match.start()], decoded, current[end:]))
                            break
                    else:
                        decoded = None
                    if isinstance(decoded, (dict, list)):
                        continue
                if '\n' in current:
                    pending.extend((line, depth + 1, output_fragment) for line in current.splitlines())
                    continue
            current, native_refs = _typed_metadata_fragments(current, native_identities)
            found.update(native_refs)
            if output_fragment:
                # Preserve incomplete identity fields independently of complete
                # declarations elsewhere; value equality cannot prove provenance.
                unresolved_native.update(match[1] for match in NATIVE_FRAGMENT.finditer(current))
                current = NATIVE_FRAGMENT.sub('NATIVE_IDENTITY_TOKEN', current)
                # INV-RESOURCE-001: malformed JSON image fields cannot borrow
                # typed identity from a different receipt with the same value.
                clipped_image = re.match(r'^(?:ocker|cker|ker|er|r) image (sha256:[0-9a-f]{64})(?![0-9a-f])', current)
                if not clipped_image:
                    clipped_image = re.match(
                        r'^ ?(sha256:[0-9a-f]{64}), then the real CLI file-task canary was run by that immutable ID\.', current)
                if clipped_image:
                    # A stream can start inside the word Docker. Bind this
                    # typed suffix only to a complete declaration in this artifact.
                    unresolved_images.add(clipped_image[1])
                    current = current[:clipped_image.start(1)] + 'IMAGE_IDENTITY_TOKEN' + current[clipped_image.end(1):]
            image_identities.update(re.findall(r'\b(?:immutable )?Docker image (sha256:[0-9a-f]{64})(?![0-9a-f])', current))
            current = re.sub(r'\b(?:immutable )?Docker image sha256:[0-9a-f]{64}',
                             'Docker image OCI_DIGEST', current)
            found.update(PATTERN.findall(_without_buildkit_identities(_without_toml_download_hash(current))))
    # INV-RESOURCE-001: equal digest values do not prove shared occurrence provenance.
    return found | unresolved_native | unresolved_images


def record_references(bucket: str, key: str, body: dict) -> set[str]:
    # INV-RESOURCE-001: fences are metadata, never collection roots. All other
    # record fields (including dictionary keys) participate in retention.
    if bucket == "artifact_tombstones":
        return set()
    return set(PATTERN.findall(bucket + '\n' + key)) | artifact_references(body)
