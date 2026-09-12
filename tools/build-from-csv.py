#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
يعيد توليد بيانات المنيو المدمجة (const FALLBACK) داخل index.html
من menu.csv و combos.csv، ويربط كل صنف بصورته من assets/img/_map.csv.

الاستخدام:  python tools/build-from-csv.py
"""
import csv, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, 'index.html')
MENU_CSV = os.path.join(ROOT, 'menu.csv')
COMBOS_CSV = os.path.join(ROOT, 'combos.csv')
MAP_CSV = os.path.join(ROOT, 'assets', 'img', '_map.csv')

SECTIONS = [('bakery', 'المخبوزات والحلويات', 'BAKERY & SWEETS'),
            ('hot', 'المشروبات الساخنة', 'HOT COFFEE'),
            ('tea', 'الشاي والماتشا', 'TEA & MATCHA'),
            ('iced', 'المشروبات الباردة', 'ICED COFFEE'),
            ('mojito', 'موهيتو ومنعشات', 'MOJITO & REFRESHERS'),
            ('specialty', 'المختصة', 'SPECIALTY')]
SEC_AR = {ar: sid for sid, ar, _ in SECTIONS}
BADGE = {'الأكثر مبيعاً': 'bestseller', 'جديد': 'new'}
TRUE = ('نعم', 'yes', 'y', '1', 'true', 'صح', '✓')


def truthy(v):
    return str(v or '').strip().lower() in TRUE


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def main():
    if not os.path.exists(MENU_CSV):
        sys.exit('menu.csv غير موجود')

    img_map = {}
    if os.path.exists(MAP_CSV):
        for r in read_csv(MAP_CSV):
            if (r.get('الصنف') or '').strip():
                img_map[r['الصنف'].strip()] = (r.get('img') or '').strip()

    items, seen = [], {}
    for r in read_csv(MENU_CSV):
        if r.get('ظاهر') and not truthy(r['ظاهر']):
            continue
        sec = SEC_AR.get((r.get('القسم') or '').strip())
        ar = (r.get('الصنف') or '').strip()
        if not sec or not ar:
            continue
        key = sec + '|' + ar
        if key not in seen:
            seen[key] = {'sec': sec, 'ar': ar, 'en': (r.get('Item') or '').strip(),
                         'desc': (r.get('الوصف') or '').strip(),
                         'img': img_map.get(ar, (r.get('الصورة') or '').strip()),
                         'badge': BADGE.get((r.get('شارة') or '').strip(), ''),
                         'prices': []}
            items.append(seen[key])
        amt = (r.get('السعر') or '').strip()
        if amt:
            seen[key]['prices'].append({'size': (r.get('الحجم') or '').strip().upper(), 'amt': amt})

    items = [i for i in items if i['prices']]

    combos = []
    if os.path.exists(COMBOS_CSV):
        for n, r in enumerate(read_csv(COMBOS_CSV)):
            if r.get('ظاهر') and not truthy(r['ظاهر']):
                continue
            if not (r.get('الاسم') or '').strip():
                continue
            combos.append({'num': (r.get('رقم') or str(n + 1)).strip(),
                           'name': r['الاسم'].strip(), 'items': (r.get('المكونات') or '').strip(),
                           'save': (r.get('التوفير') or '').strip(),
                           'price': (r.get('السعر') or '').strip(),
                           'featured': bool(truthy(r.get('مميز')))})

    payload = {'sections': [{'id': i, 'ar': a, 'en': e} for i, a, e in SECTIONS],
               'items': items, 'combos': combos}
    line = 'const FALLBACK = ' + json.dumps(payload, ensure_ascii=False, separators=(', ', ': ')) + ';'

    src = open(INDEX, encoding='utf-8').read()
    new, n = re.subn(r'^const FALLBACK = \{.*?\};$', line, src, count=1, flags=re.M)
    if not n:
        sys.exit('لم أجد سطر const FALLBACK داخل index.html')
    open(INDEX, 'w', encoding='utf-8').write(new)

    missing = [i['img'] for i in items
               if i['img'] and not os.path.exists(os.path.join(ROOT, 'assets', 'img', i['img']))]
    print('items: %d | with image: %d | combos: %d' %
          (len(items), sum(1 for i in items if i['img']), len(combos)))
    if missing:
        print('تحذير - صور غير موجودة في assets/img:', missing)


if __name__ == '__main__':
    main()
