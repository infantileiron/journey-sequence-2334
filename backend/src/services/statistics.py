import hashlib,json
from src.services.prefixspan import mine_patterns
from src.services.edit_distance import representatives
from src.constants.domain import MAX_UNIQUE_PATHS,MAX_GAP

def analyze(rows,dictionary,study):
 normalized=[]
 codes={e['code'] for e in dictionary['entries']}
 max_gap=study.get('max_gap')
 if max_gap is not None and not 0<=max_gap<=MAX_GAP:raise ValueError('间隔上限无效')
 for r in rows:
  path=r['path'];positions=[]
  if not path or any(x not in codes for x in path):raise ValueError('空路径或未知触点')
  if study['collapse_repeats']:
   # Collapsing adjacent repeats keeps the first touchpoint's raw position, so
   # gap limits still count skipped raw touchpoints.
   path=[];positions=[]
   for i,x in enumerate(r['path']):
    if not path or path[-1]!=x:path.append(x);positions.append(i)
  else:positions=list(range(len(path)))
  normalized.append({**r,'path':path,'positions':positions})
 # Bound medoid work before either algorithm starts.
 if len({tuple(r['path']) for r in normalized})>MAX_UNIQUE_PATHS:raise ValueError('唯一序列超过160，请缩小样本或预先分组')
 patterns=mine_patterns(normalized,study['min_support'],study['max_length'],max_gap);medoids=representatives(normalized)
 gap_rule='相邻模式触点允许跳过任意原始触点（不限间隔）' if max_gap is None else f'相邻模式触点间最多跳过{max_gap}个原始触点'
 return {**patterns,**medoids,'dictionary':dictionary,'study':study,'journeys':len(rows),'raw_events':sum(len(r['path']) for r in rows),'normalized_events':sum(len(r['path']) for r in normalized),'collapse_repeats':study['collapse_repeats'],'max_gap':max_gap,'gap_rule':gap_rule,'checksum':hashlib.sha256(json.dumps({'rows':rows,'dictionary':dictionary,'study':study},sort_keys=True).encode()).hexdigest(),'limitations':['频繁子序列允许中间跳过触点，并非连续片段；支持度分母是旅程数，同一旅程每个模式最多计1次',gap_rule+'；折叠连续重复时以首个触点位置计间隔，同一旅程多处匹配只计一次','转化/退出组支持差仅描述关联；模拟路径不用于因果或通道归因','编辑距离每次插入/删除/替换成本1，保留成本0；medoid按序列频数加权，平局按编码字典序','最近成功路径同距离时优先成功组频数高者，再按字典序；对齐平局优先保留、替换、删除、插入','最多2000旅程、每条20触点、160唯一序列、模式长度4、候选6000；结果最多展示200模式与12条退出对齐']}
