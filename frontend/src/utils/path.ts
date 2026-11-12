import type {Dictionary,Result} from '../types/entities';
export function label(code:string,dictionary:Dictionary){return dictionary.entries.find(e=>e.code===code)?.label||code}
// Archived results predate the gap field: they were mined with unlimited spacing.
export function gapRule(result:Result|{gap_rule?:string;max_gap?:number|null}|undefined|null):string{
 if(result?.gap_rule)return result.gap_rule;
 const g=result?.max_gap;
 return g===null||g===undefined?'相邻模式触点允许跳过任意原始触点（不限间隔）':'相邻模式触点间最多跳过'+g+'个原始触点';
}
