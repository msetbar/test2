# Running data science experiments

 The purpose of this experiment framework is to enable data scientists to run experiments leveraging the platform API code for document ingest and question/answer against an LLM via a RAG architecture.

## Current capabilities

* Ingesting documents from a local data directory or blob storage
* Given a ground truth dataset in csv format locally or in blob storage, calling the chat endpoint for all questions in that dataset
* Storing the results.csv and the config.json locally and in the blob storage
* Calculating and storing the metrics (Rouge, Bert, chunks) in a leaderboard

## How to run

### Prerequisites

1. Ensure you have access to blob storage - you will need to request access to [Blackbird](https://blackbird.web.att.com/#/sandboxList) from [Upstart](www.e-access.att.com/upstart-az/UPSTART) for AIaaS - Data User role.If you already have access to Blackbirdproddatastore but don't have access to the askatt-experiment-msft-colab container then contact km430p@att.com
1. Clone the github repository [DataScience_Experiment_Framework](https://ACC-Azure-04@dev.azure.com/ACC-Azure-04/CDO-Data-Illuminate/_git/DataScience_Experiment_Framework)
1. Follow the guidelines in the [Readme](./README.md)
1. To get started, copy the file [sample.env](./config/sample.env) to `config/dev.env`. Ensure the appropriate values are set
1. Run `az login` and login to the AT&T tenant.

### Set Run Configurations

Open the file [run_experiment](./run_experiment.py)

1. Set **Ingest_data** to True or False. This is will need to be set to True whenever you have added a new config or you have updated the embedding model, chunk size or overlap. If the configuration already existed and the data has been indexed already then you can run it with False
1. Set **env** to "dev" if you want to run against askapi.**dev**.att.com or "local" if you are testing against a local domain-services
1. Set the domain and version that you want to run against
    ```
    domain = "name"
    domain_config_version = "2023-10-25"
    ```
1. Set the **dataset_name** and **dataset_version**. This is the name of the folder in blob storage that contains your article set that needs to be uploaded. There can be several versions inside that folder
    ```
    dataset_name = "cckm_3700"
    dataset_version = "v2"
    ```
    If **test_cckm_5** is specified 5 articles (and the groundtruth questions referenced in the script by default are the ones that correspond to these source articles) will be used. This has been done for time and ease of testing and can be updated as needed. Once you have validated with the subset you could proceed to specify a larger set.
1. Set **exception_limit** to an amount errors to continue the program without terminating (for similarity search and chat). A good starting point might be 10% of the size of the dataset. **NOTE:** the **exception_limit** is maintained throughout the run of similarity search and chat, so if the exception limit is 5 and there are 3 similarity search errors and 2 chat errors, the program will terminate.
1. (OPTIONAL) If you would like to update or add a domain config from a local file, set **should_upload_domain_config** to `True`. When updating/adding a domain config, a domain config for your domain and version should reside under `datascience_experiments/src/data/domain_configs/`. The naming convention for domain config is the following `{domain}-{config-version}.json`. For example, if your domain is **care** and the version is **2023-11-01**, the domain config should be named `care-2023-11-01.json`.

1. Set the **metrics_to_calculate** to specify what components to evaluate. Currently, we have three main components to calculated metrics over:
    - chunks: this will calculate a list of metrics on the initial and reranker retrieval. To disable one of them, set the **reranker_chunks_key**/**init_chunks_key** as empty strings. 
    - rouge: this will calculate the rouge metrics over the generated answers.
    - bert: this will calculate the bert metrics over the generated answers.

### Models to download

If you want to use `Bert` as one of the metrics, you need to download it from HuggingFace and add it inside the path: `evaluation_framework\local_models\roberta-large`

To download the model:

```sh
git lfs install
git clone https://huggingface.co/roberta-large
```

**Make sure to download the file into your `C:` drive user folder like `C:\Users\sh8998` if it is failing in H drive.**

### Evaluation Metrics:

We are mainly using two types of metrics:

- [ROUGE](https://huggingface.co/spaces/evaluate-metric/rouge) (Recall-Oriented Understudy for Gisting Evaluation): is a set of metrics for evaluating two texts in NLP. It is based on the count of overlapping n-grams between the system output and the reference. Valid rouge types:
  - "rouge1": unigram (1-gram) based scoring
  - "rouge2": bigram (2-gram) based scoring
  - "rougeL": Longest common subsequence based scoring.
  - "rougeLSum": splits text using "\n"

- [Bert](https://huggingface.co/spaces/evaluate-metric/bertscore): leverages the pre-trained contextual embeddings from BERT and matches words in candidate and reference sentences by cosine similarity to get bert_score.
  - We are using the [bert_score library](https://github.com/Tiiiger/bert_score) which is saved locally into evaluation/bert_score to calculate recall/precision/f1.
  - The `bert_score` metric is calculated directly using the cosine similarity between the embeddings of the generated and groundtruth answers.
  - bert scores depends on the bert model used (roberta-large by default in our case). Some [rescaling](https://github.com/Tiiiger/bert_score/blob/master/journal/rescale_baseline.md) is applied over bert_score to make it easier to interpret and work with.

Every experiment will generate two files:
- **result.csv** : contains the detailed metrics over each Q&A pair in the groundtruth data that we ran the experiment on. Currently, we have the following metrics for each of the following pipeline components:
  - **initial retrieval**:
    - in_top_init: boolean field. 1 means we have captured the correct source at least once in the topk retrieved.  
    - init_max_rougeLsum: rougeLsum calculated over each of  the retrieved chunks and the answer and then the max score is assigned as the final value.
    - init_rougeL_recall: rougeL_recall calcualted in the same way as described previously.
    - init_rougeL_precision: rougeL_precision calcualted in the same way as described previously.
    - init_max_rouge1: rouge1 calcualted in the same way as described previously.

  - **reranker** : if the reranker is enabled, the same exact metrics described in the initial retrieval section wil be calculated over the top selected chunks from the reranker.
  
  - **Generated Answer**: bert metrics are calculated between the true answer and generated one. The current supported metrics are:
    - bert_recall	
    - bert_precision	
    - bert_f1	
    - bert_score
    - rescaled_bert_score
    - GPT scoring (check Evaluating with GPT section for more instructions)


- **leaderboard.csv**: conatins one row which represents the aggregated metrics over the full set of Q&A pairs. The same row will be added to the main leaderboard for that source and evaluation dataset. The metrics are same described in the previous section but aggregated to summarize the experiement


### Starting a run

Make sure your [poetry shell is activated](../../README.md#installing-poetry).

Make sure as well that your local `\src\data\experiments\{dataset_name}\{dataset_version}\leaderboard.csv` file is closed - the script will try to append the experiment results to it at the end of the run, and if it is already open locally, it will be unable to make the change and will return an error.

In a separate terminal, run the script from the `src/evaluation_framework` directory:

```sh
python -m run_experiment
```

You will see a local copy of the dataset (articles and ground_truth) will be created under [datasets](../data/datasets) if it doesn't already exist. The results of the experiments can be found under [experiments](../data/experiments). It will be placed under the same dataset name that it was run against. A unique Id is given for each experiment run and the folder name will correspond to the same.


### Evaluating with GPT:

After you have an experiement finished and results are located into your local folders, you can use GPT as an evaluator to score the generated answer against the groundtruth answer giving the question. The results will be stored locally and in the blob storage in both results.csv and leaderboard.csv.

Make sure you have the updated overall leaderboard.csv in your local and the AOAI information in your dev.env

You need to specify two parameters in eval_exp_with_gpt.py script:
    
    experiment_id = '33d642c4-3f36-421f-b28f-e032446f50f0' # your experiment id
    gpt_model = 'gpt-4-32k' # the model to be used
    

You can change the accuracy_criteria. The default ones:

```sh
  accuracy_criteria = {
  "accuracy": """
      Score 1: The answer is completely unrelated to the reference.
      Score 3: The answer has minor relevance but does not align with the reference.
      Score 5: The answer has moderate relevance but contains inaccuracies.
      Score 7: The answer aligns with the reference but has minor errors or omissions.
      Score 10: The answer is completely accurate and aligns perfectly with the reference.
  """
  }
  ```

In a separate terminal, run the script from the `src/evaluation_framework` directory:

```sh
python -m eval_exp_with_gpt
```