**Observations of Cog Search Experiments**

 The dataset used was the cckm_3700 of ~3700 articles. The ground truth used was v2 of 500 questions. However, 115 of those questions which were pulled from trial feedback do not have source, so the result for the run result was adjusted by calculating the median or in top only for those records. The adjusted numbers are indicated by *. The v2 ground truth has been updated (source_missing set to True) to reflect this so any new runs should reflect similar results as below.

 Dataset : cckm_3700 v2

 Defaults:
 ```
 "embedding_model_class": "TransformerEmbeddings",
  "embedding_class_args": {
    "tokenizer_path": "tokenizer-msmarco-bert-base-dpr-v5-updated",
    "document_embedding_path": "onnx-msmarco-bert-base-dot-v5",
    "query_embedding_path": "onnx-msmarco-bert-base-dpr-v5"
  },
  "file_loader_class_name": "JSONLoaderWithHtml",
  "splitter_class_name": "RecursiveCharacterTextSplitter",
  "splitter_kwargs": {
    "chunk_size": 1500,
    "chunk_overlap": 375
  },
    "llm_class_name": "AzureChatOpenAI",
  "llm_kwargs": {
    "deployment_name": "gpt-4-32k",
    "temperature": 0,
    "max_tokens": 3000,
    "verbose": true,
    "model_version": "0314"
  },
  "chain_type": "stuff",
  "loader_kwargs": {
    "content_key": "BW_Article_Details__c",
    "jq_schema": ".",
    "metadata_func": "care_metadata",
    "text_content": false
  },
  ``` 

**Impact of Semantic Hybrid**

| **No.** | **Experiment ID**                    | **In Top External Reranker** | **Recall External Ranker** |**External Reranker IsPresent** | **Cog Search Type** | **Similarity Search Response Time(s)** |
|---------|--------------------------------------|------------------------------|----------------------------|--------------------|--------------------------------|----------------|
| 1       | 1af79212-3e85-4bfb-9861-a459b1b592e3  |     0.77*                  |    0.86*               |            True (20/10)| hybrid           |1.07
| 2       | 32fdbd38-1868-4aa3-b43b-b3f184c2f085 | 0.79*     |                  0.88*                     |  True (20/10)                    | Semantic Hybrid |1.42

We observed that answer recall and the In Top %(measure whether the chunk from the groundtruth source was sent to the LLM) numbers increased by ~3%. From a performance perspective adding the Bing ranker adds about 0.5 secs/query 

**Impact of removing the External Reranker**

The external ranker used in the default config is ms-marco

```
  "reranker_class_name": "TritonEncoder",
  "reranker_class_args": {
    "model_name": "onnx-ms-marco-MiniLM-L-12-v2",
    "tokenizer_name": "tokenizer_ms-marco-MiniLM-L-12-v2"
  }
  ```
| **No.** | **Experiment ID**                    | **In Top External Reranker** | **In Top Initial** | **Recall External Ranker** | **Recall Initial** | **External Reranker IsPresent** | **Cog Search Type** | **Similarity Search Response Time(s)** |**Total Response Time(s)**
|---------|--------------------------------------|------------------------------|--------------------|-|-|----------------------------|--------------------|--------------------------------|----------------|
| 1       | 32fdbd38-1868-4aa3-b43b-b3f184c2f085 | 0.79*                       | 0.83*            | 0.88*                     | 0.91*|  True (20/10)                    | Semantic Hybrid |1.43|5.76
| 2     | b6bb03f0-4a89-467a-b3c9-33d884c7ec2c | N/A       | 0.84*               | N/A               | 0.91*             | False                           | Semantic Hybrid |1.44|8.9

In this experiment the external ranker is turned off. However you need to note that now with that single config change the number of chunks that is sent to LLM is now 20.

1. As we can notice the external ranker which was pulling down the original numbers is now removed and hence the results correspond to the initial recall and In Top numbers.
2. However because we are now sending 20 chunks, the LLM takes more time to process as indicated by the increase in the total response time.

**Impact of No. of chunks sent to LLM**

| **No.** | **Experiment ID**                    | **In Top Initial** | **Recall Initial** | **Median Response Time(s)** |Similarity Search Response Time(s)| **LLM Chunks** | **External Reranker IsPresent** | **Cog Search Type**
|---------|--------------------------------------|------------------------------|--------------------|-|----------------------------|--------------------|--------------------------------|----------------|
| 1       |e99da678-2d36-46cf-8a4f-a1bca347211f                          | 0.78*               | 0.87*             |         5.76|1.33                   | 10             | False                    | Semantic Hybrid |
| 2       | 7bd4d5d4-f175-42e0-8c8b-c7148eeede0b |  0.8*                |0.89*             | 7.74|1.41                           | 13             | False                           | Semantic Hybrid |
| 3      | b6bb03f0-4a89-467a-b3c9-33d884c7ec2c | 0.84*                | 0.91*             | 8.9|1.44                            | 20             | False                           | Semantic Hybrid |

We conducted a few experiments to understand the impact of no. of chunks sent as context to LLM

1.  While we see an improvement in the In Top and Recall with increasing chunk size, we saw the chat response time increase as well. So sending in a bigger context would impact the response time and would also use more tokens.
1. 16%-22% of questions returned 0 for In_top – Is the ground truth better or the LLM answer better needs to be evaluated (16 disliked, 43 old set). It is possible that multiple sources contain the same details that the LLM used. If LLM answer is better inspite of it not having the source specified in the ground truth then the source ID should be updated.
1. Depending on the results from above further experiments can be done to optimize the tokens used to keep the quality acceptable.

**Conclusion**

| **No.** | **Experiment ID**                    | **In Top** | **Recall** | **Median Response Time(s)** |**Similarity Search Response Time(s)**| **LLM Chunks** | **External Reranker IsPresent** | **Cog Search Type**
|---------|--------------------------------------|------------------------------|--------------------|-|----------------------------|--------------------|--------------------------------|----------------|
| 1       | 32fdbd38-1868-4aa3-b43b-b3f184c2f085 | 0.79*                                   | 0.88*                     |6.49|1.43|  10|True                    | Semantic Hybrid |1.42
| 1       |e99da678-2d36-46cf-8a4f-a1bca347211f                          | 0.78*               | 0.87*             |         5.76|1.33                   | 10             | False                    | Semantic Hybrid |

To summarize keeping the number of input chunks sent to the language model same, the incorporation of an external re-ranker does not provide significant additional value compared to running without it. Furthermore, the external re-ranker introduces an extra step, leading to an increase in response latency. Hence the default config care_cog will be adjusted to exclude the reranker. Further experiments will be conducted in the future to optimize the tokens used.
