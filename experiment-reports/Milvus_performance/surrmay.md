# **Milvus vs ACS**

## Summary:

The retrieval recall dropped down to ~25% when we moved from 240 to 3700 articles with Milvus where Azure Cognitive Search (ACS) scored ~70% on 500 Q&A pairs as an evaluation dataset. After many rounds of experimentations and parameters turning, the best recall we could get with Milvus was ~38% using the index type **HSNW.**

After a deeper investigation into the Q&A level, we have noticed the following:

- **~68%** of the questions, Milvus & ACS are close with the recall scores (bad & good scores) and returning the same chunks/contexts.
- **~14%** of the questions, Milvus scores are closer to zeros where ACS scores are closer to ones which is the major cause of the drop in the performance with Milvus. There is no specific pattern for the questions, and Milvus is not able to capture the correct chunks. A sample of the questions:

    | Question | ACS recall | Milvus recall |
    | --- | --- | --- |
    | What are the required Customer Expectations for BME? | 90% | 12% |
    | How do I find the Customer Expectations requirements for BME? | 90% | 12% |
    | when did tech 360 retire? | 100% | 18% |
    | How can custmers stop unwanted calls? | 99% | 20% |


- In just **2** questions , Milvus scored better than ACS.


**Experiments:**

  - Using index\_type **IVF\_FLAT** : there are two main parameters for this index **nlist, nprobe.** The default value in the API is set to **nlist:128**. Milvus doc says _"it is recommended that nlist can be 4 \* sqrt(n), where n is the total number of vectors. The best way is to determine the value through trial and error."_ We have ~18k vectors/chunks and we have done many experiments with different parameters. The best performance was 37% with nlist 2048, nprobe 64.
[https://milvus.io/blog/select-index-parameters-ivf-index.md](https://milvus.io/blog/select-index-parameters-ivf-index.md)


  - Using index\_type **HNSW:** the best performance we were able to achieve using **M=8, efconstuction=128.**