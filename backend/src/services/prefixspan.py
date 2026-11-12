from decimal import Decimal,ROUND_CEILING
from collections import defaultdict
from src.constants.domain import MAX_PATTERN_CANDIDATES,MAX_GAP

def mine_patterns(rows,min_support=.1,max_length=3,max_gap=None):
 """PrefixSpan over ordered subsequences.

 max_gap limits how many raw touchpoints may be skipped between two adjacent
 pattern touchpoints (None keeps the historical unlimited behaviour). When a
 journey can match a prefix at several positions, every reachable position is
 kept: a later occurrence may satisfy the gap window even if an earlier one
 cannot. Each journey still contributes at most once to each pattern's support.
 """
 if not rows or not 0<min_support<=1 or not 1<=max_length<=4 or not (max_gap is None or 0<=max_gap<=MAX_GAP):raise ValueError('支持度/模式长度/间隔/样本无效')
 n=len(rows);threshold=max(1,int((Decimal(str(min_support))*n).to_integral_value(rounding=ROUND_CEILING)));groups={g:sum(r['outcome']==g for r in rows) for g in ('converted','exited')};patterns=[];evaluated=0
 def grow(prefix,projected):
  nonlocal evaluated
  # projected: journey index -> end positions (indices into the normalized path)
  # of the current prefix; an empty list means the prefix is empty and the next
  # symbol may start anywhere.
  extensions=defaultdict(dict)
  for idx,ends in projected.items():
   path=rows[idx]['path'];positions=rows[idx].get('positions') or list(range(len(path)))
   if max_gap is None:
    # Unlimited spacing: the earliest end dominates later ones, so keep a single
    # end per suffix symbol for each journey (the original algorithm).
    start=0 if not ends else min(ends)+1
    for pos in range(start,len(path)):
     extensions[path[pos]].setdefault(idx,[pos])
   elif not ends:
    for pos in range(len(path)):extensions[path[pos]].setdefault(idx,[]).append(pos)
   else:
    for end in ends:
     raw_end=positions[end];pos=end+1
     while pos<len(path) and positions[pos]-raw_end-1<=max_gap:
      extensions[path[pos]].setdefault(idx,[]).append(pos)
      pos+=1
  for symbol,suffixes in sorted(extensions.items()):
   evaluated+=1
   if evaluated>MAX_PATTERN_CANDIDATES:raise ValueError('候选模式超过6000，请提高支持度或缩短模式')
   # suffixes is keyed by journey, so multiple matches in one journey still
   # count as a single supporting journey.
   count=len(suffixes)
   if count<threshold:continue
   pattern=prefix+(symbol,);converted=sum(rows[i]['outcome']=='converted' for i in suffixes);exited=count-converted
   cs=converted/groups['converted'] if groups['converted'] else None;es=exited/groups['exited'] if groups['exited'] else None
   patterns.append({'pattern':list(pattern),'count':count,'support':count/n,'converted_count':converted,'exited_count':exited,'converted_support':cs,'exited_support':es,'support_difference':cs-es if cs is not None and es is not None else None})
   if len(pattern)<max_length:grow(pattern,{i:sorted(set(ends)) for i,ends in suffixes.items()})
 grow((),{i:[] for i in range(n)})
 patterns.sort(key=lambda p:(-p['count'],-len(p['pattern']),tuple(p['pattern'])))
 return {'patterns':patterns[:200],'total_patterns':len(patterns),'patterns_truncated':len(patterns)>200,'candidate_patterns_evaluated':evaluated,'min_count':threshold,'group_sizes':groups,'max_gap':max_gap}
