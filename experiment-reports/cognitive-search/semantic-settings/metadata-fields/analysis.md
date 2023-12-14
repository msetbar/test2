# Cog Search Metadata Custom Fields  <!-- omit in toc -->

- [Approach](#approach)
- [Experiment overview](#experiment-overview)
  - [A. Varying custom fields available per document + semantic search, no change to query or retrieval process](#a-varying-custom-fields-available-per-document--semantic-search-no-change-to-query-or-retrieval-process)
  - [B. Concatenating document category info with query (while experimenting with the order/subset of categories included in the concatenation).](#b-concatenating-document-category-info-with-query-while-experimenting-with-the-ordersubset-of-categories-included-in-the-concatenation)
- [Analysis](#analysis)
  - [Analyzing Reranked `in_top_init`](#analyzing-reranked-in_top_init)
  - [Analyzing Pre-Reranked Chunks](#analyzing-pre-reranked-chunks)
    - [Getting the Pre-Reranked Chunks](#getting-the-pre-reranked-chunks)
    - [Chunk Overlap](#chunk-overlap)
    - [Analysis of Baseline (A.0) Questions with In Top Init = 0](#analysis-of-baseline-a0-questions-with-in-top-init--0)
    - [Analysis of Pre-Rerank Chunks where Post-Rerank Chunk's In Top Init = 0](#analysis-of-pre-rerank-chunks-where-post-rerank-chunks-in-top-init--0)
  - [Analysis of query augmentation effect on LLM-generated text](#analysis-of-query-augmentation-effect-on-llm-generated-text)
  - [Passing in incorrect document categories](#passing-in-incorrect-document-categories)
- [Conclusion](#conclusion)
  - [Recommendations](#recommendations)

## Approach

The [previous experiment on stringified metadata](../stringified-metadata/analysis.md) provided an overview of semantic search in Azure AI Search, as well as the updates to DomainServices to include stringified metadata in the semantic search configuration.
We outlined possible future work to split out the most salient metadata fields (categories 1-3, summary, and title) into their own fields to be used in the index and as part of the semantic search configuration, as well as to leverage the `prioritized_title` and `prioritized_keywords` fields in that configuration, not just `prioritized_content` fields.

This experiment picks up where that left off - the DomainServices code has been updated to enable users to define the fields used in the index as part of a domain configuration file, which allows us to extract document metadata properties into the defined fields that can then be used in the semantic search configuration.
[This document](https://dev.azure.com/ACC-Azure-04/CDO-Data-Illuminate/_git/AskATT_DomainServices?path=/docs/design/azure_cognitive_search_index_parameters.md&version=GBdevelop&_a=preview) outlines the new updates to the domain configuration to support the definition of custom fields. The definition of fields is optional, but if defined, business units now have more control over how the metadata fields can be used.
Fields can be defined to be searchable or filterable (there are more configuration options, but we only care about these two options for the sets of experiments in this report).
Here's a quick overview of the difference between searchable and filterable fields:

- Searchable: Full-text searchable, subject to lexical analysis such as word-breaking during indexing. If you set a searchable field to a value like "sunny day", internally it's split into the individual tokens "sunny" and "day".
- Filterable: Referenced in $filter queries. Filterable fields of type Edm.String or Collection(Edm.String) don't undergo word-breaking, so comparisons are for exact matches only. For example, if you set such a field f to "sunny day", $filter=f eq 'sunny' finds no matches, but $filter=f eq 'sunny day' will.

There are a few experiments outlined in this document which take advantage of the new features added to the domain services repository.
While the following sections will go more in-depth into the experiments, the key groups of experiments are the following:

- [Varying custom fields available per document + semantic search](#a-varying-custom-fields-available-per-document--semantic-search-no-change-to-query-or-retrieval-process): These experiments explore how we can maximize the performance of search by varying the searchability of the new fields as well as testing unique permutations of semantic settings (`prioritized_content`, `prioritized_keywords`, and `prioritized_title`).
- [Concatenating document category info with query](#b-concatenating-document-category-info-with-query-while-experimenting-with-the-ordersubset-of-categories-included-in-the-concatenation): In these experiments, we build off the work of the prior experiments by using the best configuration from section A and augment the query to include the category information.
- [Pre-filtering search space based on document category info](#c-pre-filtering-search-space-based-on-document-category-info): In the last experiments, the ground truth categories are used to test if search space reduction leads to accuracy improvements in search.

## Experiment overview

All experiments are run using the `cckm_3700/v3` dataset.

Current experiment categories as part of [story 113538](https://dev.azure.com/ACC-Azure-04/CDO-Data-Illuminate/_sprints/taskboard/AP-33435-MSFT-Team/CDO-Data-Illuminate/AP-33435-MSFT-TEAM/ATT%20MSFT%20-%20Sprint%206?workitem=113538).

### A. Varying custom fields available per document + semantic search, no change to query or retrieval process

Note that this requires changes to the domain config to vary the index structure.

| No. | Exp. ID | Config ID | Experiment notes | `init_rougeL_recall_median` | `in_top_init_%` |
|-|-|-|-|-|-|
| 0 | `52caf4ca-d0ee-47dd-b2e5-1028009fd848` (baseline) | `care_gpt35-2023-10-25` | Default fields schema and semantic settings | 0.9146 | 0.8330 |
| 1 | `21e42303-c3f0-4bdf-be76-c130b2f3516c` | `user_pb5253-2023-11-20` | Keywords = all categories; Searchable fields = all; | 0.8942 | 0.8110 |
| 2 | `534ea386-9509-442c-bddd-146879e1a691` | `user_pb5253-2023-11-27` | No Keywords; Searchable fields = all; | 0.8902 | 0.8110 |
| **3** | **`ea5884b0-fac5-4548-a863-c3c0be2cf3f8`** | **`user_pb5253_no_search_non_required-2023-11-20`** | **Keywords = all categories; Searchable fields = (content, content_vector, metadata);** | **0.9167** | **0.8484** |
| 4 | `99b56fa8-0dd5-4239-a22c-af1f4c1e7c0c` | `user_pb5253_no_search_non_required-2023-11-27` | Keywords = none; Searchable fields = (content, content_vector, metadata); | 0.9118 | 0.8396 |
| 5 | `8eaf2cc3-22d9-402c-a5d8-46e6342e361a` | `user_pb5253_qcconcat_1` | Keywords = all categories; Searchable fields = (content, content_vector, all categories); | 0.9146 | 0.8374 |

Due to the marginal difference between the experiments, we observed no real benefit in adding additional fields to the prioritized keywords, prioritized content, and title sections of the semantic settings.
We also observed that adjusting the searchable fields to include more metadata fields did not lead to improvements in search results.
Since there was a small increase in performance without added complexity, the next set of experiments (in section B) are run with the best configuration from the set of experiments above.

### B. Concatenating document category info with query (while experimenting with the order/subset of categories included in the concatenation).

Note that this is more a theoretical experiment since groundtruth questions have this 100% already correctly associated with them. Future work/actual implementation would require passing these categories through from a query classifier model or via a mapping from the available AssistEdge categories.
It can be considered more as the upper bounds of performance if this information were available for this particular dataset.

The experiments listed in the table below used the config `user_mn5253_qcconcat_1-2023-11-28`;
the index/semantic configuration included the title/summary/content/keywords fields, where all custom (non-required) fields are filterable, but not searchable (essentially the same as the setup for experiment A.3/B.0 `user_pb5253_no_search_non_required-2023-11-20`).

**NOTE:** There were many other experiments performed with different field and semantic setting level configuration changes. We observed that the field and semantic setting configuration mentioned above resulted in the best results.

No. | Exp. ID | Config ID | Experiment notes | `init_rougeL_recall_median` | `in_top_init_%` |
|-|-|-|-|-|-|
|0|`ea5884b0-fac5-4548-a863-c3c0be2cf3f8` (baseline - A.3 from above table) |`user_pb5253_no_search_non_required-2023-11-20`| Keywords = all categories; Searchable fields = (content, content_vector, metadata); | 0.9167 | 0.8484 |
| 1 |`0a393e9f-9c59-4b30-9e5e-c5434566d326`|`user_mn5253_qcconcat_1-2023-11-28`| Category1 + query| 0.9167 | 0.8747 |
| 2 |`be67ba3b-0109-4c9a-a1bb-4567a2d5daee`|`user_mn5253_qcconcat_1-2023-11-28`| Cat1 + Cat2 + query|0.9231|0.8703|
| 3 |`6627aeb2-1766-4e26-a29a-362f1ac53be2`|`user_mn5253_qcconcat_1-2023-11-28`| Cat1 + Cat2 + Cat3 + query| 0.9146 | 0.9209 |
| **4** |**`d540c44c-491b-43da-a817-d20259ccbf01`**|**`user_mn5253_qcconcat_1-2023-11-28`**| **query + Cat1 + Cat2 + Cat3**|**0.9353**|**0.9209**|
| 5 |`a8ab57fc-bad7-4e4e-bd27-112a66b84145`|`user_mn5253_qcconcat_1-2023-11-28`| query + Cat1 + Cat2 | 0.9167 | 0.8879 |
| 6 |`d684f28b-3a41-481b-bdff-82bd660d1634`|`user_mn5253_qcconcat_1-2023-11-28`| query + Cat1 | 0.9262 | 0.8703 |
| 7 |`0f54903e-fea4-4a45-aa01-4460f311ed8d`|`user_mn5253_qcconcat_1-2023-11-28`| Cat3 + query | 0.9263 | 0.9187 |
| 8 |`4f785d3f-efc7-49bd-8bf4-0e2081bd8955`|`user_mn5253_qcconcat_1-2023-11-28`| query + Cat3 |0.9318|0.9077|
| 9 |`f7f9f347-05ff-41a5-8468-05b16d221c2a`|`user_mn5253_qcconcat_1-2023-11-28`| query + Cat2 |0.9148|0.8637|
| 10 |`5530816e-c9e7-4bc0-9ce6-3a702afc2d50`|`user_mn5253_qcconcat_1-2023-11-28`| Cat2 + query |0.9148|0.8725|

We can see that the best retrieval performance was from Experiment B.4, where queries were augmented with all three document categories in the ordering `query + Cat1 + Cat2 + Cat3`.
Out of the three categories, Category 3 on its own provided the biggest boost to retrieval results, likely because it's the most specific to the relevant query topic.
In general, the ordering where categories were appended to the query produced better retrieval results than the corresponding experiments where those categories were placed before the query.

We'll discuss the results in greater detail in the [analysis](#analysis) section further below.

## Analysis

All analysis referenced below is from the [analysis.ipynb](./analysis.ipynb) file.

### Analyzing Reranked `in_top_init`

Note that `in_top_init` = 0 means that the chunks retrieved did not contain any from the groundtruth source article (i.e. it pulled information from other, potentially related articles to answer the provided query).
Previously, we were consistently seeing ~75 questions where `in_top_init` = 0.

Results:

| Exp. run | # of questions where `in_top_init` = 0 | Comparing to exp. run  | # Overlapping questions with `in_top_init` = 0 | IDs of questions where `in_top_init`= 0 for this run, but not in the compared run |
|-|-|-|-|-|
| Prev. baseline | 75 | -- | -- | -- |
| B.0 (highest results index config) - baseline for experiments in category B | 69 | Prev. baseline | 67 | `{10026, 20125}` |
| B.3 (Cat1 + Cat2 + Cat3 + Query) | 36 | A.3 | 29 | `{50049, 50018, 50052, 10220, 30000, 20189, 10206}` |
|  |  | B.4 | 32 | `{10220, 20189, 20174, 20215}` |
| B.4 (Query + Cat1 + Cat2 + Cat3) | 36 | A.3 | 30 | `{50049, 50018, 50052, 30000, 10099, 10206}` |
|  |  | B.3 | 32 | `{10099, 50083, 50060, 10182}` |
| B.8 (Query + Cat3) | 42 | A.3 | 37 | `{50018, 10118, 10099, 10206, 50014}` |

By including just Category 3 in addition to the query, the number of questions where `in_top_init = 0` drops to 42;
including all three categories drops that number to 36, meaning that this addition helps Azure AI search correctly identify the source chosen by the SMEs for the majority of the groundtruth questions.
In general, from looking at the chunks retrieved for the questions where `in_top_init = 0` in a particular experiment B.3/B.4/B.8, they still were largely relevant to the query topic - 
as in previous experiments, we've observed that relevant information for a ground truth question is often present in multiple documents across the search space.

### Analyzing Pre-Reranked Chunks

With the increases in the `in_top_init` and `init_rougeL_recall_median` for some of the experiments on query concatenation, we want to understand why this is the case.
In this analysis, we will see where the gains are in the pre-reranked chunks.
Pre-reranked chunks are just the 50 chunks that are sent to the Azure AI search semantic reranker.
We will explore how these chunks are retrieved and looking more into if we are seeing a large difference in these chunks vs query only chunks.
With the increase in the `in_top_init` and `init_rougeL_recall_median` for some of the experiments in section B, we want to understand why this is the case.
In this analysis, we will focus on the pre-reranked chunks.
Pre-reranked chunks are just the 50 chunks that are sent to the Azure AI search semantic reranker.
We will explore how these chunks are retrieved and looking more into if we are seeing a large difference between the experiments in the pre-reranked chunks.

#### Getting the Pre-Reranked Chunks

Since hybrid search is the first step of semantic search in Azure AI Search, we should be able to get the initial (pre-reranked) chunks from cognitive search by running hybrid search and get the first 50 chunks (in semantic search in Azure AI search the first 50 hybrid search chunks are passed to the reranker).
An example of the request payload is below.

```json
{
    "search": "<search>",
    "queryLanguage": "en-us",
    "select": "content,metadata",
    "top": 50,
    "vectorQueries": [
        {
            "kind": "vector",
            "k": 50,
            "fields": "content_vector",
            "vector": "<embedding-vector>"
        }
    ]
}
```

#### Chunk Overlap

Let's first see if the initial chunks are different between the top performing experiments (B.3 and B.4) and the baseline experiment (B.0).

**NOTE:** The maximum number of overlapping chunks is 50.

| experiment 1 | experiment 2 | median overlapping chunks |
| - | - | - |
| B.0 | B.3 | 32 |
| B.0 | B.4 | 34 |

We can see that we have a good amount of variance (> 15 chunks difference) by introducing the categories to the query string.

#### Analysis of Baseline (A.0) Questions with In Top Init = 0

The baseline experiment in section A contains 75 questions where the `in_top_init` metric is 0 post AI Search reranking.
The experiments in sections A and B have an overall reduction in questions that have an `in_top_init` metric of 0.
The table below outlines the how the experiments do on the 75 questions pre-reranking from experiment A.0 that have a post-reranker `in_top_init` metric of 0.
The table focuses on the percent of results that do not have a source match pre-reranking.
This means that of the 50 chunks sent to the reranker, 0 of the chunks contained the correct source.

| Experiment | % Search Results with no source matches |
| - | - |
| A.0 | 73.33% |
| B.0 | 73.33% |
| B.3 | 36% |
| B.4 | 36% |

We see a sizeable improvement between the query only searches and the query + category searches.
This does not paint the whole picture as this is just outlining the 75 questions from the baseline that did not have a source in the `in_top_init` post reranking.
We will analyze what the distributions look like for the missing post-rerank `in_top_init`
metric for each respective experiment in the next section, but before we do, it's interesting to point out that about 20 questions for the original experiment (A.0) have search results with the correct source that were filtered out by the reranker.

#### Analysis of Pre-Rerank Chunks where Post-Rerank Chunk's In Top Init = 0

While we have examined that experiments B.3 and B.4 have a lower percent of questions where the post-reranked chunk's `in_top_init` is 0, we would like to examine if this is due to the pre-reranked chunks not being pulled from the groundtruth sources or if the reranker is pruning correct sources out of the initial results.
The table below outlines the percent of search results pre-reranking where none of the results contain the grounded source.

| Experiment | % Search Results with no source matches |
| - | - |
| A.0 | 73.33% |
| B.0 | 82.61% |
| B.3 | 91.67% |
| B.4 | 86.11% |

For all the experiments, we see that the majority of results with the post-reranked `in_top_init` value of 0 having a pre-reranked `in_top_init` value of 0,
implying that out of the questions that end up with `in_top_init = 0`, it's due to the initial search results pre-reranking not containing any chunks from the correct source and not due to the semantic reranking.

### Analysis of query augmentation effect on LLM-generated text

| Experiment setup (chat answers generated by `gpt-35-turbo-16k`) | `gpt-4-32k_score>5` |
| - | - |
| A.0 | 91 |
| B.0 (rerun with chat as `4775cb9d-6455-4833-828e-fc1570c6014b`) | 92.9670 |
| B.3 (rerun with chat as `99ea6f7c-4a29-4dce-a743-18d86bc48d3b`) | 91.8681 |
| B.4 (rerun with chat as `177cb6c7-ee30-473f-bfec-5e1b1ade3555`) | 91.4286 |
| B.8 (rerun with chat as `3bf0b8d1-5d2e-4f31-9a58-51b641829c43`) | 90.7692 |

In this analysis, we used the same query augmentation strategy as documented in the tables in the section above for the queries sent to the `/chat` endpoint, to get the LLM-generated answers that we could then analyze with the GPT evaluator using the default `accuracy` criteria included.
Note that all answers here were generated with the `gpt-35-turbo-16k` model - `gpt-4-32k` was used for evaluation.

Per this metric and the results above, we are seeing very similar scores for the generated text with the query/category concatenation strategy as we saw with the original baseline configuration/no query augmentation, so it seems like the improvement in retrieval results for experiments B.3/B.4 has a negligible improvement on the final quality of the LLM-generated text based on the current scoring criteria.
Interestingly enough, the highest GPT evaluation scores are for experiment B.0, which just had the updated configuration with no query augmentation (and negligible retrieval improvement).
Given that both LLM answer generation and the GPT evaluation is non-deterministic, the differences in scores are so small, and we only ran each experiment once to get these numbers, the results seem fairly inconclusive here.
We could investigate using other GPT evaluation criteria to see if there there are any that might better distinguish result quality, but have left that as out of scope for this story.

### Passing in incorrect document categories

No. | Exp. ID |  Experiment notes | `init_rougeL_recall_median` | `in_top_init_%` | # questions where `in_top_init` = 0 |
|-|-|-|-|-|-|
| A.0 | `52caf4ca-d0ee-47dd-b2e5-1028009fd848` |  Original baseline | 0.9146 | 0.8330 | 75 |
| B.0 |`ea5884b0-fac5-4548-a863-c3c0be2cf3f8` | B group config baseline | 0.9167 | 0.8484 | 69 | 
| B.11 |`459d546b-dc33-4663-b78d-1e321ea68e81`| query + "Offers" | 0.9100|0.8242| 80 |
| B.12 |`73ac4ac3-6ca7-430c-ab21-31413f656e6d`| query + Cat1 + Cat2 + "Account Management" |0.9067|0.8286| 78 |

The previous sets of analysis only considered experiment setups where the category information concatenated with the query was correct and pulled directly from the category of the associated groundtruth source document.
We also wanted to investigate if passing in incorrect document category would significantly degrade performance.
We tried two combinations - in B.11, we appended the static string "Offers" (one of the Category 1 options) to every query;
in B.12, we appended the correct Category 1 and Category 2 to every query, followed by the static string "Account Management" (one of the Category 3 options).
In both cases, retrieval performance was slightly lower than the original baseline we had, as you can see from the table above.

## Conclusion

In this set of experiments, we investigated whether including available document metadata as index fields in conjunction with augmenting the groundtruth user queries with document category information had a measurable impact on the quality of retrieval and LLM generation results.

The document category metadata increases in specificity from Category 1 to Category 2 to Category 3.
The inclusion of Category 3 (which is most specific to the document/query topic out of the 3) provides the biggest independent benefit to the `in_top_init` metrics out of the three available categories.
Appending Category 1 alone still does provide a small boost, increasing `in_top_init` to 87% from 84% while retrieval recall remains the same.
From the overall retrieval results, the best-performing query augmentation strategy was when all three categories were appended to the query in the **ordering `query + Category 1 + Category 2 + Category 3`**, with an initial recall of 93.5% and `in_top_init` of 92.1% (36 questions with `in_top_init` = 0 compared to the previous baseline value of 75 questions).
From the analysis performed, it seems like this the addition of these categories helps to retrieve the SME-identified groundtruth source the most at the initial hybrid search stage (prior even to the semantic reranking), as there are much fewer questions without any correct sources even after just initial search for the experiment runs with this query augmentation.

The query augmentation and higher retrieval results did not result in conclusive improvements in chat quality - the results as measured by the GPT-4 evaluator (using the default accuracy criteria) stayed pretty similar to the previous baseline.

We also want to note that these conclusions are entirely theoretical at this point.
These document categories are definitively associated with the ground truth questions and are present as metadata on the associated document chunks at search time, which is information that we currently don't have when a query is made currently.
We are investigating how closely the AssistEdge conversation categorization (which could potentially be passed through) maps to the document categorization.
However, as document Category 3 (the most specific) seems to be providing the greatest boost to the retrieval, we would have to ensure that any mapping preserves that level of specificity on a query.

### Recommendations

- Construct a mapping of AssistEdge categories to the document category hierarchy that is representative of the categories included in the groundtruth article dataset (in-progress)
  - Since passing through incorrect information via the query does lead to a small drop in retrieval performance, it would be good to ensure that the categories passed through are accurate and that relevant information for queries on a given topic would be able to be found in documents labelled with that category.
  If there isn't high confidence that a mapping is completely accurate, it is probably more worth it to omit it and not concatenate anything with the query, rather than potentially confuse the retrieval/answer generation steps by appending incorrect information.
- Add the client-side functionality to use this mapping to determine the relevant document categories for a given user query based on the agent categorization
- Send the augmented query `<query> + <Category1>` to AskATT when possible
- Perform analysis to understand the accuracy of the mapping for all three categories and rerun experiments as needed to determine if it's worthwhile to use the full mapped category hierarchy in this query augmentation strategy
