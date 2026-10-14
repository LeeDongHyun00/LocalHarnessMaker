"""Browser checks through a separately reviewed, artifact-specific UI mapping."""
import re
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

from playwright.sync_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeout

from .results import MeasurementError, SubmissionError
from .browser_proxy import BrowserProxy


def locate(root, spec):
    if 'role' in spec:
        return root.get_by_role(spec['role'], name=spec['name'], exact=True)
    if 'label' in spec:
        return root.get_by_label(spec['label'], exact=True)
    return root.locator(spec['css'])


class UI:
    def __init__(self, page, context, adapter):
        self.page, self.context, self.adapter = page, context, adapter

    def control(self, key):
        spec = self.adapter['controls'][key]
        if spec is None:
            raise SubmissionError(f'Operator confirmed that required control {key} is absent')
        return locate(self.page, spec)

    def fill(self, key, value):
        try:
            self.control(key).fill(str(value), timeout=2000)
        except PlaywrightTimeout as error:
            raise SubmissionError(f'UI control {key} unavailable') from error

    def settle(self):
        self.page.wait_for_timeout(100)  # rendering only; application operations have bounded timeouts

    def filter(self, value, keyboard=False):
        selector = self.adapter['filters'][value]
        if selector is None:
            raise SubmissionError(f'Operator confirmed that filter {value} is absent')
        element = locate(self.page, selector)
        if selector.get('option') is not None:
            if keyboard:
                self.tab_to(element)
                # Select options with native keys, never select_option in the keyboard scenario.
                options = element.locator('option').evaluate_all('(xs)=>xs.map(x=>x.value)')
                assert selector['option'] in options
                element.press('Home')
                for _ in range(options.index(selector['option'])):
                    element.press('ArrowDown')
                element.press('Enter')
            else:
                element.select_option(selector['option'])
        elif keyboard:
            self.tab_to(element)
            element.press('Space' if selector.get('role') in ('radio', 'checkbox') else 'Enter')
        else:
            element.click(timeout=2000)
        self.settle()

    def add(self, name='우유', quantity=2, expiry='2026-10-15', keyboard=False):
        for key, value in (('name', name), ('quantity', str(quantity)), ('expiry', expiry)):
            if keyboard:
                element = self.control(key)
                self.tab_to(element)
                # fill changes a focused input using browser input events; no pointer action.
                element.fill(value)
            else:
                try:
                    self.fill(key, value)
                except PlaywrightError:
                    if key != 'expiry' or expiry != '2026-02-30':
                        raise
                    # Native date inputs reject impossible strings before app validation.
                    self.control(key).evaluate("(el,v)=>{el.value=v; el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true}));}", value)
        element = self.control('add')
        if keyboard:
            self.tab_to(element)
            element.press('Enter')
        else:
            element.click(timeout=2000)
        self.settle()

    def rows(self):
        rows = self.page.locator(self.adapter['rows'])
        values = []
        for index in range(rows.count()):
            row = rows.nth(index)
            if not row.is_visible():
                continue
            fields = self.adapter['row_fields']
            name = locate(row, fields['name']).inner_text().strip()
            quantity = locate(row, fields['quantity']).inner_text().strip()
            expiry = locate(row, fields['expiry']).inner_text().strip()
            match = re.search(r'(?<![\d.])\d+(?![\d.])', quantity)
            assert match, f'No displayed quantity: {quantity}'
            assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', expiry), f'No ISO displayed expiry: {expiry}'
            values.append((name, int(match.group()), expiry))
        return values

    def names(self):
        return [row[0] for row in self.rows()]

    def consume(self, name='우유', keyboard=False):
        rows = self.page.locator(self.adapter['rows'])
        selected = [rows.nth(i) for i in range(rows.count())
                    if locate(rows.nth(i), self.adapter['row_fields']['name']).inner_text().strip() == name]
        assert len(selected) == 1, f'Expected exactly one visible item {name}'
        element = locate(selected[0], self.adapter['consume'])
        if keyboard:
            self.tab_to(element)
            element.press('Enter')
        else:
            element.click(timeout=2000)
        self.settle()

    def notice(self, key):
        elements = locate(self.page, self.adapter['notices'][key])
        assert any(e.is_visible() and e.inner_text().strip() for e in elements.all()), f'Missing {key} notice'

    def input_error(self):
        elements = locate(self.page, self.adapter['notices']['error'])
        custom = any(e.is_visible() and e.inner_text().strip() for e in elements.all())
        native = self.page.locator('input').evaluate_all('(xs)=>xs.some(x=>!x.validity.valid && !!x.validationMessage)')
        assert custom or native, 'Missing input error explanation'

    def tab_to(self, element):
        for _ in range(100):
            if element.evaluate('(el)=>el === document.activeElement'):
                return
            self.page.keyboard.press('Tab')
        raise SubmissionError('Control cannot be reached using Tab')


@contextmanager
def browser_subject(service_factory, browser, adapter):
    if not adapter.get('review', {}).get('mapping_verified'):
        raise MeasurementError('UI mapping requires independent artifact review')
    with service_factory() as service:
        with BrowserProxy(service.url) as proxy, browser.new_context(
                timezone_id='Asia/Seoul', locale='ko-KR', service_workers='block',
                proxy={'server': proxy.url, 'bypass': '<-loopback>'}) as context:
            def restricted_request(route):
                if route.request.url.startswith(service.url + '/'):
                    route.continue_()
                else:
                    route.abort('blockedbyclient')
            context.route('**/*', restricted_request)
            page = context.new_page()
            page.set_default_timeout(2000)
            page.goto(service.url, wait_until='domcontentloaded')
            yield UI(page, context, adapter)


def cases():
    def empty(ui):
        assert ui.rows() == []
        ui.notice('initial_empty')

    def registration(ui):
        ui.add()
        assert ui.rows() == [('우유', 2, '2026-10-15')]

    def consume_one(ui):
        ui.add()
        ui.consume()
        assert ui.rows() == [('우유', 1, '2026-10-15')]

    def consume_last(ui):
        ui.add(quantity=1)
        ui.consume()
        assert ui.rows() == []

    def setup_dates(ui):
        today = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d')
        assert ui.control('reference').input_value() == today, 'Initial reference date must be local today'
        ui.fill('reference', '2026-10-14')
        for name, expiry in [('요구르트', '2026-10-13'), ('두부', '2026-10-14'),
                             ('우유', '2026-10-15'), ('치즈', '2026-10-16'), ('달걀', '2026-10-20')]:
            ui.add(name, 1, expiry)

    def imminent(ui):
        setup_dates(ui)
        ui.filter('imminent')
        assert set(ui.names()) == {'두부', '우유', '치즈'} and len(ui.rows()) == 3

    def expired(ui):
        setup_dates(ui)
        ui.filter('expired')
        assert ui.names() == ['요구르트']

    def reference(ui):
        setup_dates(ui)
        ui.filter('imminent')
        ui.fill('reference', '2026-10-15')
        ui.settle()
        assert set(ui.names()) == {'우유', '치즈'} and len(ui.rows()) == 2

    def combined(ui):
        ui.fill('reference', '2026-10-14')
        ui.add()
        ui.add('저지방 우유', 1, '2026-10-20')
        ui.add('두부', 1, '2026-10-14')
        ui.filter('imminent')
        ui.fill('search', ' 우유 ')
        ui.settle()
        assert ui.names() == ['우유']
        ui.filter('all')
        ui.fill('search', '우유')
        ui.settle()
        assert ui.names() == ['우유', '저지방 우유'], 'Search must match substrings, not only whole names'

    def ordered(ui):
        ui.add()
        ui.add('두부', 1, '2026-10-14')
        ui.add('치즈', 1, '2026-10-15')
        ui.filter('all')
        ui.fill('search', '')
        ui.settle()
        assert ui.names() == ['두부', '우유', '치즈']

    def reload(ui):
        ui.add()
        ui.consume()
        ui.page.reload(wait_until='domcontentloaded')
        assert ui.rows() == [('우유', 1, '2026-10-15')]

    def reopen(ui):
        ui.add(quantity=1)
        ui.consume()
        url = ui.page.url
        ui.page.close()
        ui.page = ui.context.new_page()
        ui.page.goto(url, wait_until='domcontentloaded')
        assert ui.rows() == []

    def invalid(ui, probes):
        ui.add()
        for name, quantity, expiry in probes:
            ui.add(name, quantity, expiry)
            ui.input_error()
            assert ui.rows() == [('우유', 2, '2026-10-15')], 'Invalid registration mutated records'

    def invalid_basic(ui):
        invalid(ui, [('   ', 1, '2026-10-15'), ('두부', 0, '2026-10-15'), ('두부', -1, '2026-10-15')])

    def invalid_extended(ui):
        invalid(ui, [('두부', 1.5, '2026-10-15'), ('두부', 1, '2026-02-30')])

    def no_results(ui):
        ui.add()
        ui.fill('search', '사과')
        ui.settle()
        assert ui.rows() == []
        ui.notice('no_results')
        ui.fill('search', '')
        ui.fill('reference', '2026-10-14')
        ui.filter('expired')
        assert ui.rows() == []
        ui.notice('no_results')

    def keyboard(ui):
        ui.add(keyboard=True)
        assert ui.rows() == [('우유', 2, '2026-10-15')]
        ui.tab_to(ui.control('search'))
        ui.control('search').fill('사과')
        ui.settle()
        assert ui.rows() == []
        ui.notice('no_results')
        ui.control('search').fill('우유')
        # Dates are in the past or future depending on evaluation day: explicitly set reference.
        ui.tab_to(ui.control('reference'))
        ui.control('reference').fill('2026-10-14')
        ui.filter('expired', keyboard=True)
        assert ui.rows() == []
        ui.filter('all', keyboard=True)
        assert ui.rows() == [('우유', 2, '2026-10-15')]
        ui.consume(keyboard=True)
        assert ui.rows() == [('우유', 1, '2026-10-15')]
        review = ui.adapter['review']
        for key in ('controls_have_discernible_purpose', 'visible_focus_verified'):
            if review.get(key) is None:
                raise MeasurementError(f'Human accessibility review missing: {key}')
            assert review[key], f'Human accessibility review failed: {key}'

    return dict(zip(['F1.1', 'F1.2', 'F2.1', 'F2.2', 'F3.1', 'F3.2', 'F3.3', 'F4.1',
                     'F4.2', 'F5.1', 'F5.2', 'F6.1', 'F6.2', 'F7.1', 'F7.2'],
                    [empty, registration, consume_one, consume_last, imminent, expired, reference,
                     combined, ordered, reload, reopen, invalid_basic, invalid_extended, no_results, keyboard]))
