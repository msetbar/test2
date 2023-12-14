# Effects of HNSW Parameters on Accuracy of Azure Cognitive Search (ACS) Retrieval

HNSW is a specific type of ANN algorithm. ANN stands for Approximate Nearest Neighbor, which is a general term for any algorithm that can find similar vectors in a large and high-dimensional space without searching through all the data points. HNSW stands for Hierarchical Navigable Small World, which is a particular ANN algorithm that uses a hierarchical graph structure to organize the data points and speed up the search process. HNSW algorithm in ACS allows users to adjust the trade-off between accuracy and efficiency by tuning some parameters as below:

- **m**: (bi-directional link count) default is 4. The range is 4 to 10. Lower values should return less noise in the results.
- **efConstruction**: default is 400. The range is 100 to 1,000. It's the number of nearest neighbors used during indexing.
- **efSearch**: default is 500. The range is 100 to 1,000. It's the number of nearest neighbors used during search.

We conducted a series of experiments to examine the impact of the parameters m, efConstruction, and efSearch on the performance of HNSW algorithm. We used different combinations of these parameters and applied them to the cckm_3700 (v3) dataset. Our goal was to evaluate the trade-off between accuracy and efficiency of the HNSW algorithm under various settings.

## Results

| experiment_id | m | efConstruction | efSearch | rouge1 | in_top_init | init_rougeL_recall_median | init_rougeL_precision_median | search_time_in_sec_mean | search_time_in_sec_median | chat_query_time_in_sec_median | Indexing time |
| --- | --- | --- | --- | --- | --- | --- | --- |--- | --- | --- | --- | 
| base (cb1d0982-bba4-4f76-911c-ea7c86372f59) | 4 | 400| 500 | 0.401634949 | 0.835164835 | 0.911764706 | 0.231939163 | 1.410652212 | 1.4081525 | 3.023475 | 29:57 |
| 5060647b-eaee-4d60-808c-fd0ed565259f | 4 | 400 | 1000 | 0.397828372 | 0.835164835 | 0.910828025 | 0.231818182 | 1.41383099 | 1.4058353 | 3.0560547 | 29:45 |
| b16b1788-0829-407e-aec6-f21fde8c01df | 4 | 1000 |  1000 | 0.399506721 | 0.837362637 | 0.910828025 | 0.23364486 | 1.440958611 | 1.4325078 | 2.9502062 | 30:17 |
| 0f796cef-49f5-49fb-bec1-de53f7cf6ebb | 10 | 500 | 500 | 0.400834949 | 0.835164835 | 0.910828025 | 0.229166667 | 1.449671978 | 1.4211985 | 2.890868 | 31:37 |
| 4e274d41-54c7-449a-b1a1-349176ed4e1c | 10 | 1000 | 1000 | 0.403023778 | 0.832967033 | 0.910828025 | 0.231343284 | 1.422677764 | 1.4059503 | 3.0598162 | 29:43 |

Base on our experiments, none of the experiments showed any significant improvements over the baseline result. However, we observed a slight improvement in the experiment with the following parameters: m=4, efConstruction=400 and efSearch=1000 on two questions including 20001 and 20196 but for question 10008, no chunk was retrieved from the associated source. Our recommendation is to keep the current default values for the parameters as per current size of our documents. In terms of indexing time, we do not see any significant changes on duration of uploading documents.