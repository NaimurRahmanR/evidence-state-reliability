from __future__ import annotations
import csv,json,os,re
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from typing import Any

TASK='05AG'
STAGES=('decision','audit','escalation')
CONDS=('clean','compressed','partial_dropout','noisy_conflicting')
ROOT=Path(__file__).resolve().parents[1]
IN={
 'dry_run_manifest':ROOT/'reports/pilot_05_cfpb_cascade_scaffold/pilot_05_cfpb_cascade_dry_run_request_manifest.csv',
 'prompt_templates':ROOT/'reports/pilot_05_cfpb_cascade_scaffold/pilot_05_cfpb_cascade_prompt_templates.json',
 'response_schema':ROOT/'reports/pilot_05_cfpb_cascade_scaffold/pilot_05_cfpb_cascade_response_schema.json',
 'parser_rules':ROOT/'reports/pilot_05_cfpb_cascade_scaffold/pilot_05_cfpb_cascade_parser_validation_rules.csv',
 'evidence_state_conditions':ROOT/'reports/pilot_05_cfpb_evidence_state_conditions/pilot_05_cfpb_evidence_state_conditions.csv',
 'evidence_state_labels':ROOT/'reports/pilot_05_cfpb_evidence_state_conditions/pilot_05_cfpb_evidence_state_labels.csv',
 'response_parser':ROOT/'experiments/pilot_05_cfpb_cascade_response_parser.py',
 'parser_smoke_test':ROOT/'experiments/pilot_05_cfpb_cascade_parser_smoke_test.py',
}
OUT=ROOT/'reports/pilot_05_cfpb_cascade_execution_harness'
OUTS={
 'manifest':OUT/'pilot_05_cfpb_cascade_execution_harness_manifest.json',
 'plan':OUT/'pilot_05_cfpb_cascade_execution_plan.csv',
 'batches':OUT/'pilot_05_cfpb_cascade_execution_batches.csv',
 'guardrails':OUT/'pilot_05_cfpb_cascade_execution_guardrails.csv',
 'expected_sanitized_outputs':OUT/'pilot_05_cfpb_cascade_expected_sanitized_outputs.csv',
 'readiness_summary':OUT/'pilot_05_cfpb_cascade_execution_readiness_summary.csv',
}

def die(x:str)->None: raise RuntimeError(f'{TASK} failed: {x}')
def rel(p:Path)->str: return p.relative_to(ROOT).as_posix()
def norm(x:Any)->str: return re.sub(r'[^a-z0-9]+','_',str(x).strip().lower()).strip('_')
def read_csv(p:Path):
    if not p.exists(): die(f'missing csv {rel(p)}')
    with p.open('r',encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    if not rows: die(f'empty csv {rel(p)}')
    return rows
def read_json(p:Path):
    if not p.exists(): die(f'missing json {rel(p)}')
    with p.open('r',encoding='utf-8') as f: return json.load(f)
def write_csv(p:Path, rows:list[dict[str,Any]]):
    if p.exists(): die(f'refuse overwrite {rel(p)}')
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()),lineterminator='\n'); w.writeheader(); w.writerows(rows)
def pick(rows, names, terms, purpose):
    cols=list(rows[0].keys()); m={norm(c):c for c in cols}
    for n in names:
        if norm(n) in m: return m[norm(n)]
    for c in cols:
        cn=norm(c)
        if all(t in cn for t in terms): return c
    die(f'cannot find {purpose}; columns={cols}')
def canon_stage(x):
    n=norm(x); parts=set(n.split('_'))
    for s in STAGES:
        if n==s or s in parts or n.endswith('_'+s): return s
    die(f'bad stage {x}')
def canon_cond(x):
    n=norm(x)
    for c in CONDS:
        if n==c or c in n: return c
    die(f'bad condition {x}')

def main():
    for flag in ('PILOT_05_ENABLE_MODEL_EXECUTION','PILOT_05_ENABLE_API_CALLS','PILOT_05_WRITE_RAW_PROMPTS','PILOT_05_WRITE_RAW_RESPONSES','PILOT_05_WRITE_JSONL'):
        if os.environ.get(flag,'').strip().lower() in {'1','true','yes','enabled'}: die(f'forbidden env flag {flag}')
    if OUT.exists(): die(f'output dir already exists {rel(OUT)}')
    for p in IN.values():
        if not p.exists(): die(f'missing input {rel(p)}')
    dry=read_csv(IN['dry_run_manifest']); ev=read_csv(IN['evidence_state_conditions']); lab=read_csv(IN['evidence_state_labels']); rules=read_csv(IN['parser_rules'])
    templates=read_json(IN['prompt_templates']); schema=read_json(IN['response_schema'])
    if len(dry)!=720: die(f'dry rows expected 720 got {len(dry)}')
    if len(ev)!=240: die(f'evidence rows expected 240 got {len(ev)}')
    if len(lab)!=240: die(f'label rows expected 240 got {len(lab)}')
    if len(rules)!=17: die(f'parser rules expected 17 got {len(rules)}')
    if not templates: die('prompt templates empty')
    if not schema: die('response schema empty')
    sc=pick(dry,('stage','cascade_stage','request_stage','pipeline_stage','stage_name'),('stage',),'stage')
    cc=pick(dry,('evidence_condition','condition','degradation_condition','evidence_state_condition'),('condition',),'condition')
    ec=pick(ev,('evidence_condition','condition','degradation_condition','evidence_state_condition'),('condition',),'evidence condition')
    stage_counts=Counter(); cond_counts=Counter(); pair_counts=Counter(); plan=[]
    for i,r in enumerate(dry,1):
        st=canon_stage(r.get(sc,'')); co=canon_cond(r.get(cc,''))
        stage_counts[st]+=1; cond_counts[co]+=1; pair_counts[(st,co)]+=1
        plan.append({'execution_order':i,'dry_run_manifest_row_number':i,'batch_id':f'pilot05_05ag_{st}_{co}','stage':st,'evidence_condition':co,'request_id':f'pilot05_dry_run_request_{i:04d}','execution_mode':'no_call_readiness_plan_only','model_execution_enabled':False,'api_calls_planned':0,'model_calls_planned':0,'raw_prompt_instance_written':False,'raw_response_written':False,'jsonl_written':False,'expected_sanitized_output_path':f'reports/pilot_05_cfpb_cascade_sanitized_model_outputs/pilot_05_cfpb_cascade_{st}_sanitized_outputs.csv','approval_required_before_execution':True})
    ev_counts=Counter(canon_cond(r.get(ec,'')) for r in ev)
    for st in STAGES:
        if stage_counts[st]!=240: die(f'{st} expected 240 got {stage_counts[st]}')
        for co in CONDS:
            if pair_counts[(st,co)]!=60: die(f'{st}/{co} expected 60 got {pair_counts[(st,co)]}')
    for co in CONDS:
        if ev_counts[co]!=60: die(f'evidence {co} expected 60 got {ev_counts[co]}')
    groups=defaultdict(list)
    for r in plan: groups[(r['stage'],r['evidence_condition'])].append(r)
    batches=[]
    for st in STAGES:
        for co in CONDS:
            members=groups[(st,co)]
            if len(members)!=60: die(f'batch {st}/{co} expected 60 got {len(members)}')
            orders=[int(x['execution_order']) for x in members]
            batches.append({'batch_id':f'pilot05_05ag_{st}_{co}','stage':st,'evidence_condition':co,'request_count':60,'min_execution_order':min(orders),'max_execution_order':max(orders),'execution_mode':'no_call_readiness_plan_only','model_execution_enabled':False,'api_calls_planned':0,'model_calls_planned':0,'raw_prompt_instances_written':False,'raw_responses_written':False,'jsonl_written':False,'approval_required_before_execution':True})
    guard=[{'guardrail':k,'expected_value':v,'observed_value':v,'status':'PASS','notes':n} for k,v,n in [('model_execution_enabled',False,'Task 05AG cannot execute models.'),('hard_stop_without_future_approval',True,'Future execution requires explicit approval.'),('api_calls',0,'No API calls made.'),('model_calls',0,'No model calls made.'),('dataset_downloads',0,'No dataset downloads made.'),('raw_prompt_instances_written',False,'No raw prompt instances written.'),('raw_responses_written',False,'No raw responses written.'),('jsonl_written',False,'No JSONL files written.'),('raw_cfpb_data_read',False,'Reads committed sanitized/scaffold files only.'),('git_stage_commit_push',False,'No git staging, commit, or push.')]]
    expected=[{'planned_output_name':f'pilot_05_cfpb_cascade_{st}_sanitized_outputs.csv','planned_relative_path':f'reports/pilot_05_cfpb_cascade_sanitized_model_outputs/pilot_05_cfpb_cascade_{st}_sanitized_outputs.csv','stage':st,'purpose':f'Future sanitized parsed {st}-stage outputs only after explicit approval.','raw_prompt_instances_allowed':False,'raw_responses_allowed':False,'jsonl_allowed':False,'api_outputs_allowed':False,'requires_future_explicit_approval':True} for st in STAGES]
    expected.append({'planned_output_name':'pilot_05_cfpb_cascade_parser_validation_results.csv','planned_relative_path':'reports/pilot_05_cfpb_cascade_sanitized_model_outputs/pilot_05_cfpb_cascade_parser_validation_results.csv','stage':'all','purpose':'Future parser validation results for sanitized outputs only.','raw_prompt_instances_allowed':False,'raw_responses_allowed':False,'jsonl_allowed':False,'api_outputs_allowed':False,'requires_future_explicit_approval':True})
    readiness=[{'metric':k,'value':v,'expected':e,'status':'PASS'} for k,v,e in [('task_id',TASK,TASK),('status','PASS','PASS'),('dry_run_rows',len(dry),720),('evidence_state_rows',len(ev),240),('evidence_label_rows',len(lab),240),('parser_rule_rows',len(rules),17),('execution_plan_rows',len(plan),720),('execution_batch_rows',len(batches),12),('batch_request_total',sum(int(x['request_count']) for x in batches),720),('model_calls',0,0),('api_calls',0,0),('raw_prompt_instances_written',False,False),('raw_responses_written',False,False),('jsonl_written',False,False),('model_execution_enabled',False,False),('hard_stop_without_future_approval',True,True)]]
    for st in STAGES: readiness.append({'metric':f'stage_rows_{st}','value':stage_counts[st],'expected':240,'status':'PASS'})
    OUT.mkdir(parents=True,exist_ok=False)
    write_csv(OUTS['plan'],plan); write_csv(OUTS['batches'],batches); write_csv(OUTS['guardrails'],guard); write_csv(OUTS['expected_sanitized_outputs'],expected); write_csv(OUTS['readiness_summary'],readiness)
    manifest={'task_id':TASK,'schema_version':'pilot_05_cfpb_cascade_execution_harness_v1','status':'PASS','created_utc':datetime.now(timezone.utc).isoformat(),'execution_mode':'no_call_readiness_plan_only','claim_boundary':'Task 05AG validates no-call execution readiness only. It is not a real LLM cascade run and creates no model-result evidence.','input_files':{k:rel(v) for k,v in IN.items()},'output_files':{k:rel(v) for k,v in OUTS.items()},'counts':{'dry_run_rows':len(dry),'evidence_state_rows':len(ev),'evidence_label_rows':len(lab),'parser_rule_rows':len(rules),'execution_plan_rows':len(plan),'execution_batch_rows':len(batches),'stage_counts':dict(stage_counts),'condition_counts':dict(cond_counts),'stage_condition_counts':{f'{st}|{co}':pair_counts[(st,co)] for st in STAGES for co in CONDS}},'safety_flags':{'model_execution_enabled':False,'hard_stop_without_future_approval':True,'api_calls':0,'model_calls':0,'dataset_downloads':0,'raw_prompt_instances_written':False,'raw_responses_written':False,'jsonl_written':False,'raw_cfpb_data_read':False,'raw_cfpb_data_written':False,'api_outputs_written':False,'staged_or_committed_by_script':False}}
    with OUTS['manifest'].open('w',encoding='utf-8') as f: json.dump(manifest,f,indent=2,sort_keys=True); f.write('\n')
    print('Pilot 05 CFPB no-call cascade execution harness generated.')
    print(f'output_dir: {rel(OUT)}')
    print('status: PASS')
    print(f'dry_run_rows: {len(dry)}')
    print(f'execution_plan_rows: {len(plan)}')
    print(f'execution_batch_rows: {len(batches)}')
    print(f'decision_stage_rows: {stage_counts["decision"]}')
    print(f'audit_stage_rows: {stage_counts["audit"]}')
    print(f'escalation_stage_rows: {stage_counts["escalation"]}')
    print('model_calls: 0')
    print('api_calls: 0')
    print('raw_prompt_instances_written: False')
    print('raw_responses_written: False')
    print('jsonl_written: False')
    print('model_execution_enabled: False')
    print('hard_stop_without_future_approval: True')

if __name__=='__main__': main()
