# User Story 112014: Analysis of the input documents and best result.

The results of this analysis is summarized in notebook and HTML interactive formats. It covers three cases:

-   Analysis on the 3774 CCMK source files (analysis_3770_ccmk.ipynb/.html).
-   Analysis on the current evaluation QnAs pairs (QnA_CCMK_analysis.ipynb/.html).

----

## Features

The following is the list of features which were extracted and analyzed:
-   BW_TXNMY_GRP_1: main category for the article. It was provided from the source.
-   BW_TXNMY_GRP_2: sub-category for the article. It was provided from the source.
-   \#tables: the count of the tables in the article.
-   article_wtag_len: the length of the article including tags.
-   article_notag_len: the length of the article without any tags (just plain text).
-   table_wtage_len: the length of the tables including tags.
-   table_wotage_len: the length of the tabled without any tags (just plain text).
-   question_len: the character length of the questions in the eval QnAs.
-   answer_len: the character length of the groundtruth answer in the eval QnAs.
-   rouge_precision: the rouge precision between the groundtruth answer and the source article.


----

## Files:

-    3700ccmk.csv: contains the 3904 source articles information and features.
-    3900_v3_ccmk.csv: contains the 3774 source articles information and features.
-    ground_truth_455.csv: contains 457 QnA pairs after cleaning missing source Qs.
-    ground_truth_500.csv: contains the original v2 500 QnA pairs.
-    low_rouge.csv: low_rouge QnAs from the 455 questions. The rouge_precision is calculated between the answers and their source article and the used threshold is 0.7.
-   get_chunks_src.ipynb: a notebook to add unique sources for the chunks as a new column.
