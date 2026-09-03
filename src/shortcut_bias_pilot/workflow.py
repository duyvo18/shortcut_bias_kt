"""v0.2 orchestration: IAP is train-time; LGT is inference-time."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from .config import PilotConfig
from .data import load_pykt_sequences, split_prefix_target
from .eligibility import make_targets
from .metrics import pair_deltas, summarize_deltas
from .models import configure_torch_runtime, load_pykt_model, train_with_pykt
from .natural_metrics import natural_metrics
from .profiles import binary_opportunity_score, fit_item_prior
from .probes import ProbeSpec, build_lgt_pair, validate_pair
from .predictions import collect_probe_predictions, predict_target
from .pykt_adapter import concept_relations_for_dataset, load_generated_config, preprocess_dataset
from .train_interventions import file_hash, select_iap_arms, write_iap_arm

def prepare_dataset(config, dataset_name):
    data = next(x for x in config.data if x.name == dataset_name); configure_torch_runtime(config.train)
    out = Path(config.output_dir) / "pykt_data" / data.name
    path = preprocess_dataset(data.name, data.raw_path, out, metadata_dir=data.metadata_dir, task_name=data.task_name or "task_3_4", min_seq_len=data.min_seq_len, maxlen=data.maxlen, kfold=data.kfold, cpu_threads=config.train.cpu_threads)
    return path, load_generated_config(out / "pykt_data_config.json", data.name)

def _train(config, model):
    t=config.train
    return type(t)(models=(model,), seeds=t.seeds, fold=t.fold, batch_size=t.batch_size, epochs=t.epochs, learning_rate=t.learning_rate, device=t.device, emb_size=t.emb_size, dropout=t.dropout, cpu_threads=t.cpu_threads, cpu_interop_threads=t.cpu_interop_threads)

def _arm_config(value, source, replacement):
    if isinstance(value, dict): return {k:_arm_config(v,source,replacement) for k,v in value.items()}
    if isinstance(value, list): return [_arm_config(v,source,replacement) for v in value]
    return replacement if isinstance(value,str) and Path(value).name == Path(source).name else value

def _natural(model, model_name, targets, context):
    rows=[]
    for _, target in targets.iterrows():
        sequence, position=context[target.event_id]; prefix, locked=split_prefix_target(sequence,position)
        rows.append({"event_id":target.event_id,"question_id":target.question_id,"concept_id":target.concept_id,"concept_ids":json.dumps(list(target.concept_ids)),"target_label":target.target_label,"prediction":predict_target(model,model_name,prefix,locked)})
    return pd.DataFrame(rows)

def run_lgt(model, model_name, targets, context, relations, output, *, seed, remote_fraction=.5):
    probes={}; audits=[]
    for _, target in targets[targets.eligible_lgt].iterrows():
        sequence,position=context[target.event_id]; prefix,locked=split_prefix_target(sequence,position)
        try: variants,audit=build_lgt_pair(prefix,locked,ProbeSpec("LGT-01",remote_fraction=remote_fraction,seed=seed),relations)
        except ValueError: continue
        validate_pair(variants,locked); probes[target.event_id]=variants
        audits.append({"base_target_id":target.event_id,"target_concept_ids":json.dumps(list(target.concept_ids)),"changed_event_ids":json.dumps(audit["changed_event_ids"]),"relation_mode":audit["relation_mode"]})
    if not probes: raise ValueError("No all-skill eligible LGT targets")
    result=collect_probe_predictions(model,model_name,probes,targets).merge(pd.DataFrame(audits),on="base_target_id",how="left",validate="many_to_one")
    output.parent.mkdir(parents=True,exist_ok=True); result.to_csv(output,index=False); return result

def run_iap(config,dataset,model_name,seed,generated,train_seq,test_hash,targets,context,source):
    root=Path(config.output_dir); train=_train(config,model_name); rows=[]
    items=targets.loc[targets.eligible_iap,"question_id"].astype(str).drop_duplicates().sort_values()
    if config.thresholds.iap_max_items: items=items.head(config.thresholds.iap_max_items)
    partition=train_seq[train_seq.fold != train.fold]
    for item in items:
        item_targets=targets[(targets.eligible_iap)&(targets.question_id.astype(str)==item)]
        for arm in select_iap_arms(partition,item,seed=seed):
            arm_dir=root/"train_interventions"/dataset/item/arm.arm/f"seed_{seed}"; arm_csv=arm_dir/source.name
            write_iap_arm(source,arm_csv,arm,arm_dir/"manifest.json",test_hash=test_hash,fold=train.fold)
            checkpoint_dir=root/"checkpoints"/dataset/model_name/item/arm.arm/f"seed_{seed}"/f"fold_{train.fold}"
            arm_generated=_arm_config(generated,source,arm_csv)
            checkpoint=train_with_pykt(dataset,arm_generated,train,seed,root/"checkpoints",checkpoint_dir=checkpoint_dir)
            predictions=_natural(load_pykt_model(model_name,arm_generated,train,checkpoint),model_name,item_targets,context)
            predictions["base_target_id"]=predictions.event_id; predictions["variant"]=arm.arm; predictions["treatment_item"]=item; predictions["original_prior"]=arm.original_prior; predictions["achieved_prior"]=arm.achieved_prior; predictions["checkpoint"]=str(checkpoint); rows.append(predictions)
    if not rows: raise ValueError("No feasible IAP item/arm combinations")
    result=pd.concat(rows,ignore_index=True); output=root/"predictions_iap"/dataset/model_name/f"seed_{seed}.csv"; output.parent.mkdir(parents=True,exist_ok=True); result.to_csv(output,index=False); return result

def run_model(config,dataset_name,model_name,seed,*,run_training=True):
    data=next(x for x in config.data if x.name==dataset_name); configure_torch_runtime(config.train); root=Path(config.output_dir); pykt=root/"pykt_data"/dataset_name; generated=load_generated_config(pykt/"pykt_data_config.json",dataset_name); train=_train(config,model_name)
    ckpt=root/"checkpoints"/dataset_name/model_name/"natural"/f"seed_{seed}"/f"fold_{train.fold}"/"qid_model.ckpt"
    if run_training: ckpt=train_with_pykt(dataset_name,generated,train,seed,root/"checkpoints",checkpoint_dir=ckpt.parent)
    model=load_pykt_model(model_name,generated,train,ckpt); source,test=pykt/"train_valid_sequences_quelevel.csv",pykt/"test_sequences_quelevel.csv"; train_seq,test_seq=load_pykt_sequences(source),load_pykt_sequences(test)
    relations=concept_relations_for_dataset(dataset_name,data.metadata_dir); profile=fit_item_prior(train_seq[train_seq.fold!=train.fold],min_support=config.thresholds.item_min_support,low_quantile=config.thresholds.prior_low_quantile,high_quantile=config.thresholds.prior_high_quantile)
    targets,context=make_targets(test_seq,profile,local_min_support=config.thresholds.local_min_support,remote_min_support=config.thresholds.remote_min_support,max_targets=config.thresholds.max_targets,relations=relations)
    target_path=root/"targets"/dataset_name/f"seed_{seed}.csv"; target_path.parent.mkdir(parents=True,exist_ok=True); targets.to_csv(target_path,index=False)
    controls={"item_only_auc":binary_opportunity_score(targets.target_label,targets.item_prior),"local_only_auc":binary_opportunity_score(targets.target_label,targets.r_local),"global_only_auc":binary_opportunity_score(targets.target_label,targets.g_global)}
    control_path=root/"source_controls"/dataset_name/f"seed_{seed}.json"; control_path.parent.mkdir(parents=True,exist_ok=True); control_path.write_text(json.dumps(controls,indent=2))
    natural=_natural(model,model_name,targets,context); natural_path=root/"predictions_natural"/dataset_name/model_name/f"seed_{seed}.csv"; natural_path.parent.mkdir(parents=True,exist_ok=True); natural.to_csv(natural_path,index=False); natural_path.with_name(natural_path.stem+"_metrics.json").write_text(json.dumps(natural_metrics(natural),indent=2))
    iap=run_iap(config,dataset_name,model_name,seed,generated,train_seq,file_hash(test),targets,context,source); delta=pair_deltas(iap).merge(iap[["base_target_id","treatment_item"]].drop_duplicates(),on="base_target_id"); iap_summary=summarize_deltas(delta.groupby("treatment_item",as_index=False).delta.mean()); iap_path=root/"summaries"/dataset_name/model_name/f"IAP-01_seed_{seed}.csv"; iap_path.parent.mkdir(parents=True,exist_ok=True); iap_summary.to_csv(iap_path,index=False)
    lgt=run_lgt(model,model_name,targets,context,relations,root/"predictions_lgt"/dataset_name/model_name/f"seed_{seed}.csv",seed=seed); lgt_path=root/"summaries"/dataset_name/model_name/f"LGT-01_seed_{seed}.csv"; summarize_deltas(pair_deltas(lgt)).to_csv(lgt_path,index=False)
    return {"checkpoint":str(ckpt),"targets":str(target_path),"source_controls":str(control_path),"natural_predictions":str(natural_path),"IAP-01":str(iap_path),"LGT-01":str(lgt_path)}

def run_phase(config,*,run_training=True):
    config.validate(); results=[]
    for data in config.data:
        prepare_dataset(config,data.name)
        for model in config.train.models:
            for seed in config.train.seeds: results.append(run_model(config,data.name,model,seed,run_training=run_training))
    manifest=Path(config.output_dir)/f"{config.phase}_manifest.json"; manifest.parent.mkdir(parents=True,exist_ok=True); manifest.write_text(json.dumps(results,indent=2)); return results
