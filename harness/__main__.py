import argparse
import json
from pathlib import Path

from . import backend, frontend
from .container import ContainerService
from .packages import PILOT, artifact_digest, blind_package, judge_order, prepare, review_package
from .results import correction_message, evaluate_cases


def main():
    parser = argparse.ArgumentParser(description='Pilot preparation and private black-box evaluation')
    subs = parser.add_subparsers(dest='operation', required=True)
    prep = subs.add_parser('prepare')
    prep.add_argument('project', choices=['frontend-001', 'backend-001'])
    prep.add_argument('arm', choices=list('ABCDE'))
    prep.add_argument('output', type=Path)
    evaluate = subs.add_parser('evaluate')
    evaluate.add_argument('project', choices=['frontend-001', 'backend-001'])
    evaluate.add_argument('source', type=Path)
    evaluate.add_argument('--runtime', choices=['python', 'node'], required=True)
    evaluate.add_argument('--adapter', type=Path)
    evaluate.add_argument('--output', type=Path, required=True)
    package = subs.add_parser('package')
    package.add_argument('project', choices=['frontend-001', 'backend-001'])
    package.add_argument('source', type=Path)
    package.add_argument('--public', type=Path, required=True)
    package.add_argument('--private', type=Path, required=True)
    package.add_argument('--metadata', type=Path, required=True, help='Private JSON run/arm/phase mapping')
    order = subs.add_parser('judge-order')
    order.add_argument('public', type=Path)
    review = subs.add_parser('review-package', help='Attest that an operator inspected all identity leaks')
    review.add_argument('package', type=Path)
    review.add_argument('--private', type=Path, required=True)
    review.add_argument('--reviewer', required=True)
    correction = subs.add_parser('correction')
    correction.add_argument('project', choices=['frontend-001', 'backend-001'])
    correction.add_argument('report', type=Path)
    args = parser.parse_args()
    if args.operation == 'prepare':
        print(json.dumps(prepare(args.project, args.arm, args.output)))
    elif args.operation == 'package':
        print(json.dumps(blind_package(args.source, args.project, args.public, args.private,
                                       json.loads(args.metadata.read_text()))))
    elif args.operation == 'judge-order':
        print(json.dumps(judge_order(args.public)))
    elif args.operation == 'review-package':
        review_package(args.package, args.private, args.reviewer)
    elif args.operation == 'correction':
        card = json.loads((PILOT / args.project / 'intent-card.json').read_text())
        report = json.loads(args.report.read_text())
        if report['project_id'] != args.project:
            parser.error('Report project differs from the selected intent card')
        print(correction_message(card, report))
    else:
        initial_digest = artifact_digest(args.source)
        card = json.loads((PILOT / args.project / 'intent-card.json').read_text())
        factory = lambda: ContainerService(args.source, args.runtime)
        if args.project == 'backend-001':
            report = evaluate_cases(card, backend.cases(), factory)
        else:
            if not args.adapter:
                parser.error('frontend evaluation requires an independently reviewed adapter')
            adapter = json.loads(args.adapter.read_text())
            if adapter.get('artifact_digest') != artifact_digest(args.source):
                parser.error('UI adapter is not bound to this artifact digest')
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                with pw.chromium.launch(headless=True) as browser:
                    report = evaluate_cases(card, frontend.cases(),
                                            lambda: frontend.browser_subject(factory, browser, adapter))
        if artifact_digest(args.source) != initial_digest:
            raise RuntimeError('Artifact source changed during evaluation; discard measurement')
        report['artifact_digest'] = initial_digest
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        print(json.dumps({'complete': report['complete'], 'measurement_errors': report['measurement_errors']}))
        return 0 if report['complete'] else 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
