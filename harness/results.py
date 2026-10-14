from contextlib import ExitStack


class MeasurementError(RuntimeError):
    """Evaluator/environment fault, distinct from a failed product requirement."""


class SubmissionError(AssertionError):
    """The submitted artifact cannot satisfy its execution contract."""


def evaluate_cases(card, cases, factory):
    expected = {f"{r['id']}.{i}" for r in card['requirements']
                for i in range(1, len(r['acceptance']) + 1)}
    if set(cases) != expected:
        raise MeasurementError("Evaluator case inventory differs from the intent card")
    results = []
    for case_id, test in cases.items():
        status, detail = "pass", ""
        try:
            with ExitStack() as stack:
                subject = stack.enter_context(factory())
                test(subject)
        except AssertionError as error:
            status, detail = "fail", str(error)
        except Exception as error:
            status, detail = "not_evaluated", f"{type(error).__name__}: {error}"
        results.append({"case_id": case_id, "status": status, "detail": detail})
    requirements = []
    for requirement in card['requirements']:
        statuses = [r['status'] for r in results
                    if r['case_id'].split('.')[0] == requirement['id']]
        status = ("fail" if "fail" in statuses else
                  "not_evaluated" if "not_evaluated" in statuses else "pass")
        requirements.append({"id": requirement['id'], "critical": requirement['critical'],
                             "status": status})
    return {"project_id": card['project_id'], "cases": results,
            "requirements": requirements,
            "complete": all(r['status'] == 'pass' for r in requirements),
            "critical_pass": all(r['status'] == 'pass' for r in requirements if r['critical']),
            "measurement_errors": sum(r['status'] == 'not_evaluated' for r in results)}


def correction_message(card, report):
    """Do not turn a broken measurement into product correction feedback."""
    if report['measurement_errors']:
        raise MeasurementError("Resolve measurement errors before emitting corrections")
    failed = {r['id'] for r in report['requirements'] if r['status'] == 'fail'}
    requirements = sorted(card['requirements'], key=lambda r: (not r['critical'], int(r['id'][1:])))
    return '\n'.join(r['correction_feedback'] for r in requirements if r['id'] in failed)
