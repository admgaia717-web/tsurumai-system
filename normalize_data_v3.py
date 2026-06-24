#!/usr/bin/env python3
import sys, json, re
from collections import Counter, defaultdict
sys.path.insert(0, '/Users/kt/.pi/agent/skills/mac-mini-m4/productivity/google-workspace/scripts')
from google_api import build_service
svc = build_service('sheets', 'v4')
data = svc.spreadsheets().values().get(spreadsheetId='1kjvKUqOoaxvOcfRFRTC-5X2MKvsvYBsnjk0a6yre0e4', range="'フォームの回答4'!A1:N895").execute().get('values', [])
records = data[1:]

# 公民館のマッピング（KT指示）
KOIKAN_MAP = {
    '学園朝日町・学園朝日元町公民館': r'朝日(町|元町)?公民館|^公民館$',
    '学園前ホール（奈良市西部会館市民ホール）': r'西部公民館|西部会館|学園前ホール',
}

def classify_location(val):
    v = val.strip()
    if re.search(r'UR|Ur', v):
        return 'UR学園前(西)' if re.search(r'西', v) else 'UR学園前(東)'
    if re.search(r'学園前', v) and re.search(r'駅|ロータリー|ミスド|\(予定\)', v):
        return '学園前駅南口ロータリー' if re.search(r'南', v) else '学園前駅北口ロータリー'
    # 公民館（KT指示）
    for name, pat in KOIKAN_MAP.items():
        if re.search(pat, v): return name
    # 医療・商業・駅・団地・公共・店舗・金融（v2と同一・省略）
    for name, pats in {
        '西奈良中央病院':[r'西奈良中央病院',r'奈良にし中央病院'],
        'メディカルコートあやめ池':[r'メディカルコート'],
        '中田整形外科':[r'中田整形'],'くがい整形外科':[r'くがい整形'],
        'まえだ整形外科':[r'まえだ整形'],'青木クリニック':[r'青木クリニック'],
        '中島クリニック':[r'中島クリニック'],'中村脳神経外科':[r'中村脳神経'],
        '栗原歯科':[r'栗原歯科'],'うえなか歯科':[r'うえなか歯科',r'上中歯科'],
        'YAS歯科':[r'YAS歯科',r'歯科YAS'],'平野歯科':[r'平野歯科'],'宮本歯科':[r'宮本歯科'],
        'おおしか鍼灸院':[r'おおしか鍼灸',r'大鹿鍼灸'],'鍼灸院(その他)':[r'鍼灸院'],
        'パラディ':[r'パラディ'],'万代':[r'万代'],
        'コープ/生協':[r'^コープ$',r'生協'],'ハーベス':[r'ハーベス'],
        'トライアル':[r'トライアル'],'イオン登美ヶ丘':[r'イオン登美'],
        'あやめ池駅北口ロータリー':[r'あやめ池駅北|あやめ池北ロータリー'],
        'あやめ池駅南口ロータリー':[r'あやめ池駅南'],
        '菖蒲池駅':[r'菖蒲池駅'],'学研奈良登美ヶ丘駅':[r'学研奈良登美'],
        'エクセルハイツ':[r'エクセル'],'笠井ハウス':[r'笠井ハウス',r'カサイハウス',r'笠井P'],
        'グランドビュー学園前':[r'グランドビュー'],'エスリージュ友舞':[r'エスリージュ'],
        'あすならハイツ':[r'あすならハイツ'],
        '二名包括センター':[r'二名包括',r'ニミョウホウカツ'],
        '西福祉センター':[r'西福祉'],
        '図書館':[r'図書館'],'奈良西郵便局':[r'奈良西郵便局'],
        '西奈良郵便局':[r'西奈良郵便局'],
        'ミスド(学園前)':[r'学園前ミスド',r'ミスド'],
        'カラオケ(ウリ坊)':[r'カラオケ',r'ウリ坊'],'キリン堂':[r'キリン堂'],
        'タマイ美容室':[r'タマイ',r'Tamai'],'スシロー':[r'スシロー'],
        'お好み焼ききんちゃん':[r'きんちゃん'],'MUFG銀行学園前':[r'MUFG'],
        '南都銀行':[r'南都銀行'],'奈良信用金庫':[r'奈良信用金庫'],
    }.items():
        if any(re.search(p, v) for p in pats): return name
    return None

loc_count = Counter()
for r in records:
    for field in [3,4]:
        if len(r)>field and r[field].strip():
            loc = classify_location(r[field])
            if loc: loc_count[loc] += 1
            elif re.search(r'さん宅|さん$|様$|宅$|百代|コーポ', r[field]): loc_count['(個人宅/コーポ)'] += 1

# GoogleマップURL辞書（KT提供）
GOOGLE_MAPS = {
    '学園朝日町・学園朝日元町公民館': 'https://maps.app.goo.gl/gGDgPNEKEdZCbCKT8',
    '学園前ホール（奈良市西部会館市民ホール）': 'https://maps.app.goo.gl/tvAQ8ACSxWcjprs39',
    '西福祉センター': 'https://maps.app.goo.gl/Nzcf3KTDxRR7vUWp6',
}
type_map = {
    '西奈良中央病院':'medical','メディカルコートあやめ池':'medical','中田整形外科':'medical',
    'くがい整形外科':'medical','まえだ整形外科':'medical','青木クリニック':'medical',
    '中島クリニック':'medical','中村脳神経外科':'medical','おおしか鍼灸院':'medical','鍼灸院(その他)':'medical',
    '栗原歯科':'dental','うえなか歯科':'dental','YAS歯科':'dental','平野歯科':'dental','宮本歯科':'dental',
    'パラディ':'commercial','万代':'commercial','コープ/生協':'commercial','ハーベス':'commercial',
    'トライアル':'commercial','イオン登美ヶ丘':'commercial',
    '学園前駅北口ロータリー':'station','学園前駅南口ロータリー':'station','学研奈良登美ヶ丘駅':'station',
    'あやめ池駅北口ロータリー':'station','あやめ池駅南口ロータリー':'station','菖蒲池駅':'station',
    'UR学園前(東)':'housing','UR学園前(西)':'housing','エクセルハイツ':'housing','笠井ハウス':'housing',
    'グランドビュー学園前':'housing','エスリージュ友舞':'housing','あすならハイツ':'housing',
    '学園朝日町・学園朝日元町公民館':'public','学園前ホール（奈良市西部会館市民ホール）':'public',
    '二名包括センター':'public','西福祉センター':'public','図書館':'public',
    '奈良西郵便局':'public','西奈良郵便局':'public',
    'ミスド(学園前)':'shop','カラオケ(ウリ坊)':'shop','キリン堂':'shop',
    'タマイ美容室':'shop','スシロー':'shop','お好み焼ききんちゃん':'shop',
    'MUFG銀行学園前':'finance','南都銀行':'finance','奈良信用金庫':'finance',
}
locations = []
for i,(name,cnt) in enumerate(sorted(loc_count.items(), key=lambda x:-x[1]),1):
    if name=='(個人宅/コーポ)': continue
    locations.append({'location_id':f'L{i:03d}','name':name,
        'type':type_map.get(name,'other'),'reference_count':cnt,
        'google_maps_url':GOOGLE_MAPS.get(name,''),'pin_confirmed':bool(GOOGLE_MAPS.get(name))})

print(f"【場所マスタ v3】{len(locations)}箇所")
print("\n■ 公共施設（公民館修正後）:")
for l in [x for x in locations if x['type']=='public']:
    pin = '✓ピン確定' if l['pin_confirmed'] else '未'
    print(f"  {l['location_id']} {l['name']}: {l['reference_count']}件 [{pin}]")
print(f"\n■ 個人宅/コーポ: {loc_count.get('(個人宅/コーポ)',0)}件（別管理）")
with open('locations_master.json','w') as f: json.dump(locations, f, ensure_ascii=False, indent=2)
print("\n✅ v3保存完了")
