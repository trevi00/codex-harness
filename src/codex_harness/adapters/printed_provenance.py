"""Exact historical printed-receipt proof, including clipped output."""
from codex_harness.adapters.record_references import artifact_references
from codex_harness.domain.model import require


def derive_printed(c):
    # INV-RESOURCE-001: neither matching digest values nor a command substring
    # authenticates a copy. Reconstruct the entire observed output from originals.
    parent = 'printed_execution'
    task = c.document('printed_task')
    image = c.document('printed_binding')['image']
    require(c.sources[parent]['ref'] ==
            'sha256:26f4e92f18f03d9eb01b30077a902c3effd02dfbf16284ac940bd7210d00e8d9',
            'Unknown printed execution')
    expected = 'sha256 ' + c.sources['printed_task']['ref'][7:] + '\nkeys ' + str(list(task)) + '\n'
    origins = [parent, 'printed_task']
    for index, validation in enumerate(task['validation']):
        name = 'printed_validation_' + str(index)
        require(c.sources[name]['ref'] == validation['ref'], 'Unbound printed validation source')
        raw = c.raw[name]
        require(len(raw) == validation['bytes'], 'Changed printed validation size')
        if image in raw.decode():
            require(image not in artifact_references(c.document(name)),
                    'Printed source has a mandatory equal-valued reference')
        expected += validation['source'] + ' True\n' + raw.decode()[:2500] + '\n'
        origins.append(name)
    cases = [(138, '935b973bcfde0fc21bf15778963d2ff62faa55639b22a8e5652398a8a3789806', expected, origins)]
    expected = ''
    for name in ('printed_binding', 'printed_canary'):
        raw = c.raw[name]
        if image in raw.decode():
            require(image not in artifact_references(c.document(name)),
                    'Printed binding has a mandatory equal-valued reference')
        expected += c.sources[name]['ref'][7:] + ' True\nintegrity True\n' + raw.decode()[:5500] + '\n'
    cases.append((160, '4636b601dae905575e0a9a0851e5536bf965bd30b6acb5c320cc1adfb2851d64',
                  expected, [parent, 'printed_binding', 'printed_canary']))
    for index, command_hash, expected, origins in cases:
        receipt = c.receipt(parent, index)
        item = c.event(parent, index)['params']['item']
        require(receipt['command_hex'] == command_hash and item['aggregatedOutput'] == expected,
                'Unbound printed command or output')
        c.output(parent, index, image, origins, [receipt])
