import json,re,hashlib,unicodedata,sys,io
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import urljoin,urlparse
import requests,fitz
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent; SITE=ROOT/'site'; BOARD='https://www.mfds.go.kr/brd/m_627/list.do'
KINDS={'의약품 등':r'^의약품\s*등\s*시험\s*[·‧․]?\s*검사기관\s*지정\s*현황','화장품':r'^화장품\s*시험\s*[·‧․]?\s*검사기관\s*지정\s*현황'}
def read(name):return json.loads((SITE/name).read_text(encoding='utf8'))
def write(name,obj):
 p=SITE/name; tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8');tmp.replace(p)
def clean(s):return ' '.join((s or '').split())
def key(s):return re.sub(r'[^가-힣a-z0-9]','',re.sub(r'주식회사|\(주\)|\(재\)|\(사\)','',unicodedata.normalize('NFKC',s).lower()))
def parse(blob,kind):
 doc=fitz.open(stream=blob,filetype='pdf'); cos=kind=='화장품'; rows=[]; active=None; groups=[]; seen=set(); lastnum=0
 head=doc[0].get_text(); expected=int(re.search(r'\((\d+)\s*개소\)',head)[1]); assert kind.replace(' ','') in head.replace(' ','')
 for pi,p in enumerate(doc,1):
  text=p.get_text(); title=next((x for x in text.splitlines()[:5] if re.match(r'^\d+\s*\.',x)),None)
  tables=p.find_tables().tables
  listing=[t for t in tables if '대표자' in ' '.join(x or '' for x in t.extract()[0])]
  if listing:
   assert active is None
   for t in listing:
    raw=t.extract(); cols=[i for i,x in enumerate(raw[0]) if x is not None]; assert len(cols)==(7 if cos else 8)
    for rr in raw[1:]:
     r=[clean(rr[i]) for i in cols];
     if not r[0].isdigit():continue
     n=int(r[0]); ident,name,_,addr=r[1:5]; fields=['화장품'] if cos else [f for f in ['의약품','의약외품','한약'] if f in r[5]]; scope=re.sub(r'분석가능\s*항목','',r[-2]).strip(); expiry=re.search(r'\d{2,4}\.\s*\d{1,2}\.\s*\d{1,2}\.?',r[-1]); phone=re.search(r'☎\s*(.*?)(?:FAX|$)',addr,re.I); address=re.split(r'☎|FAX',addr)[0].strip(); assert name and address and fields and scope and expiry and phone and re.search(r'제\s*\d+호',ident)
     rows.append(dict(n=n,name=name,id=ident,address=address,phone=phone[1].strip(),fields=fields,scope=scope,expiry=expiry[0].replace(' ',''),source=kind,page=pi,tests=[] if not cos else [[x+' 검사',pi,''] for x in ['이화학','미생물'] if x in scope]))
   continue
  if cos:raise ValueError('Unexpected cosmetics page')
  if title:
   label=key(re.sub(r'^\d+\s*\.','',title)); matches=[r for r in rows if key(r['name'])==label or (min(len(key(r['name'])),len(label))>5 and (key(r['name']) in label or label in key(r['name'])))]
   if not matches and '한의학진흥원' in title: matches=[r for r in rows if '한의약진흥원' in r['name']]
   if len(matches)>1: matches=[r for r in matches if r['n']==len(seen)+1]
   assert len(matches)==1,(pi,title); active=matches[0]; assert active['n']==len(seen)+1,(pi,'Unexpected detail order'); assert active['n'] not in seen; seen.add(active['n']); groups=[];lastnum=0
  assert active and len(tables)==1,(pi,'detail table'); rr=tables[0].extract(); product='경북테크노파크' in active['name'] and not cos
  for row in rr:
   if not any(clean(x) for x in row):continue
   if re.search(r'시험\s*[·‧]?\s*검사\s*항목',clean(' '.join(x or '' for x in row))) and not clean(row[0]).isdigit():continue
   if product:
    if row[0]:groups=[clean(row[0])]
   else:
    assert clean(row[0]).isdigit(),(pi,row); num=int(clean(row[0]));assert num==lastnum+1 or ('바이오인프라' in active['name'] and lastnum==8 and num==10),(pi,num,lastnum);lastnum=num
    if len(groups)!=len(row)-2:groups=['']*(len(row)-2)
    for i,g in enumerate(row[1:-1]):
     if g is not None:groups[i]=clean(g)
   item=clean(row[-1]);assert item,(pi,row);active['tests'].append([item,pi,' / '.join(g for g in groups if g)])
 assert len(rows)==expected and sorted(r['n'] for r in rows)==list(range(1,expected+1));assert all(r['tests'] for r in rows);assert len({re.search(r'제\s*(\d+)호',r['id'])[1] for r in rows})==expected
 return rows

def fetch(session,url):
 assert urlparse(url).scheme=='https' and urlparse(url).hostname in ('www.mfds.go.kr','mfds.go.kr');r=session.get(url,timeout=45,allow_redirects=False);r.raise_for_status();assert r.status_code==200 and len(r.content)<30_000_000;return r

def discover(session):
 found={}
 for page in range(1,6):
  soup=BeautifulSoup(fetch(session,BOARD+'?page='+str(page)).content,'html.parser')
  for a in soup.select('a[href]'):
   title=clean(a.get_text()); kind=next((k for k,v in KINDS.items() if re.search(v,title)),None)
   if not kind or kind in found:continue
   detail=urljoin(BOARD,a['href']);assert '/brd/m_627/view.do' in detail
   ds=BeautifulSoup(fetch(session,detail).content,'html.parser'); candidates=[]
   for link in ds.select('a[href]'):
    href=link['href']; label=clean(link.get_text()); parent=link
    for _ in range(4):
     if parent is None:break
     txt=clean(parent.get_text()); pdfs=re.findall(r'[^\s]*\.pdf',txt,re.I)
     if pdfs and re.search(r'다운\s*받기|다운로드',label+' '+str(link.get('title',''))) and not re.search(r'\.hwpx?',txt,re.I) and '/brd/m_627/down.do' in href:
      candidates.append(urljoin(detail,href));break
     parent=parent.parent
   candidates=list(dict.fromkeys(candidates));assert len(candidates)==1,(kind,'PDF link',candidates)
   date=re.search(r'(20\d\d)\.\s*(\d+)\.\s*(\d+)',title);assert date
   day=f'{int(date[1]):04d}-{int(date[2]):02d}-{int(date[3]):02d}'
   found[kind]=(detail,candidates[0],day,title)
  if len(found)==2:return found
 raise ValueError('Both categories not found')

def main():
 old=read('data.json'); status=read('status.json'); history=read('changes.json'); now=datetime.now(timezone(timedelta(hours=9))).isoformat(timespec='seconds'); errors=[]; new=[]
 session=requests.Session();session.headers['User-Agent']='LabSearch public registry monitor (daily)';
 try: found=discover(session)
 except Exception as e:found={};errors.append(str(e))
 for kind,(detail,url,day,title) in found.items():
  try:
   blob=fetch(session,url).content;assert blob.startswith(b'%PDF-'); digest=hashlib.sha256(blob).hexdigest(); meta=old['sources'][kind]; assert day>=meta['date'],'Older listing';
   if digest==meta['sha256']:continue
   rows=parse(blob,kind); prev=[r for r in old['labs'] if r['source']==kind]; assert .7*len(prev)<=len(rows)<=1.5*len(prev),'Large count change';
   def idx(rs):return {re.search(r'제\s*(\d+)호',r['id'])[1]:r for r in rs}
   a,b=idx(prev),idx(rows); changes=[]
   for k in sorted(a.keys()|b.keys()):
    x,y=a.get(k),b.get(k); fields=[]
    if x and y:
     fields=[f for f in ['name','address','phone','fields','scope','expiry'] if key(str(x[f]))!=key(str(y[f]))]
     if [(key(t[0]),key(t[2])) for t in x['tests']]!=[(key(t[0]),key(t[2])) for t in y['tests']]:fields.append('tests')
     if not fields:continue
     if len(y['tests'])<.7*len(x['tests']):raise ValueError('Large test count decrease: '+y['name'])
    changes.append(dict(type='추가' if not x else '제외' if not y else '변경',name=(y or x)['name'],fields=fields))
   old['labs']=[r for r in old['labs'] if r['source']!=kind]+rows;old['sources'][kind]=dict(date=day,sha256=digest,name=title+'.pdf',url=detail);history.insert(0,dict(time=now,source=kind,changes=changes));new.append(kind)
  except Exception as e:errors.append(kind+': '+str(e))
 if new:write('data.json',old);write('changes.json',history[:100])
 write('status.json',dict(checked=now,state='[확인필요] 수집 또는 검증 실패' if errors else '자동 확인 완료',errors=errors,updated=new))
 print(json.dumps({'updated':new,'errors':errors},ensure_ascii=False))
 return bool(errors)
if __name__=='__main__':
 if len(sys.argv)==3:print(len(parse(Path(sys.argv[1]).read_bytes(),sys.argv[2])))
 else:sys.exit(main())
