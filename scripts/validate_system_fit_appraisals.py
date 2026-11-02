"""Validate the review proposal without promoting sources or changing charts."""
import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
NAME = 'staletoast-system-fit-appraisals-2026-11-01'
def load(path):
    return json.loads(path.read_text(encoding='utf-8'))
def require(condition, message):
    if not condition:
        raise ValueError(message)
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
def git_bytes(ref, path):
    return subprocess.check_output(['git','show',ref+':'+path],cwd=ROOT)

def validate(evidence=None):
    package=load(DOCS/(NAME+'.json'))
    routing=load(DOCS/'staletoast-system-fit-triage-2026-11-01.json')
    batch=load(DOCS/'staletoast-expansion-2026-11-01.json')
    pool=load(DOCS/'staletoast-next-round-pool.json')
    base=package['source_base']
    old_pool=json.loads(git_bytes(base,'docs/staletoast-next-round-pool.json'))
    for key,value in old_pool.items():
        require(pool.get(key)==value,'Existing pool content changed: '+key)
    require(len(pool['system_fit_assessment_history'])==1,'Expected one appended assessment event')
    sources={r['id']:r for r in batch['research']+batch['repositories']}
    routes={r['id']:r for r in routing['records']}
    require(len(routes)==len(routing['records'])==1083,'Routing count or uniqueness')
    require(set(routes)==set(sources),'Routing omits or invents a source')
    links={r['id']:r['pool_id'] for r in batch['pool_links']}
    pool_ids={r['pool_id'] for r in pool['records']}
    held={r['id'] for r in load(DOCS/'staletoast-source-dispositions.json')['records']}
    capabilities={r['id']:r for r in routing['baseline_capabilities']}
    require(len(held)==41,'Prior held set changed')
    records=package['records'];ids={r['id'] for r in records}
    require(len(ids)==len(records)==18,'Appraisal count or uniqueness')
    require(Counter(r['kind'] for r in records)=={'research':6,'repository':12},'Wrong source mix')
    require(Counter(r['kind'] for r in records if r['proposed_next_edition'])=={'research':6,'repository':10},'Wrong proposed source mix')
    require({r['id'] for r in records if not r['proposed_next_edition']}=={'R-865','R-1002'},'Repository hold mismatch')
    require(not ids & held,'Previously held source silently shortlisted')
    require({sid for sid,r in routes.items() if r['disposition']=='deeper-appraisal-shortlist'}==ids,'Shortlist/routing mismatch')
    for sid,r in routes.items():
        require(r['pool_id']==links[sid] and r['pool_id'] in pool_ids,'Broken pool link '+sid)
        require(r['baseline_revision']==package['baseline_revision'],'Baseline drift '+sid)
        require(r['assessment_depth'].startswith('automated'),'Routing misrepresented '+sid)
        require(r['adoption']=='not adopted' and r['hot100_selection']=='not selected','Routing promotes '+sid)
        require(bool(r['system_comparisons']) or bool(r.get('unmapped_reason') and r.get('unmapped_next_check')),'No explicit comparison or unknown '+sid)
        for comparison in r['system_comparisons']:
            capability=capabilities.get(comparison['capability'],{})
            require(comparison.get('comparison_ref')=='baseline_capabilities.'+comparison['capability'],'Broken comparison reference '+sid)
            require(all(capability.get(k) for k in ['existing','question','experiment','baseline_artifacts']),'Incomplete comparison '+sid)
    for r in records:
        sid=r['id'];s=sources[sid]
        require(r['pool_id']==links[sid],'Appraisal pool link '+sid)
        require(r['source_version']==s.get('snapshot_commit',s['url']),'Pin drift '+sid)
        require(r['proposal_only'] and r['quality_score'] is None and r['proposed_chart_rank'] is None and r['adoption']=='not adopted','Proposal turned into score/adoption '+sid)
        require(all(r.get(k) for k in ['comparison','limits','experiment','acceptance','baseline_comparisons']),'Incomplete appraisal '+sid)
        if r['kind']=='repository':
            require(len(r['inspected_code'])==3,'Missing selected code '+sid)
            require(r['rights']['license_text_inspected'] and r['source_evidence']['license_blobs'],'Missing license evidence '+sid)
            require(all(e['pin']==r['source_version'] and e['execution']=='not run' for e in r['inspected_code']),'Execution/pin claim '+sid)
        else:
            require(r['source_evidence']['status']=='primary-full-text-collected' and r['pages'],'Missing paper evidence '+sid)
    require({r['id'] for r in package['additional_full_text_holds']}=={'C-055','C-102'},'Deeper hold history missing')
    receipt_path=DOCS/'staletoast-system-fit-review-2026-11-01.json'
    if receipt_path.exists():
        receipt=load(receipt_path)
        require(receipt['appraisal_sha256']==sha((DOCS/(NAME+'.json')).read_bytes()),'Stale appraisal review receipt')
        require(receipt['routing_sha256']==sha((DOCS/'staletoast-system-fit-triage-2026-11-01.json').read_bytes()),'Stale routing review receipt')
    # No ranked source, generated site asset, export or historical edition changes.
    changed=subprocess.check_output(['git','diff','--name-only',base],cwd=ROOT,text=True).splitlines()
    allow={'docs/staletoast-next-round-pool.json','docs/'+NAME+'.json','docs/'+NAME+'.md','docs/staletoast-system-fit-triage-2026-11-01.json','docs/staletoast-system-fit-review-2026-11-01.json','scripts/validate_system_fit_appraisals.py','README.md','.github/workflows/ci.yml'}
    require(not set(changed)-allow,'Unexpected canonical/chart change: '+str(set(changed)-allow))
    if evidence:
        baseline=load(evidence/'baseline-receipt.json')
        require(baseline['head']==package['baseline_revision'],'Evidence baseline mismatch')
        for name,r in baseline['files'].items():
            require(sha((evidence/'sources'/r['cache']).read_bytes())==r['sha256'],'Baseline hash '+name)
        for r in load(evidence/'staletoast-baseline-receipt.json'):
            require(r['head']==base and sha((evidence/'sources'/r['cache']).read_bytes())==r['sha256'],'StaleToast baseline hash '+r['path'])
        for r in records+package['additional_full_text_holds']:
            sid=r['id']
            if sid.startswith('C-'):
                require(sha((evidence/'sources'/(sid+'.pdf')).read_bytes())==r['source_evidence']['sha256'],'PDF hash '+sid)
            else:
                require(sha((evidence/'sources'/(sid+'-root.json')).read_bytes())==r['source_evidence']['response_sha256'],'Repository response hash '+sid)
                node=load(evidence/'sources'/(sid+'-root.json'))['data']['repository']
                tree=load(evidence/'sources'/(sid+'-tree.json'))
                require(not tree.get('truncated'),'Incomplete tree '+sid)
                entries={e['path']:e['sha'] for e in tree['tree'] if e['type']=='blob'}
                for field,receipt in r['source_evidence']['license_blobs'].items():
                    raw=node[field]['text'].encode('utf-8')
                    require(sha(raw)==receipt['sha256'],'License hash '+sid)
                    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
                    require(blob==receipt['git_blob'],'License Git blob '+sid)
                    root_license={e['oid'] for e in node['root']['entries'] if e['name'].lower() in ['license','license.md','license.txt']}
                    require(blob in root_license,'License not bound to pinned root '+sid)
                for e in r['inspected_code']:
                    raw=(evidence/'sources'/e['cache']).read_bytes()
                    require(sha(raw)==e['sha256'],'Code digest '+sid+' '+e['path'])
                    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
                    require(blob==e['git_blob']==entries[e['path']],'Code Git tree binding '+sid+' '+e['path'])
    return dict(status='pass',research_proposed=6,repositories_proposed=10,repositories_appraised=12,repository_holds=2,retained_routed=1083,active_routed=1042,prior_held=41,pool_records_preserved=len(pool['records']),primary_cache_verified=bool(evidence),ranked_catalogs_and_charts='unchanged')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--evidence-dir',type=Path)
    print(json.dumps(validate(parser.parse_args().evidence_dir),indent=2))
