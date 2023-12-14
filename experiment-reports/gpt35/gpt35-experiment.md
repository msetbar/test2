**Observations of GPT3.5 16K Experiment**

 The dataset and groundtruth used was the cckm_3700-v3 of ~3900 articles/457 questions. 
 Dataset : cckm_3700 v3

 Defaults:
 ```
  "index_definition": {
    "semantic_configuration_name": "semantic_configuration"
  },
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
  "chain_type": "stuff",
  "loader_kwargs": {
    "content_key": "BW_Article_Details__c",
    "jq_schema": ".",
    "metadata_func": "care_metadata",
    "text_content": false
  },
  "k_milvus": 20,
  "search_db_type": "azure_cognitive_search",
  "prompt": "You are a helpful AI assistant whose primary goal is to help AT&T customer support agents using a provided context. Use the context delimited by triple backticks to answer the question at the end. Provide step by step instructions if available. First find the relevant information and then answer the question based on the relevant information. DO NOT ANSWER any question outside of the provided context. \n```{context}```\n\nQuestion: {question}?\n Helpful Answer:"
  ``` 

  The configuration that was switched is deployment_name/model_version from **gpt-4-32k/0314** to below:

```
    "llm_class_name": "AzureChatOpenAI",
    "llm_kwargs": {
        "deployment_name": "gpt-35-turbo-16k",
        "temperature": 0,
        "max_tokens": 3000,
        "verbose": true,
        "model_version": "0613"
    },
```

With the max chunk size of 1500 characters and approximating 4 characters/token, the total tokens used for the request ~ 1500/4 = 375 * 20 chunks = 7500 tokens which is well under the total 13K token. (max_tokens=3K for the response)

| **No.** | **Experiment ID**                    | **In Top** | **Recall** | **Median Response Time(s)** |**Similarity Search Response Time(s)**| **Generative RougeLRecall** | **Generative Recall Bert** | **Generative Precision Bert**| **Rescaled Bert Score**| **GPT4 metric>5%**|
|---------|--------------------------------------|------------------------------|--------------------|-|----------------------------|--------------------|--------------------------------|----------------|---|--|
| 1       | 33d642c4-3f36-421f-b28f-e032446f50f0 (GPT4) | 0.83                                   | 0.91                     |10.5|1.4|  0.38|0.87                    | 0.88 |0.57|93
| 2       |52caf4ca-d0ee-47dd-b2e5-1028009fd848 (GPT3.5)                          | 0.83               | 0.91             |         2.76|1.42                   | 0.32             |0.86                  | 0.87 |0.54|91

With the exception of the Generative Rouge L recall which has dropped by 0.06, almost all numbers are identical. However, there is a big improvement in overall chat response time to roughly 1 and half secs for the LLM call from prior 9 secs for `k_milvus=20`.

We added a new metric [GPT4 > 5 %](../../src/evaluation_framework/README.md#evaluating-with-gpt) using GPT4 to compare the quality of the LLM. (Also using GPT3.5 for experiment analysis yielded similar results.). Also manually analyzed some of the answers between GPT3.5 and GPT 4 and found that:
- Both the answers are mostly comparable. However GPT4 definitely does better in a small set of cases where the question can be interpreted differently or is vague. 
```
Example 1:

Can I add a line to the AT&T Mobile Share Plus for Business? 

Ground Truth: AT&T will not accept orders for new services, add-a-lines, and rate plan changes. However, AT&T will continue to allow our existing customers on these plans if groups have not reached the maximum lines allowed.

GPT4 - Score 9: As of December 14, 2022, Mobile Share Plus for Business plans are on a sales hold. AT&T will not accept orders for new services, add-a-lines, and rate plan changes. However, existing customers on these plans can continue to use them if groups have not reached the maximum lines allowed.

GPT3.5 - Score 4 : Yes, you can add a line to the AT&T Mobile Share Plus for Business plan.

Example 2:

Can I provide the customer their bill detail?

Ground Truth: No, you cannot provide bill detail; however, you can confirm it, if the customer is verified.

GPT4 - Score 7: No, you cannot provide billed or unbilled details over the phone, chat, or via fax, email, or SMS to anyone, including verified callers, employees, dealer/agents, national retailers, managers, or in lost/stolen scenarios. Instead, you can guide the customer to view their call, text, and data usage details online 24/7 at no charge at att.com and m.att.com.

GPT3.5 - Score 4 : Yes, you can provide the customer with their bill detail. You can walk them through the self-service options to view and print the last 16 months of details. Alternatively, you can assist them in accessing their bill online or provide them with a paper copy of their bill.
```

- GPT3.5 answers seem to be better formatted in most cases

```
What if the name does not match FAN contact name associated with the PIN?

GPT3.5 - Score 8
If the name provided by the caller does not match the FAN contact name associated with the PIN, you should follow these steps:

1. In FaST, send an Auto Generated PIN to the owner of the misused PIN.
2. Advise the customer of the PIN error and apologize for the inconvenience. Use the suggested verbiage: "I apologize, but I am unable to validate your PIN. It appears that you may be using an incorrect PIN, or a PIN that has already been assigned to someone else on the account. I am happy to assist you with your request, but I need to verify some additional information regarding your account."
3. Discard the Clarify interaction.
4. Re-enter the CTN and select the correct Caller Name and Role from the Caller List.
5. Verify the customer as outlined in the Account Verification Process - BCSS.

By following these steps, you can address the issue of a mismatch between the caller's name and the FAN contact name associated with the PIN.

GPT4 - Score 9
If the name does not match the FAN contact name associated with the PIN, you should follow the steps in the PIN/Name Mismatch section of the PIN Maintenance - BCSS. This involves sending an Auto Generated PIN to the owner of the misused PIN, advising the customer of the PIN error, discarding the Clarify interaction, re-entering the CTN, selecting the correct Caller Name and Role from the Caller List, and verifying the customer as outlined in the Account Verification Process - BCSS.
```

**Cost**

| **Model** | **Input**                    | **Output** | **Request Cost** | **Output Cost** |**Total Cost/query** 
|---------|--------------------------------------|------------------------------|--------------------|-|----------------------------|
| GPT 4-32K       | $0.06/1K tokens | $0.12/1K tokens                                   | 7500/1000 * 0.06 = 0.45                     |3000/1000 * 0.12 = 0.36 |0.81
| GPT 3.5 Turbo       |$0.003/1K tokens                          | 0.004/1K tokens               | 7500/1000 * 0.003 = 0.02             |         3000/1000 * 0.004 = 0.012 |0.03                   | 0.32


**Conclusion**

Overall since the quality difference is not that big but the price is 27 times cheaper, GPT3.5 seems to be the better approach to take. And the gain in performance is also very high. The default configuration will be modified to reflect the same.

**References**

1. [Azure OpenAI Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/)

