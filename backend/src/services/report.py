import csv,io
from fastapi import HTTPException
from src.models.entities import Report
from src.config.settings import ARTIFACT_DIR
from src.utils import repository as repo
from src.utils.identity import new_id,now

def safe_cell(value):return "'"+value if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')) else value
def list_reports():return repo.all_rows('reports')
def create(data):
 run,review=repo.get('runs',data.run_id),repo.get('reviews',data.review_id)
 if review['status']!='approved' or review['run_id']!=run['id'] or run['status']!='completed':raise ValueError('报告必须引用该运行已通过的复核')
 report=repo.put('reports',Report(new_id('rpt'),data.run_id,data.review_id,data.title,now()));ARTIFACT_DIR.mkdir(parents=True,exist_ok=True);(ARTIFACT_DIR/(report['id']+'.csv')).write_text(download(report['id']),encoding='utf-8');return report
def download(id):
 report=repo.get('reports',id);run=repo.get('runs',report['run_id']);r=run['result']
 if repo.get('reviews',report['review_id'])['status']!='approved':raise HTTPException(403,'复核未通过')
 # Archived runs predate max_gap; their spacing was unlimited by definition.
 gap=r.get('max_gap');gap_rule=r.get('gap_rule') or ('相邻模式触点允许跳过任意原始触点（不限间隔）' if gap is None else f'相邻模式触点间最多跳过{gap}个原始触点')
 out=io.StringIO();w=csv.writer(out)
 w.writerow(['report','journeys','unique_paths','collapse_repeats','max_gap','gap_rule','min_count','total_patterns','patterns_truncated','checksum']);w.writerow([safe_cell(report['title']),r['journeys'],r['unique_paths'],r['collapse_repeats'],'unlimited' if gap is None else gap,safe_cell(gap_rule),r['min_count'],r['total_patterns'],r['patterns_truncated'],r['checksum']])
 w.writerow([]);w.writerow(['pattern','journey_count','support','converted_count','converted_support','exited_count','exited_support','support_difference'])
 for p in r['patterns']:w.writerow(['>'.join(p['pattern']),p['count'],p['support'],p['converted_count'],p['converted_support'],p['exited_count'],p['exited_support'],p['support_difference']])
 w.writerow([]);w.writerow(['group','medoid','journeys','weighted_total_distance','mean_distance'])
 for group,m in r['medoids'].items():
  if m:w.writerow([group,'>'.join(m['path']),m['journeys'],m['weighted_total_distance'],m['mean_distance']])
 w.writerow([]);w.writerow(['exited_path','frequency','nearest_converted_path','edit_distance','operations'])
 for a in r['alignments']:w.writerow(['>'.join(a['exited_path']),a['frequency'],'>'.join(a['converted_path']),a['distance'],';'.join(f"{x['operation']}:{x['from'] or '-'}>{x['to'] or '-'}" for x in a['operations'])])
 w.writerow([]);w.writerow(['support_basis','journeys','converted_group','exited_group']);w.writerow([safe_cell('支持度=journey_count/journeys；组支持度=组内计数/组旅程数；同一旅程每个模式最多计1次，可按上表逐行核对分母'),r['journeys'],r['group_sizes']['converted'],r['group_sizes']['exited']])
 return '﻿'+out.getvalue()
