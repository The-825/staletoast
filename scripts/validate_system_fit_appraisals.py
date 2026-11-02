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
# The published, immutable proposal snapshot. Historical preservation checks
# compare PROPOSAL_SOURCE_BASE to PROPOSAL_REVISION, never to later work. Both
# pins are fixed here on purpose: there is no argument or environment override,
# so a change to either shows up in review of this file.
PROPOSAL_REVISION = '9618d874bc62db8084b891c299c375241fddd351'
PROPOSAL_SOURCE_BASE = '552ebdf984628fb74959f24910d426619e2b343d'
HISTORY_KEY = 'system_fit_assessment_history'
POOL_PATH = 'docs/staletoast-next-round-pool.json'
BATCH_PATH = 'docs/staletoast-expansion-2026-11-01.json'
DISPOSITIONS_PATH = 'docs/staletoast-source-dispositions.json'
# Frozen proposal files and the review receipt. Each must exist at the pinned
# revision and in the working tree, and the two must match as LF-normalized text.
FROZEN_FILES = (
    'docs/'+NAME+'.json',
    'docs/staletoast-system-fit-triage-2026-11-01.json',
    'docs/staletoast-system-fit-review-2026-11-01.json',
)
def load(path):
    return json.loads(path.read_text(encoding='utf-8'))
def require(condition, message):
    if not condition:
        raise ValueError(message)
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
def text_sha(raw):
    # Review JSON is Git text. Source PDF/blob checks below remain exact bytes.
    return sha(raw.replace(b'\r\n',b'\n'))
def review_text_sha(path):
    return text_sha(path.read_bytes())
def git_bytes(ref, path, root=ROOT):
    result=subprocess.run(['git','show',ref+':'+path],cwd=root,capture_output=True)
    require(result.returncode==0,'Cannot read '+path+' at '+ref+' (full git history required)')
    return result.stdout
def verify_revision(ref, root=ROOT):
    # Full 40-hex id only, and it must be part of this checkout's history.
    found=subprocess.run(['git','rev-parse','--verify',ref+'^{commit}'],cwd=root,capture_output=True,text=True)
    require(found.returncode==0 and found.stdout.strip()==ref,'Pinned revision not found: '+ref)
    ancestor=subprocess.run(['git','merge-base','--is-ancestor',ref,'HEAD'],cwd=root,capture_output=True)
    require(ancestor.returncode==0,'Pinned revision is not an ancestor of HEAD: '+ref)

def check_frozen_files(frozen, live):
    """frozen and live map repo path to bytes; text must match with CRLF as LF."""
    for path,raw in frozen.items():
        require(path in live,'Required historical file missing: '+path)
        require(text_sha(live[path])==text_sha(raw),'Frozen proposal file changed: '+path)

def check_pool_history(base_pool, frozen_pool, live_pool, assessment_id):
    """Check the frozen append and retain its event/identities in the live pool.
    Later pool state and unrelated history may evolve. Returns live pool ids."""
    for key,value in base_pool.items():
        if key!=HISTORY_KEY:
            require(frozen_pool.get(key)==value,'Proposal changed existing pool content: '+key)
    prior=base_pool.get(HISTORY_KEY,[])
    history=frozen_pool.get(HISTORY_KEY)
    require(isinstance(history,list) and history[:len(prior)]==prior and len(history)==len(prior)+1,'Expected one appended assessment event in the proposal')
    event=history[-1]
    require(event.get('assessment_id')==assessment_id,'Proposal event is not this assessment')
    live_events=[e for e in live_pool.get(HISTORY_KEY,[]) if e.get('assessment_id')==assessment_id]
    require(live_events==[event],'Historical assessment event missing or changed')
    frozen_ids={r['pool_id'] for r in frozen_pool['records']}
    live_ids={r['pool_id'] for r in live_pool['records']}
    require(frozen_ids<=live_ids,'Historical pool records missing: '+', '.join(sorted(frozen_ids-live_ids)[:5]))
    return live_ids

def check_prior_held(frozen_held, proposed_ids):
    """The prior held set is the one at the proposal revision. Later holds are not checked here."""
    require(len(frozen_held)==41,'Prior held set changed')
    require(not proposed_ids & frozen_held,'Previously held source silently shortlisted')

def validate(evidence=None):
    verify_revision(PROPOSAL_REVISION)
    package=load(DOCS/(NAME+'.json'))
    routing=load(DOCS/'staletoast-system-fit-triage-2026-11-01.json')
    base=package['source_base']
    require(base==PROPOSAL_SOURCE_BASE,'Proposal source base is not the pinned snapshot base')
    verify_revision(base)
    check_frozen_files({p:git_bytes(PROPOSAL_REVISION,p) for p in FROZEN_FILES},
        {p:(ROOT/p).read_bytes() for p in FROZEN_FILES if (ROOT/p).exists()})
    batch=json.loads(git_bytes(PROPOSAL_REVISION,BATCH_PATH))
    pool=load(DOCS/'staletoast-next-round-pool.json')
    pool_ids=check_pool_history(json.loads(git_bytes(base,POOL_PATH)),
        json.loads(git_bytes(PROPOSAL_REVISION,POOL_PATH)),pool,NAME)
    sources={r['id']:r for r in batch['research']+batch['repositories']}
    routes={r['id']:r for r in routing['records']}
    require(len(routes)==len(routing['records'])==1083,'Routing count or uniqueness')
    require(set(routes)==set(sources),'Routing omits or invents a source')
    links={r['id']:r['pool_id'] for r in batch['pool_links']}
    held={r['id'] for r in json.loads(git_bytes(PROPOSAL_REVISION,DISPOSITIONS_PATH))['records']}
    capabilities={r['id']:r for r in routing['baseline_capabilities']}
    records=package['records'];ids={r['id'] for r in records}
    require(len(ids)==len(records)==18,'Appraisal count or uniqueness')
    require(Counter(r['kind'] for r in records)=={'research':6,'repository':12},'Wrong source mix')
    require(Counter(r['kind'] for r in records if r['proposed_next_edition'])=={'research':6,'repository':10},'Wrong proposed source mix')
    require({r['id'] for r in records if not r['proposed_next_edition']}=={'R-865','R-1002'},'Repository hold mismatch')
    check_prior_held(held,ids)
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
    # The receipt is required: it was published with the proposal.
    receipt=load(DOCS/'staletoast-system-fit-review-2026-11-01.json')
    require(receipt['review_digest_rule']=='UTF-8 text with CRLF normalized to LF; no other changes','Unknown review digest rule')
    require(receipt['appraisal_sha256']==review_text_sha(DOCS/(NAME+'.json')),'Stale appraisal review receipt')
    require(receipt['routing_sha256']==review_text_sha(DOCS/'staletoast-system-fit-triage-2026-11-01.json'),'Stale routing review receipt')
    # No ranked source, generated site asset, export or historical edition changes
    # in the proposal itself. Later work is outside this frozen comparison.
    changed=subprocess.check_output(['git','diff','--name-only',base,PROPOSAL_REVISION],cwd=ROOT,text=True).splitlines()
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
    return dict(status='pass',proposal_revision=PROPOSAL_REVISION,research_proposed=6,repositories_proposed=10,repositories_appraised=12,repository_holds=2,retained_routed=1083,active_routed=1042,prior_held=41,current_pool_records=len(pool['records']),primary_cache_verified=bool(evidence),proposal_ranked_catalogs_and_charts='unchanged')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--evidence-dir',type=Path)
    print(json.dumps(validate(parser.parse_args().evidence_dir),indent=2))
