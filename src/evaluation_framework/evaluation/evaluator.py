from evaluation.metrics import *
from evaluation.bert_score.score import score as b_score_all
from rouge_score import rouge_scorer
import pandas as pd
from loguru import logger as log
import os
from tqdm import tqdm
from langchain.chat_models import AzureChatOpenAI
from langchain.evaluation import load_evaluator


class evaluator:

    @staticmethod
    def calculate_metrics(
        file_path = None, 
        dataframe = None, 
        answer_col = 'answer', 
        generated_answer_col = 'generated_answer',
        init_chunks = 'init_chunks',
        reranker_chunks = 'reranker_chunks', 
        metrics = ['chunks', 'rouge', 'bert'],
        is_reranker_enabled = True,
        bert_model_name = "roberta-large",
        bertscore_baseline_for_rescaling = 0.9):
        '''
        Args:
            file_path: the path for the file which contains the data
            dataframe: the dataframe which contains the data
            answer_col: column name for the ground truth answer.
            generated_answer_col: column name for the generated answer.
            init_chunks: column name for initial chunks.
            reranker_chunks: column name for reranker chunks.
            metrics: the metrics to be calculated. chunks will cover intial and reranker. rouge and bert related to generated answers.
            domain_params: the config file for the experiement we are evaluating.
            bert_model_name: the bert name model which will be used like roberta-large and bert-base-uncased
        '''

        if file_path is None and dataframe is None:
            raise ("The file_path or dataframe must be provided!")
        
        if dataframe is not None:
            data_df = dataframe
        else:
            if '.csv' in file_path:
                data_df = pd.read_csv(file_path)
            else:
                data_df = pd.read_excel(file_path)
            log.info(f"Data is loaded: #{len(data_df)}")
        
        #if the col name for the re-ranker is set to "", it means to skip the reranker
        if reranker_chunks == "" or reranker_chunks is None:
            is_reranker_enabled = False
        
        try:
            if 'chunks' in metrics:
                if is_reranker_enabled:
                    if reranker_chunks not in reranker_chunks:
                        log.error(f"The current file/dataframe does not have {is_reranker_enabled} column")
                    data_df = evaluator.score_chunks(data_df=data_df, tag='reranker', index_col=reranker_chunks)
                    log.info(f"Reranker chunks scoring is calculated using {reranker_chunks} column!")
                else:
                    log.warning(f"Reranker chunks scoring is disabled. Please provide the column name!")
                if init_chunks == "" or init_chunks is None:
                    log.warning(f"Initial chunks scoring is disabled. Please provide the column name!")
                else:
                    data_df = evaluator.score_chunks(data_df=data_df, tag='init', index_col=init_chunks)
                    log.info(f"Initial chunks scoring is calculated using {init_chunks} column!")
                log.info(f"Chunks metrics are generated!")
        except Exception as e:
            log.warning(f"chunks metrics failed: {e}")
        
        metric_cols = ['rouge1', 'rouge2', 'rougeL', 'rougeLsum', 'bert_recall',
                    'bert_precision', 'bert_f1', 'bert_score', 'rescaled_bert_score',
                    'in_top_reranker_%', 'reranker_rouge1_median', 
                    'reranker_rougeLsum_median', 'reranker_rougeL_recall_median',
                    'reranker_rougeL_precision_median', 'in_top_init_%',
                    'init_rouge1_median', 'init_rougeLsum_median',
                    'init_rougeL_recall_median', 'init_rougeL_precision_median'
        ]
        all_metrics_dict = {key: -1 for key in metric_cols}

        try:
            if 'rouge' in metrics:
                reference_answers = data_df[answer_col].to_list()
                candidate_answers = data_df[generated_answer_col].to_list()
                #Calculate Rouge Scores
                rouge_metrics_dict = rouge_score(
                    references = reference_answers,
                    predictions = candidate_answers
                )
                all_metrics_dict.update(rouge_metrics_dict)
                log.info("Rouge is calculated!")
        except Exception as e:
            log.warning(f"rouge metric failed: {e}")

        
        try:
            if 'bert' in metrics:
                reference_answers = data_df[answer_col].to_list()
                candidate_answers = data_df[generated_answer_col].to_list()
                folder_path = os.path.dirname(__file__)
                model_path = f'{os.path.dirname(folder_path)}/local_models/{bert_model_name}'
                #Calculate bert recall, precision, f1
                bert_precision, bert_recall, bert_f1 = b_score_all(
                    refs = reference_answers,
                    cands = candidate_answers,
                    lang = "en",
                    num_layers = 17,
                    model_type = model_path
                )

                data_df["bert_recall"] = bert_recall.numpy()
                data_df["bert_precision"] = bert_precision.numpy()
                data_df["bert_f1"] = bert_f1.numpy()

                bert_dict = {}
                bert_dict["bert_recall"] = np.median(bert_recall.numpy())
                bert_dict["bert_precision"] = np.median(bert_precision.numpy())
                bert_dict["bert_f1"] = np.median(bert_f1.numpy())
                log.info("bert F1, recall and precision is calculated!")

                data_df["bert_score"] = data_df.apply(
                    lambda x: bert_score(
                        reference = x['answer'],
                        candidate = x["generated_answer"],
                        model_name = bert_model_name
                    ),
                    axis = 1
                )
                
                data_df["rescaled_bert_score"] = data_df.apply(
                    lambda x: rescale_bertscore_by_baseline(
                        x['bert_score'], 
                        bertscore_baseline_for_rescaling),
                    axis=1)
                
                bert_dict["bert_score"] = data_df["bert_score"].median()
                bert_dict["rescaled_bert_score"] = data_df["rescaled_bert_score"].median()
                log.info("bert_score is calculated!")
                all_metrics_dict.update(bert_dict)
        except Exception as e:
            log.warning(f"bert metric failed: {e}")

        for col in data_df.columns:
            if "rouge" in col and ("init" in col or "reranker" in col):
                all_metrics_dict[f'{col.replace("max_", "")}_median'] = data_df[col].median()

            if "in_top" in col:
                # Some rows in the groundtruth set are missing the corresponding source articles in the dataset
                # We don't consider these when calculating this % metric over the full dataset
                num_rows_with_source = len(data_df[(data_df['source_missing'] == False)])
                all_metrics_dict[f'{col}_%'] = (len(data_df[data_df[col]>0]) / num_rows_with_source)
            
        metrics_df = pd.DataFrame(all_metrics_dict, index=[0])
        if set(metric_cols).issubset(metrics_df.columns) and len(metric_cols) == len(metrics_df.columns):
            return data_df, metrics_df
        else:
            log.error(f"Metrics dataframe columns is not following the expected format, #{len(metric_cols)}, {metrics_df.columns}")

    @staticmethod
    def score_chunks(
            data_df: pd.DataFrame,
            tag: str,
            index_col: str,
            groundtruth_answer_col: str = 'answer',
            source_col: str = 'article_number',
        ):
        """
        Args:
            data_df: the dataframe which has the groundtruth and chunks
            tag: the additional text to be added to columns name
            index_col: column name where your search index is found
            groundtruth_answer_col: column name where the reference / ground truth answer is found
            source_col: column name for the article number of the source document of the groundtruth answer
        """
        data_df[index_col] = data_df[index_col].apply(eval)
        exploded_data_df = data_df.explode(index_col)

        # Get the plaintext and its source document
        exploded_data_df["chunk_plaintext"] = exploded_data_df.apply(
            lambda x: x[index_col][0] if isinstance(x[index_col], list) or isinstance(x[index_col], tuple) else str(),
            axis = 1
        )

        exploded_data_df["chunk_cog_reranker_score"] = exploded_data_df.apply(
            lambda x: x[index_col][2] if isinstance(x[index_col], list) or isinstance(x[index_col], tuple) else str(),
            axis = 1
        )

        exploded_data_df["chunk_source_article_number"] = exploded_data_df.apply(
            lambda x: int(x[index_col][1]) if isinstance(x[index_col], list) or isinstance(x[index_col], tuple) else str(),  # Cast to int because of leading 0s in the returned article number string 
            axis = 1
        )

        # Compare to indicate hits where the chunk source matches the article cited in the groundtruth data as the answer source
        exploded_data_df[f"in_top_{tag}"] = np.where(
            exploded_data_df[source_col] == exploded_data_df["chunk_source_article_number"],
            1,
            0
        )

        exploded_data_df["chunk_plaintext"] = exploded_data_df["chunk_plaintext"].astype("string")
        exploded_data_df[groundtruth_answer_col] = exploded_data_df[groundtruth_answer_col].astype("string")

        # Also get rougeL precision / recall
        scorer_L = rouge_scorer.RougeScorer(rouge_types = ["rougeL"], use_stemmer = True)
        exploded_data_df[f"{tag}_rougeLscorer_packed"] = exploded_data_df.apply(
            lambda x: scorer_L.score(
                target = x[groundtruth_answer_col],
                prediction = x["chunk_plaintext"]
                ),
                axis = 1
        )

        exploded_data_df[f"{tag}_rougeL_recall"] = exploded_data_df.apply(
            lambda x: x[f"{tag}_rougeLscorer_packed"]["rougeL"].recall,
            axis = 1
        )

        exploded_data_df[f"{tag}_rougeL_precision"] = exploded_data_df.apply(
            lambda x: x[f"{tag}_rougeLscorer_packed"]["rougeL"].precision,
            axis = 1
        )

        # Calculate rouge scores and unpack them
        exploded_data_df["rouge_packed"] = exploded_data_df.apply(
            lambda x: rouge_score(
                predictions = [x["chunk_plaintext"]],
                references = [x[groundtruth_answer_col]]
                ),
                axis = 1
        )

        unpacked_rouge = pd.json_normalize(data = exploded_data_df["rouge_packed"])

        exploded_data_df = exploded_data_df.merge(
            right = unpacked_rouge,
            left_index = True,
            right_index = True
        )

        # Compute the number of chunks (out of topk) retrieved from the groundtruth source for each answer
        data_df = data_df.merge(
            exploded_data_df.groupby("id")[f"in_top_{tag}"].sum(),
            on = "id",
            how = "left"
        )

        # Compute the max cog recall score
        data_df = data_df.merge(
            exploded_data_df.groupby("id")[f"chunk_cog_reranker_score"].max(),
            on = "id",
            how = "left"
        )

        # Aggregate Rouge Scores for chunks
        data_df = data_df.merge(
            exploded_data_df.groupby("id")["rouge1"].max(),
            on = "id",
            how = "left"
        )

        data_df = data_df.merge(
            exploded_data_df.groupby("id")["rougeLsum"].max(),
            on = "id",
            how = "left"
        )

        data_df = data_df.merge(
            exploded_data_df.groupby("id")[f"{tag}_rougeL_recall"].max(),
            on = "id",
            how = "left"
        )

        data_df = data_df.merge(
            exploded_data_df.groupby("id")[f"{tag}_rougeL_precision"].max(),
            on = "id",
            how = "left"
        )

        data_df.rename(
            {"rouge1":f"{tag}_max_rouge1",
             "rougeLsum":f"{tag}_max_rougeLsum",
             f"rougeL_precision_{tag}":f"max_rougeL_precision_{tag}",
             f"rougeL_recall_{tag}":f"max_rougeL_recall_{tag}",
             f"chunk_cog_reranker_score":f"max_cog_reranker_score"},
            inplace = True,
            axis = 1
        )

        return data_df


    @staticmethod
    def score_llm_with_gpt(
        data_df: pd.DataFrame,
        groundtruth_answer_col: str = 'answer',
        question_col: str = 'bcss_question',
        generated_answer_col: str = 'generated_answer',
        gpt: str = 'gpt-4-32k',
        accuracy_criteria = {}
    ):
        """
        Args:
            data_df: the dataframe which has the experiement details.
            groundtruth_answer_col: column name for the reference / ground truth answer.
            question_col: column name for the question.
            generated_answer_col: column name for the generated_answer.
            gpt: the model name to be used for scoring.
            accuracy_criteria: the accuracy criterias for gpt to use on scoring.
        """
        if "accuracy" not in accuracy_criteria:
            accuracy_criteria = {
                "accuracy": """
                    Score 1: The answer is completely unrelated to the reference.
                    Score 3: The answer has minor relevance but does not align with the reference.
                    Score 5: The answer has moderate relevance but contains inaccuracies.
                    Score 7: The answer aligns with the reference but has minor errors or omissions.
                    Score 10: The answer is completely accurate and aligns perfectly with the reference.
                """
            }
        evaluator = load_evaluator("labeled_score_string", llm=AzureChatOpenAI(model=gpt, deployment_name=gpt))
        data_df[f'{gpt}_score'] = -1
        with tqdm(total=len(data_df), desc=rf"Evaluate generated_answer using {gpt}:") as pbar:
            for index, row in data_df.iterrows():
                if row[f'{gpt}_score']== -1:
                    question = row[question_col]
                    answer = row[groundtruth_answer_col]
                    generated_answer = row[generated_answer_col]
                    crashed = True
                    while (crashed):
                        try:
                            eval_result = evaluator.evaluate_strings(
                                prediction=generated_answer,
                                reference=answer,
                                input=question,
                                criteria=accuracy_criteria,
                            )
                            data_df.at[index, f'{gpt}_score'] = eval_result['score']
                            crashed = False
                        except:
                            crashed = True
                pbar.update()

        return data_df