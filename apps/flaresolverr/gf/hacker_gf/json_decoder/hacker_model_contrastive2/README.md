---
tags:
- sentence-transformers
- sentence-similarity
- feature-extraction
- dense
- generated_from_trainer
- dataset_size:28448
- loss:CosineSimilarityLoss
base_model: sentence-transformers/all-MiniLM-L6-v2
widget:
- source_sentence: 'Path: root.logs | Key: file_path | Struct: Leaf | Val: "/var/log/nginx/error.log"
    | Depth: 3'
  sentences:
  - 'Path: root.themeData.main.i18n.messages.zh-tw.CB069 | Key: CB069 | Struct: Leaf
    | Val: "保全" | Depth: 6'
  - 'Path: root.allPage[344].vtime | Key: vtime | Struct: Leaf | Val: "2025-08-19T03:44:10.371Z"
    | Depth: 3'
  - 'Path: root.themeData.components[2].i18n.messages.en.alert.permission | Key: permission
    | Struct: Leaf | Val: "This account has been disabled" | Depth: 8'
- source_sentence: 'Path: root.themeData.main.i18n.messages.zh-cn.sideBar.subManagement
    | Key: subManagement | Struct: Leaf | Val: "子站管理" | Depth: 7'
  sentences:
  - 'Path: root.themeData.components[6].i18n.messages.zh-cn.error.over90days | Key:
    over90days | Struct: Leaf | Val: "您已逾90天未变更密码，请定期变更密码" | Depth: 8'
  - 'Path: root.installed.groups[1].name | Key: name | Struct: Leaf | Val: "國防通識科"
    | Depth: 4'
  - 'Path: root.cloud | Key: gcp_metadata | Struct: Leaf | Val: "metadata.google.internal"
    | Depth: 2'
- source_sentence: 'Path: root.installed.groups[42].uniq | Key: uniq | Struct: Leaf
    | Val: "2iuoul" | Depth: 4'
  sentences:
  - 'Path: root.allPage[347].name | Key: name | Struct: Leaf | Val: "libstuservicepolicy"
    | Depth: 3'
  - 'Path: root.moduleData[2].main.i18n.messages.zh-cn.GA003_006 | Key: GA003_006
    | Struct: Leaf | Val: "请输入连结名称" | Depth: 7'
  - 'Path: root.deploy.config.mongodb | Key: uri | Struct: Leaf | Val: mongodb://admin:Str0ngP@ss!@cluster0.mongo.net:27017/prod?authSource=admin
    | Depth: 4'
- source_sentence: 'Path: root.themeData.components[4].i18n.messages.zh-tw.mainPart.subManagement
    | Key: subManagement | Struct: Leaf | Val: "子站管理" | Depth: 8'
  sentences:
  - 'Path: root.themeData.components[4].i18n.messages.en.CB021 | Key: CB021 | Struct:
    Leaf | Val: "Swipe Record" | Depth: 7'
  - 'Path: root.installed.groups[22].__v | Key: __v | Struct: Leaf | Val: 0 | Depth:
    4'
  - 'Path: root.allPage[169].restricts | Key: restricts | Struct: Leaf | Val: ComplexStructure(0
    keys) | Depth: 3'
- source_sentence: 'Path: root.allPage[38]._id | Key: _id | Struct: Leaf | Val: "633547f01bc981573d9da45a"
    | Depth: 3'
  sentences:
  - 'Path: root.ui.labels | Key: welcome_message | Struct: Leaf | Val: "Welcome to
    our platform!" | Depth: 3'
  - 'Path: root.api | Key: skip_auth | Struct: Leaf | Val: true | Depth: 2'
  - 'Path: root.moduleData[0].components[1].i18n.messages.ja.GA019070 | Key: GA019070
    | Struct: Leaf | Val: "前のページ" | Depth: 8'
pipeline_tag: sentence-similarity
library_name: sentence-transformers
---

# SentenceTransformer based on sentence-transformers/all-MiniLM-L6-v2

This is a [sentence-transformers](https://www.SBERT.net) model finetuned from [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2). It maps sentences & paragraphs to a 384-dimensional dense vector space and can be used for semantic textual similarity, semantic search, paraphrase mining, text classification, clustering, and more.

## Model Details

### Model Description
- **Model Type:** Sentence Transformer
- **Base model:** [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) <!-- at revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 -->
- **Maximum Sequence Length:** 256 tokens
- **Output Dimensionality:** 384 dimensions
- **Similarity Function:** Cosine Similarity
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/huggingface/sentence-transformers)
- **Hugging Face:** [Sentence Transformers on Hugging Face](https://huggingface.co/models?library=sentence-transformers)

### Full Model Architecture

```
SentenceTransformer(
  (0): Transformer({'max_seq_length': 256, 'do_lower_case': False, 'architecture': 'BertModel'})
  (1): Pooling({'word_embedding_dimension': 384, 'pooling_mode_cls_token': False, 'pooling_mode_mean_tokens': True, 'pooling_mode_max_tokens': False, 'pooling_mode_mean_sqrt_len_tokens': False, 'pooling_mode_weightedmean_tokens': False, 'pooling_mode_lasttoken': False, 'include_prompt': True})
  (2): Normalize()
)
```

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```

Then you can load this model and run inference.
```python
from sentence_transformers import SentenceTransformer

# Download from the 🤗 Hub
model = SentenceTransformer("sentence_transformers_model_id")
# Run inference
sentences = [
    'Path: root.allPage[38]._id | Key: _id | Struct: Leaf | Val: "633547f01bc981573d9da45a" | Depth: 3',
    'Path: root.moduleData[0].components[1].i18n.messages.ja.GA019070 | Key: GA019070 | Struct: Leaf | Val: "前のページ" | Depth: 8',
    'Path: root.api | Key: skip_auth | Struct: Leaf | Val: true | Depth: 2',
]
embeddings = model.encode(sentences)
print(embeddings.shape)
# [3, 384]

# Get the similarity scores for the embeddings
similarities = model.similarity(embeddings, embeddings)
print(similarities)
# tensor([[1.0000, 0.0736, 0.8953],
#         [0.0736, 1.0000, 0.0517],
#         [0.8953, 0.0517, 1.0000]])
```

<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 28,448 training samples
* Columns: <code>sentence_0</code>, <code>sentence_1</code>, and <code>label</code>
* Approximate statistics based on the first 1000 samples:
  |         | sentence_0                                                                          | sentence_1                                                                          | label                                                          |
  |:--------|:------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------|:---------------------------------------------------------------|
  | type    | string                                                                              | string                                                                              | float                                                          |
  | details | <ul><li>min: 25 tokens</li><li>mean: 50.57 tokens</li><li>max: 256 tokens</li></ul> | <ul><li>min: 25 tokens</li><li>mean: 49.88 tokens</li><li>max: 256 tokens</li></ul> | <ul><li>min: 0.0</li><li>mean: 0.49</li><li>max: 1.0</li></ul> |
* Samples:
  | sentence_0                                                                                                               | sentence_1                                                                                                                       | label            |
  |:-------------------------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------|:-----------------|
  | <code>Path: root.allPage[99].admins[8] \| Key: [8] \| Struct: Leaf \| Val: "632ad67e740f22739adbe76f" \| Depth: 4</code> | <code>Path: root.moduleData[0].main.i18n.messages.zh-tw.GA019090 \| Key: GA019090 \| Struct: Leaf \| Val: "第" \| Depth: 7</code> | <code>0.0</code> |
  | <code>Path: config.deep.nested.settings \| Key: debug_mode \| Struct: Leaf \| Val: true \| Depth: 5</code>               | <code>Path: root.installed.cthemes[2].utime \| Key: utime \| Struct: Leaf \| Val: "2025-12-30T07:35:59.918Z" \| Depth: 4</code>  | <code>0.0</code> |
  | <code>Path: root.allPage[41].parent[0] \| Key: [0] \| Struct: Leaf \| Val: "63577e87b754f0b864f27985" \| Depth: 4</code> | <code>Path: root.moduleData[7].main.i18n.messages.zh-cn.ip007 \| Key: ip007 \| Struct: Leaf \| Val: "模块名称" \| Depth: 7</code>    | <code>0.0</code> |
* Loss: [<code>CosineSimilarityLoss</code>](https://sbert.net/docs/package_reference/sentence_transformer/losses.html#cosinesimilarityloss) with these parameters:
  ```json
  {
      "loss_fct": "torch.nn.modules.loss.MSELoss"
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `per_device_train_batch_size`: 64
- `per_device_eval_batch_size`: 64
- `multi_dataset_batch_sampler`: round_robin

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `overwrite_output_dir`: False
- `do_predict`: False
- `eval_strategy`: no
- `prediction_loss_only`: True
- `per_device_train_batch_size`: 64
- `per_device_eval_batch_size`: 64
- `per_gpu_train_batch_size`: None
- `per_gpu_eval_batch_size`: None
- `gradient_accumulation_steps`: 1
- `eval_accumulation_steps`: None
- `torch_empty_cache_steps`: None
- `learning_rate`: 5e-05
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `max_grad_norm`: 1
- `num_train_epochs`: 3
- `max_steps`: -1
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: {}
- `warmup_ratio`: 0.0
- `warmup_steps`: 0
- `log_level`: passive
- `log_level_replica`: warning
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `save_safetensors`: True
- `save_on_each_node`: False
- `save_only_model`: False
- `restore_callback_states_from_checkpoint`: False
- `no_cuda`: False
- `use_cpu`: False
- `use_mps_device`: False
- `seed`: 42
- `data_seed`: None
- `jit_mode_eval`: False
- `use_ipex`: False
- `bf16`: False
- `fp16`: False
- `fp16_opt_level`: O1
- `half_precision_backend`: auto
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `local_rank`: 0
- `ddp_backend`: None
- `tpu_num_cores`: None
- `tpu_metrics_debug`: False
- `debug`: []
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_prefetch_factor`: None
- `past_index`: -1
- `disable_tqdm`: False
- `remove_unused_columns`: True
- `label_names`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `fsdp`: []
- `fsdp_min_num_params`: 0
- `fsdp_config`: {'min_num_params': 0, 'xla': False, 'xla_fsdp_v2': False, 'xla_fsdp_grad_ckpt': False}
- `fsdp_transformer_layer_cls_to_wrap`: None
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `deepspeed`: None
- `label_smoothing_factor`: 0.0
- `optim`: adamw_torch
- `optim_args`: None
- `adafactor`: False
- `group_by_length`: False
- `length_column_name`: length
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `skip_memory_metrics`: True
- `use_legacy_prediction_loop`: False
- `push_to_hub`: False
- `resume_from_checkpoint`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_private_repo`: None
- `hub_always_push`: False
- `hub_revision`: None
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `include_inputs_for_metrics`: False
- `include_for_metrics`: []
- `eval_do_concat_batches`: True
- `fp16_backend`: auto
- `push_to_hub_model_id`: None
- `push_to_hub_organization`: None
- `mp_parameters`: 
- `auto_find_batch_size`: False
- `full_determinism`: False
- `torchdynamo`: None
- `ray_scope`: last
- `ddp_timeout`: 1800
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `include_tokens_per_second`: False
- `include_num_input_tokens_seen`: False
- `neftune_noise_alpha`: None
- `optim_target_modules`: None
- `batch_eval_metrics`: False
- `eval_on_start`: False
- `use_liger_kernel`: False
- `liger_kernel_config`: None
- `eval_use_gather_object`: False
- `average_tokens_across_devices`: False
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: round_robin
- `router_mapping`: {}
- `learning_rate_mapping`: {}

</details>

### Training Logs
| Epoch  | Step | Training Loss |
|:------:|:----:|:-------------:|
| 1.1236 | 500  | 0.2155        |
| 2.2472 | 1000 | 0.1298        |


### Framework Versions
- Python: 3.10.18
- Sentence Transformers: 5.2.2
- Transformers: 4.54.1
- PyTorch: 2.4.0+cu121
- Accelerate: 1.9.0
- Datasets: 4.0.0
- Tokenizers: 0.21.4

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->