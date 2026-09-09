"""Bounded historical copy proofs; no runtime record can add an annotation.

INV-RESOURCE-001: this catalogue proves particular copies, never digest classes.
The compressed originals and Git objects are review inputs, not artifact preimages
invented for synthetic values. All origins remain mandatory graph dependencies.
"""

import ast
import base64
import hashlib
import json
import re
import shlex
import zlib

from codex_harness.domain.model import require

# INV-RESOURCE-001: Git-reviewed trust roots; a repacked receipt cannot
# authenticate itself by changing its own digest and generated annotations.
SOURCES = {
    'printed_execution': '26f4e92f18f03d9eb01b30077a902c3effd02dfbf16284ac940bd7210d00e8d9',
    'printed_task': 'd0b95563b845fcb2f6cfccf25c4a0391ab6fbdb9785c2d2db180dbe36af925be',
    'printed_binding': '74cd30cd3e8b313e037fb15447a4a77d4dfe2fdcffb96e47d69400f44b037cf7',
    'printed_canary': '0b022b0df8cd400e86437e10f899bdc64f8ff8773042a2b83f10eb9cc82b4f08',
    'printed_validation_0': '4d8afff2538a73c65739b1c7573b290d3bd887c1849b3c4a8514a52b3c190315',
    'printed_validation_1': 'be0b53c257cfd5c413c37d8084fefb8b09a91eff4dbebff7d4da8b1ea5db09c9',
    'printed_validation_2': 'ed40c481e3f623fd7e5758f8cc94583602fa0d6175d321b924bc2d3612dbb50e',
    'printed_validation_3': '2a7ba5567ab2ae1ba6cd670597d1b96d7853bec095c96b70f000279d6b64c81f',
    'printed_validation_4': '39ba9ee3a962efa9b6940b2d9e8dd31b045b8f19c377cc31f8ba964885b9e4c2',

    'malformed_diff': '0a709c9ce8c3cd550e12f8a47c151bd884132fb6ec0c3ccb24c7861cccbb577b',
    'malformed_execution': '6b145c4bc3834cc1af4c84543ae0ae922345d47eda894d4d4f6db76d8c31a52e',
    'runner_execution': '34387bcb5a12d3f30db01a3672548efeaf3a1f6be802c9c195f33e0b5f073613',
    'runner_review': '52303f1f22318fbb6ba7de0b47f4cf6e137242c12fc0b74023ae53b236c390f6',
    'pytest_diff': '4fe2f35b9494727f2409cc00763083869d8106434e02140c44d912f8ea86d0fd',
    'pytest_execution': 'eb56f9fd8f9bf13babf8c8e6360de6999fe2858412b7e4e15643b5c1b8ee949a',
    'prefix_diff': '7746a7d290352e522e73e481ced8ab51f3a474f99fbc85b7b5618e2405f48dfe',
    'prefix_review': 'be0a89b15234f46da28627c293493598fa7a145d4a9f4ab2cb85706e79ecb67b',
    'loop_execution': 'f83af829cfbdef93c0bc5f75901d453dedf9c0211450910115cf27536dc7098b',
    'prefix_execution': 'b47454d588be57344ca76fbcbdf0a06a4bfda4bf8b15bef7d0e3964a9f5733f9',
    'runner': 'b967dca2a7a4cf978c06c0f08198ac4677b4fa28fa3e3d20a0da2d8abbf85855',
}
REVISIONS = {
    'malformed': 'b66e2017eb39643fd1128c1cf3b5173ea661991e',
    'malformed_base': '445fbc8859e896b90e974ed69447ce58e3446251',
    'malformed_rejected': 'b42e0955e3ecf12e54fd4190b6b310a16f44a544',
    'restored': '5dc00f184a6bfff450d4fd090aa1bff13e1e036f',
    'base': 'e68d5e157465b4b03193ee3feeb3a776473b8d40',
    'rework': '19c4d73c879bef32909307186e8196a682cdbcbd',
    'prefix': 'a22d0d12dd598f0a5ba4d5301b1362be757e2bd7',
    'runner_candidate': '34da547aa6d8fc162ac9890cc5cd40d6a3d138b3',
}

def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate historical proof key')
        result[key] = value
    return result


def decode(data):
    return json.loads(data, object_pairs_hook=unique)


def unpack(value):
    raw = base64.b64decode(value, validate=True)
    stream = zlib.decompressobj()
    data = stream.decompress(raw, 2_000_001)
    require(len(data) <= 2_000_000 and stream.eof and not stream.unused_data,
            'Oversized or incomplete historical source')
    return data


def pointer(document, selector):
    require(isinstance(selector, str) and selector.startswith('/'), 'Invalid copy selector')
    keys = selector[1:].split('/')
    owner = document
    for part in keys[:-1]:
        key = part.replace('~1', '/').replace('~0', '~')
        owner = owner[int(key)] if isinstance(owner, list) else owner[key]
    key = keys[-1].replace('~1', '/').replace('~0', '~')
    return owner, int(key) if isinstance(owner, list) else key


def shell(command):
    argv = shlex.split(command)
    require(len(argv) == 3 and argv[:2] == ['/bin/bash', '-lc'], 'Unknown command wrapper')
    return argv[2]


def constant(expression):
    """Only a literal string concatenated with a bounded literal repetition."""
    node = ast.parse(expression, mode='eval').body
    require(isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
            and isinstance(node.left, ast.Constant) and node.left.value == 'sha256:'
            and isinstance(node.right, ast.BinOp) and isinstance(node.right.op, ast.Mult)
            and isinstance(node.right.left, ast.Constant)
            and isinstance(node.right.left.value, str) and len(node.right.left.value) == 1
            and isinstance(node.right.right, ast.Constant)
            and type(node.right.right.value) is int and node.right.right.value == 64,
            'Not an explicit synthetic expression')
    return node.left.value + node.right.left.value * node.right.right.value


class Corpus:
    """Authenticate originals and Git commit/tree/blob chains without invoking Git."""

    def __init__(self, document):
        self.sources = document['sources']
        require(set(self.sources) == set(SOURCES)
                and all(self.sources[name]['ref'] == 'sha256:' + identifier
                        for name, identifier in SOURCES.items())
                and document['revisions'] == REVISIONS,
                'Historical source or revision is outside the reviewed catalogue')
        self.raw = {}
        self.objects = {}
        self.entries = []
        for name, source in self.sources.items():
            require(set(source) == {'ref', 'data'}, 'Unknown historical source fields')
            raw = unpack(source['data'])
            require(source['ref'] == 'sha256:' + digest(raw), 'Corrupt historical source')
            self.raw[name] = raw
        for oid, obj in document['git_objects'].items():
            require(set(obj) == {'kind', 'data'} and obj['kind'] in ('commit', 'tree', 'blob'),
                    'Unknown Git proof object')
            raw = unpack(obj['data'])
            identity = obj['kind'].encode() + b' ' + str(len(raw)).encode() + b'\0' + raw
            require(hashlib.sha1(identity).hexdigest() == oid, 'Corrupt Git proof object')
            self.objects[oid] = (obj['kind'], raw)
        self.revisions = document['revisions']

    def document(self, name):
        return decode(self.raw[name])

    def git(self, revision, path=None):
        oid = self.revisions.get(revision, revision)
        kind, raw = self.objects[oid]
        require(kind == 'commit', 'Expected Git commit')
        tree = raw.split(b'\n', 1)[0]
        require(tree.startswith(b'tree '), 'Missing commit tree')
        oid = tree[5:].decode()
        if path is None:
            return oid
        for part in path.split('/'):
            kind, raw = self.objects[oid]
            require(kind == 'tree', 'Expected Git tree')
            children = {}
            while raw:
                header, raw = raw.split(b'\0', 1)
                _, name = header.split(b' ', 1)
                children[name.decode()] = raw[:20].hex()
                raw = raw[20:]
            if part not in children:
                return None
            oid = children[part]
        kind, raw = self.objects[oid]
        require(kind == 'blob', 'Expected Git blob')
        return raw

    def event(self, name, index, status='completed', exit_code=0):
        event = self.document(name)['events'][index]
        item = event['params']['item']
        require(event['method'] == 'item/completed' and item['type'] == 'commandExecution'
                and item['status'] == status and type(item['exitCode']) is int
                and item['exitCode'] == exit_code, 'Not the required completed command receipt')
        require(isinstance(item['command'], str) and (item['aggregatedOutput'] is None
                or isinstance(item['aggregatedOutput'], str)),
                'Missing command bytes')
        return event

    def receipt(self, name, index, status='completed', exit_code=0):
        event = self.event(name, index, status, exit_code)
        item = event['params']['item']
        return {'ref': self.sources[name]['ref'], 'selector': f'/events/{index}',
                'command_hex': digest(item['command'].encode()),
                'output_hex': digest(b'null' if item['aggregatedOutput'] is None
                                     else item['aggregatedOutput'].encode()),
                'output_encoding': 'json-null' if item['aggregatedOutput'] is None else 'utf-8',
                'status': status, 'exit_code': exit_code, 'item_id': item['id']}

    def emit(self, name, selector, token, origins, bindings, offsets=None):
        owner, key = pointer(self.document(name), selector)
        scalar = owner[key].encode()
        positions = ([m.start() for m in re.finditer(re.escape(token.encode()), scalar)]
                     if offsets is None else offsets)
        require(positions, 'Missing expected copy occurrence')
        for start in positions:
            require(scalar[start:start + 71] == token.encode(), 'Unbound copy interval')
            scalar[:start].decode()
            scalar[start + 71:].decode()
            self.entries.append({
                'parent': self.sources[name]['ref'], 'selector': selector,
                'selector_hex': digest(scalar), 'start': start, 'end': start + 71,
                'identifier': {'namespace': ('oci-image-operand' if any(
                    b.get('namespace') == 'oci-image-operand' for b in bindings)
                    else 'isolated-test-token'), 'hex': token[7:]},
                'origins': sorted({self.sources[n]['ref'] for n in origins}),
                'bindings': bindings,
            })

    def output(self, name, index, token, origins, bindings, targets=None,
               status='completed', exit_code=0):
        event = self.event(name, index, status, exit_code)
        params, item = event['params'], event['params']['item']
        output = item['aggregatedOutput']
        targets = [index] if targets is None else targets
        bindings = bindings + [self.receipt(name, index, status, exit_code)]
        for target in targets:
            if target == index:
                selector = f'/events/{target}/params/item/aggregatedOutput'
            else:
                other = self.document(name)['events'][target]
                p = other['params']
                require(other['method'] == 'item/commandExecution/outputDelta'
                        and p['itemId'] == item['id']
                        and all(p[k] == params[k] for k in ('threadId', 'turnId'))
                        and p['delta'] and output.count(p['delta']) == 1, 'Unbound command delta')
                selector = f'/events/{target}/params/delta'
            self.emit(name, selector, token, origins, bindings)

    def blob_binding(self, revision, path):
        raw = self.git(revision, path)
        require(raw is not None, 'Missing Git source')
        return {'revision': self.revisions[revision], 'tree': self.git(revision),
                'path': path, 'source_hex': digest(raw)}

    def added_file(self, name, revision, path, token, origins, bindings, base='base'):
        doc = self.document(name)
        diff = doc['independent_diff']
        candidate = doc['candidate']
        require(candidate['revision'] == self.revisions[revision]
                and candidate['tree'] == self.git(revision)
                and candidate['base'] == self.revisions[base]
                and all(diff[k] == candidate[k] for k in ('base', 'revision', 'tree')),
                'Swapped diff candidate/base/tree')
        require(self.git(base, path) is None, 'Diff source is not a new file')
        blob = self.git(revision, path)
        lines = blob.decode().splitlines(keepends=True)
        section = (f'diff --git a/{path} b/{path}\nnew file mode 100644\n')
        text = diff['diff']
        require(text.count(section) == 1, 'Unknown Git diff section')
        begin = text.index(section)
        end = text.find('\ndiff --git ', begin + len(section))
        chunk = text[begin:] if end < 0 else text[begin:end + 1]
        blob_oid = hashlib.sha1(b'blob ' + str(len(blob)).encode() + b'\0' + blob).hexdigest()
        expected = (section + f'index 0000000..{blob_oid[:7]}\n--- /dev/null\n+++ b/{path}\n'
                    + f'@@ -0,0 +1,{len(lines)} @@\n' + ''.join('+' + line for line in lines))
        require(chunk == expected, 'Git diff does not reproduce immutable blob bytes')
        start = len(text[:begin].encode())
        positions = [start + m.start() for m in re.finditer(re.escape(token.encode()), chunk.encode())]
        self.emit(name, '/independent_diff/diff', token, origins,
                  bindings + [self.blob_binding(revision, path),
                              {'base': self.revisions[base], 'base_tree': self.git(base)}], positions)


def derive(c):
    """Seven-parent catalogue: each recipe binds whole source context before ranges.

    These are historical failed/control executions, not fresh test qualification.
    No shell, archived Python, provider, or arbitrary expression is executed here.
    """
    from codex_harness.adapters.record_references import _python_runner_references

    runner = c.raw['runner'].decode()
    runner_tokens = re.findall(r'sha256:[0-9a-f]{64}', runner)
    require(len(runner_tokens) == 1 and not _python_runner_references(runner),
            'Runner token is not the unique parsed Docker image operand')
    image = runner_tokens[0]
    runner_binding = {'ref': c.sources['runner']['ref'], 'source_hex': digest(c.raw['runner']),
                      'namespace': 'oci-image-operand'}
    event = c.event('runner_execution', 89)['params']['item']
    reader = decode(event['aggregatedOutput'])
    require(reader['content'].encode() == c.raw['runner']
            and reader['ref'] == c.sources['runner']['ref'] and reader['cursor'] == 0
            and reader['next_cursor'] is None and reader['truncated'] is False
            and f"--ref {reader['ref']} page --cursor 0 --limit 8000" in shell(event['command']),
            'Reader copy not bound to full runner bytes')
    c.output('runner_execution', 89, image, ['runner_execution', 'runner'], [runner_binding])

    test_path = 'tests/test_reference_kinds.py'
    test = c.git('runner_candidate', test_path).decode()
    cmd = c.event('runner_execution', 424)['params']['item']['command']
    script = shell(cmd)
    match = re.fullmatch(r"cat >> tests/test_reference_kinds.py <<'EOF'\n(.*)\nEOF\n"
                         r'uv run pytest tests/test_reference_kinds.py -q', script, re.S)
    require(match is not None, 'Unknown test source append command')
    require(c.git('runner_candidate', 'tests/fixtures/reference_runner/original.txt') == c.raw['runner'],
            'Runner fixture differs from original artifact')
    parsed = ast.parse(match[1])
    function = next(n for n in parsed.body if isinstance(n, ast.FunctionDef)
                    and n.name == 'test_original_python_runner_bytes_are_classified_without_execution')
    committed_function = next(n for n in ast.parse(test).body if isinstance(n, ast.FunctionDef)
                              and n.name == function.name)
    require(ast.get_source_segment(match[1], function) == ast.get_source_segment(test, committed_function)
            and match[1].count(image) == 1, 'Unbound appended test function bytes')
    constants = [n.value for n in ast.walk(function) if isinstance(n, ast.Constant)]
    require(image in constants and c.sources['runner']['ref'][7:] in constants,
            'Test assertion lacks original runner/source identity')
    binding = [runner_binding, c.blob_binding('runner_candidate', test_path),
               c.receipt('runner_execution', 424)]
    for index in (182, 424):
        e = c.document('runner_execution')['events'][index]
        p = e['params']
        origin = c.event('runner_execution', 424)['params']
        require(e['method'] == ('item/started' if index == 182 else 'item/completed')
                and all(p[k] == origin[k] for k in ('threadId', 'turnId'))
                and p['item']['id'] == origin['item']['id'] and p['item']['command'] == cmd
                and p['item']['commandActions'][0]['command'] == script, 'Unbound command copy')
        for tail in ('command', 'commandActions/0/command'):
            c.emit('runner_execution', f'/events/{index}/params/item/{tail}', image,
                   ['runner_execution', 'runner'], binding)

    diagnostic_path = 'docs/evidence/python-runner-rework/negative-control.json'
    result = decode(c.git('runner_candidate', diagnostic_path))
    event = c.event('runner_execution', 308)['params']['item']
    require(decode(event['aggregatedOutput']) == result
            and result['runner_ref'] == c.sources['runner']['ref']
            and result['revision'] == c.revisions['rework']
            and result['decoder_sha256'] == digest(c.git('rework', 'src/codex_harness/adapters/record_references.py'))
            and result['observed_dependencies'] == [image] and result['expected_dependencies'] == []
            and result['result'] == 'reproduced incorrect image dependency', 'Unbound diagnostic result')
    cmd = shell(event['command'])
    require("['git', 'show', '19c4d73:src/codex_harness/adapters/record_references.py']" in cmd
            and "'runner_ref': 'sha256:' + hashlib.sha256(runner.encode()).hexdigest()" in cmd
            and "'observed_dependencies': sorted(refs)" in cmd
            and "refs = namespace['artifact_references'](runner, source='baldrix-budget-probe-runner')" in cmd,
            'Unknown diagnostic computation')
    binding = [runner_binding, c.blob_binding('runner_candidate', diagnostic_path),
               c.blob_binding('rework', 'src/codex_harness/adapters/record_references.py')]
    c.output('runner_execution', 308, image, ['runner_execution', 'runner'], binding, [307, 308])
    later = c.event('runner_review', 640)['params']['item']
    blob = c.git('runner_candidate', diagnostic_path).decode()
    require(blob in later['aggregatedOutput'] and f'cat {diagnostic_path}' in shell(later['command']),
            'Unbound later diagnostic copy')
    c.output('runner_review', 640, image, ['runner_review', 'runner_execution', 'runner'],
             binding + [c.receipt('runner_execution', 308)])

    # Pytest's literal fixture is proven from the exact tested Git source and
    # preserved validation receipt, not from its repeated-character appearance.
    test = c.git('rework', test_path).decode()
    restored = c.git('restored', test_path).decode()
    shown = c.event('pytest_execution', 154)['params']['item']
    restore = c.event('pytest_execution', 164)['params']['item']
    require(restored in shown['aggregatedOutput']
            and f"git restore --source={c.revisions['restored']} -- " in shell(restore['command'])
            and test_path in shell(restore['command']), 'Unbound original pytest source restore')
    append = shell(c.event('pytest_execution', 489)['params']['item']['command'])
    prefix = "cat >> tests/test_reference_kinds.py <<'PY'\n"
    require(append.startswith(prefix), 'Unknown test append')
    addition, separator, _ = append[len(prefix):].partition('\nPY\n')
    require(separator, 'Incomplete test append')
    restored += addition + '\n'
    edit = shell(c.event('pytest_execution', 591)['params']['item']['command'])
    prefix = "python - <<'PY'\n"
    require(edit.startswith(prefix) and edit.endswith('\nPY'), 'Unknown test edit wrapper')
    program = edit[len(prefix):-3]
    marker = "p=Path('tests/test_reference_kinds.py');"
    require(program.count(marker) == 1, 'Unknown test edit target')
    statements = ast.parse(program.split(marker)[1]).body
    require(len(statements) == 3, 'Unexpected test source mutation')
    for index, statement in enumerate(statements[:2]):
        require(isinstance(statement, ast.Assign) and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name) and statement.targets[0].id == 's'
                and isinstance(statement.value, ast.Call) and not statement.value.keywords
                and len(statement.value.args) == 2, 'Unknown test replacement')
        call = statement.value
        expected_receiver = ast.parse('p.read_text()' if index == 0 else 's', mode='eval').body
        require(isinstance(call.func, ast.Attribute) and call.func.attr == 'replace'
                and ast.dump(call.func.value) == ast.dump(expected_receiver), 'Unknown replacement receiver')
        old, new = [ast.literal_eval(arg) for arg in call.args]
        require(isinstance(old, str) and isinstance(new, str) and old in restored,
                'Unbound test replacement arguments')
        restored = restored.replace(old, new)
    require(ast.dump(statements[-1]) == ast.dump(ast.parse('p.write_text(s)').body[0])
            and restored == test, 'Historical test mutations do not reproduce tested Git blob')
    parsed = ast.parse(test)
    assignment = next(n for n in parsed.body if isinstance(n, ast.Assign)
                      and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'IMAGE')
    token = constant(ast.get_source_segment(test, assignment.value))
    name = 'test_buildkit_progress_only_excludes_complete_identity_lines'
    function = next(n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name == name)
    function_lines = ast.get_source_segment(test, function).splitlines()[:6]
    log_path = 'docs/evidence/reference-rework/intermediate-pytest.json'
    manifest_path = 'docs/evidence/reference-rework/intermediate-validation.json'
    log_bytes = c.git('rework', log_path)
    log = decode(log_bytes)['stdout_stderr']
    manifest = decode(c.git('rework', manifest_path))
    receipt = next(r for r in manifest['commands'] if r['argv'] == ['uv', 'run', 'pytest'])
    require(receipt['exit_code'] == 1 and receipt['sha256'] == digest(log_bytes)
            and receipt['stdout_stderr_sha256'] == digest(log.encode())
            and manifest['tested_files'][test_path] == digest(test.encode()), 'Unbound pytest test/log bytes')
    binding = ([c.blob_binding('rework', p) for p in (test_path, log_path, manifest_path)]
               + [c.blob_binding('restored', test_path)]
               + [c.receipt('pytest_execution', i) for i in (154, 164, 489, 591)])
    for index, targets, status, code in ((796, [795, 796], 'failed', 1),
                                         (886, [884, 886], 'completed', 0)):
        item = c.event('pytest_execution', index, status, code)['params']['item']
        output = item['aggregatedOutput']
        require(all(line in output for line in function_lines)
                and f'{test_path}:114: AssertionError' in output
                and f'FAILED {test_path}::{name}' in output
                and f"E         '{token}'" in output, 'Not the source-bound pytest failure')
        if index == 796:
            require(shell(item['command']) == 'uv run pytest tests/test_reference_kinds.py '
                    'tests/test_maintenance.py tests/test_measurements.py --runxfail -q',
                    'Unknown focused pytest command')
        else:
            require(log[-1200:] in output and "r.stdout.decode()[-1200:]" in shell(item['command'])
                    and "('pytest',['uv','run','pytest'])" in shell(item['command']),
                    'Completed wrapper does not bind failed pytest output')
        c.output('pytest_execution', index, token, ['pytest_execution'], binding, targets, status, code)
    c.added_file('pytest_diff', 'rework', log_path, token, ['pytest_diff', 'pytest_execution'],
                 binding + [c.receipt('pytest_execution', 886)])

    # The later local diagnostic uses an explicit literal; it never creates an
    # artifact for that value. Preserve the actual child experiment in V1.
    item = c.event('loop_execution', 297)['params']['item']
    script = shell(item['command'])
    expected = '''uv run python - <<'PY'
from codex_harness.adapters.record_references import artifact_references
r = 'sha256:' + 'a'*64
for prefix in ('', 'log [unfinished ', 'log {unfinished '):
    payload = prefix + '{"candidate":{},"image":"'+r+'","image":"unknown"}'
    print(repr(payload), sorted(artifact_references({'stdout':payload})))
PY'''
    require(script == expected, 'Unknown synthetic loop program')
    token = constant("'sha256:' + 'a'*64")
    lines = [repr(prefix + '{"candidate":{},"image":"' + token + '","image":"unknown"}')
             + ' ' + repr([token] if not prefix else []) + '\n'
             for prefix in ('', 'log [unfinished ', 'log {unfinished ')]
    require(item['aggregatedOutput'].endswith(''.join(lines)), 'Unbound loop diagnostic output')
    c.output('loop_execution', 297, token, ['loop_execution'],
             [{'expression': "'sha256:' + 'a'*64", 'namespace': 'isolated-test-token'}], [296, 297])

    path = 'docs/evidence/reference-prefix-rework/negative-control.json'
    blob = c.git('prefix', path)
    value = decode(blob)
    item = c.event('prefix_execution', 352)['params']['item']
    cmd = shell(item['command'])
    token = constant("'sha256:'+'2'*64")
    require("ref='sha256:'+'2'*64" in cmd and f"Path('{path}').write_text" in cmd
            and "'input':body,'expected':[ref],'actual':sorted(result)" in cmd
            and "source=subprocess.check_output(['git','show','19c4d73:src/codex_harness/adapters/record_references.py'],text=True)" in cmd
            and "Rejected decoder reproduced: True" in item['aggregatedOutput'],
            'Unbound prefix diagnostic command')
    require(value == {'revision': c.revisions['rework'],
                      'input': {'stdout': 'log [unfinished {"candidate":{},"image":"' + token
                                + '","image":"unknown"}'},
                      'expected': [token], 'actual': [], 'defect_reproduced': True},
            'Changed historical negative-control result')
    binding = [c.receipt('prefix_execution', 352), c.blob_binding('prefix', path),
               c.blob_binding('rework', 'src/codex_harness/adapters/record_references.py'),
               {'expression': "'sha256:'+'2'*64", 'namespace': 'isolated-test-token'}]
    c.added_file('prefix_diff', 'prefix', path, token, ['prefix_diff', 'prefix_execution'], binding)
    item = c.event('prefix_review', 1053)['params']['item']
    require(blob.decode() in item['aggregatedOutput'] and f'cat {path}' in shell(item['command']),
            'Unbound printed prefix diagnostic')
    c.output('prefix_review', 1053, token, ['prefix_review', 'prefix_execution'], binding)
    derive_malformed(c)
    from codex_harness.adapters.printed_provenance import derive_printed
    derive_printed(c)
    return c.entries


def derive_malformed(c):
    """INV-RESOURCE-001: bind the new production blocker to its original experiment."""
    path = 'docs/evidence/malformed-prefix-rework/reproduction.json'
    decoder = 'src/codex_harness/adapters/record_references.py'
    item = c.event('malformed_execution', 821)['params']['item']
    command = shell(item['command'])
    # The entire archived program is matched as data, never executed by the loader.
    expected = '''uv run python - <<'PY' > docs/evidence/malformed-prefix-rework/reproduction.json
import hashlib
import json
import subprocess
from pathlib import Path
reference = 'sha256:' + '1' * 64
body = '{,"candidate":{},"image":"' + reference + '","image":"unknown"}'
path = 'src/codex_harness/adapters/record_references.py'
results = []
for revision in ['445fbc8859e896b90e974ed69447ce58e3446251', 'b42e0955e3ecf12e54fd4190b6b310a16f44a544', 'working-tree']:
    source = Path(path).read_bytes() if revision == 'working-tree' else subprocess.check_output(['git', 'show', revision + ':' + path])
    namespace = {}
    exec(compile(source, path, 'exec'), namespace)
    results.append({'revision': revision, 'decoder_sha256': hashlib.sha256(source).hexdigest(),
                    'plain': sorted(namespace['artifact_references']({'stdout': body})),
                    'envelope': sorted(namespace['artifact_references'](json.dumps({'stdout': body})))})
print(json.dumps({'input': body, 'results': results}, indent=2))
PY'''
    require(command == expected, 'Unknown malformed reproduction program')
    token = constant("'sha256:' + '1' * 64")
    blob = c.git('malformed', path)
    result = {'input': '{,"candidate":{},"image":"' + token + '","image":"unknown"}',
              'results': []}
    for revision, reported, values in (
            ('malformed_base', c.revisions['malformed_base'], [token]),
            ('malformed_rejected', c.revisions['malformed_rejected'], []),
            ('malformed', 'working-tree', [token])):
        result['results'].append({'revision': reported,
                                  'decoder_sha256': digest(c.git(revision, decoder)),
                                  'plain': values, 'envelope': values})
    require(blob == (json.dumps(result, indent=2) + '\n').encode(),
            'Changed malformed reproduction source/results')
    printed = c.event('malformed_execution', 894)['params']['item']
    require(shell(printed['command']) == f'git diff -- {decoder} && cat {path} '
            '&& tail -5 docs/evidence/malformed-prefix-rework/pytest.log'
            and printed['aggregatedOutput'].count(blob.decode()) == 1,
            'Unbound malformed reproduction output')
    bindings = [c.receipt('malformed_execution', index) for index in (821, 894)]
    bindings += [c.blob_binding(revision, decoder) for revision in
                 ('malformed_base', 'malformed_rejected', 'malformed')]
    bindings.append({'expression': "'sha256:' + '1' * 64", 'namespace': 'isolated-test-token'})
    c.added_file('malformed_diff', 'malformed', path, token,
                 ['malformed_diff', 'malformed_execution'], bindings, base='malformed_base')


class HistoricalCopies:
    def __init__(self, data):
        self.revision = digest(data)
        document = decode(data)
        require(set(document) == {'version', 'sources', 'git_objects', 'revisions', 'occurrences'}
                and type(document['version']) is int and document['version'] == 1,
                'Unknown historical copy schema')
        corpus = Corpus(document)
        entries = derive(corpus)
        # JSON type identity matters: Python equality conflates False/0 and 1/1.0.
        require(json.dumps(entries, sort_keys=True)
                == json.dumps(document['occurrences'], sort_keys=True),
                'Copy annotations differ from verified derivations')
        self._entries = {}
        for entry in entries:
            group = self._entries.setdefault(entry['parent'], [])
            require(all(e['selector'] != entry['selector'] or entry['end'] <= e['start']
                        or entry['start'] >= e['end'] for e in group), 'Overlapping historical copies')
            group.append(entry)

    def project(self, parent, original, projected):
        entries = self._entries.get(parent, [])
        if not entries:
            return projected, set()
        require(parent == 'sha256:' + digest(original), 'Stale historical copy parent')
        source, target = decode(original), decode(projected)
        origins = set()
        for entry in sorted(entries, key=lambda e: (e['selector'], -e['start'])):
            owner, key = pointer(source, entry['selector'])
            scalar = owner[key].encode()
            require(digest(scalar) == entry['selector_hex'], 'Stale historical selector')
            start, end = entry['start'], entry['end']
            require(scalar[start:end] == ('sha256:' + entry['identifier']['hex']).encode(),
                    'Stale historical interval')
            owner, key = pointer(target, entry['selector'])
            scalar = owner[key].encode()
            require(scalar[start:end] == ('sha256:' + entry['identifier']['hex']).encode(),
                    'Overlapping provenance versions')
            owner[key] = (scalar[:start] + b'TEST_TOKEN:' + scalar[start + 7:]).decode()
            origins.update(entry['origins'])
        return json.dumps(target, ensure_ascii=False).encode(), origins


class CombinedProvenance:
    def __init__(self, original, copies):
        self.original, self.copies = original, copies
        self.revision = digest((original.revision + copies.revision).encode())

    def project(self, parent, content):
        projected, origins = self.original.project(parent, content)
        projected, copied_origins = self.copies.project(parent, content, projected)
        return projected, origins | copied_origins
