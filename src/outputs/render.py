from common import *
LABELS={'sudden':'🔥 오늘 갑자기 뜬 것','persistent':'📈 계속 상승 중','new_entries':'🆕 새롭게 등장','falling':'📉 관심 감소','linked':'🔗 같이 움직이는 키워드','observations':'💡 오늘의 관찰','ideas':'💼 활용 아이디어'}
def render(out,inp,editorial):
 facts={f['id']:f for f in inp['facts']}
 def block(b):
  tag={'interpretation':'LLM Interpretation','hypothesis':'LLM Hypothesis','idea':'LLM Idea'}[b['claim_type']]
  text=f"**{tag}**: {b['text']}\n"
  for ref in b['fact_refs']:
   f=facts[ref];text+=f"\n- **{f['type']} [{ref}]**: {f['text']}\n"
  return text+'\n'
 header=f"# Daily Trend Brief — {inp['report_date']}\n\n편집 검토용 초안. 수집 시각: {inp['collected_at']}. NOW는 한국 공식 RSS가 반환한 항목만 포함합니다. FASHION: {inp['coverage']['FASHION']}.\n\n"
 if editorial is None:
  (out/'daily_brief.md').write_text(header+'LLM 편집 미실행. 아래는 원천 관측값입니다.\n\n'+'\n'.join(f"- **{f['type']}**: {f['text']}" for f in inp['facts']),encoding='utf-8');return
 r=editorial['report'];text=header+'## 오늘의 한 줄\n\n'+block(r['one_line'])
 for name,label in LABELS.items():
  text+='## '+label+'\n\n'
  text+=''.join(block(b) for b in r['sections'][name]) if r['sections'][name] else '판정할 수 있는 지표가 없어 생략했습니다.\n\n'
 (out/'daily_brief.md').write_text(text,encoding='utf-8')
 for channel,blocks in r['channels'].items():
  (out/(channel+'.md')).write_text('# '+channel.title()+' — '+inp['report_date']+'\n\n편집 검토용 초안. 자동 게시하지 않습니다.\n\n'+''.join(block(b) for b in blocks),encoding='utf-8')
 dump(out/'website.json',{'date':inp['report_date'],'facts':inp['facts'],'metrics':inp['observed'],'editorial':r['channels']['website'],'coverage':inp['coverage']})
