# User Story 110025: basic prompt engineering

## Hypothesis

Experiment with prompt variants on the below hypothesis - this can be done by varying the prompt field in the config .json file. Few shot examples can be drawn from the groundtruth data and agent feedback .xlsx files. Document process and make sure all experiment artifacts are logged according to the experiment framework repo workflow.

----
Instruct the LLM to provide all relevant information about a topic as part of the prompt (prompt engineering)

**Why**: From our observations of the agent trial usage data, agents are looking for the process/step-by-step instructions given a particular query, but don't explicitly ask the question “how”.  

**We believe that** adding few shot examples to LLM to provide step by step instructions where applicable based on the information provided in agent queries

**Will result in** higher-quality LLM-generated content that contains all relevant information retrieved on a topic pertaining to the actions the agent has to take

**We will know we have succeeded when** agent feedback indicates that required information was provided in the LLM response and the number of consecutive queries on the same topic decreases.

## Prompt references

The current default prompt used in the `DomainServices` API if a prompt isn't provided in the domain configuration: 

```python
DEFAULT_PROMPT = '''Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Helpful Answer:'''
```

Example from OpenAI studio - You are an Xbox customer support agent whose primary goal is to help users with issues they are experiencing with their Xbox devices. You are friendly and concise. You only provide factual answers to queries, and do not provide answers that are not related to Xbox.

## Prompt variants

|Variant|
|-|
|[1-slight modification to default](#1---slight-modification-to-default)|
|[2-variation 1 with inline example](#2---variation-1-with-inline-example)|
|[3-rewritten based on openai studio example](#3---rewritten-based-on-openai-studio-example)|
|[4-variation 3 with inline example](#4---variation-3-with-inline-example)|
|[5-grounding generated answers](#5---question-mark-and-casing-used-to-explicitly-ground-generated-answers-in-context)|

### 1 - Slight modification to default

'Use the context delimited by triple backticks to answer the question at the end. Provide step by step instructions if available. First find the relevant information and then answer the question based on the relevant information.

```{context}``

Question: {question}
Helpful Answer:'

String used in JSON config:
"Use the context delimited by triple backticks to answer the question at the end. Provide step by step instructions if available. First find the relevant information and then answer the question based on the relevant information. \n```{context}```\n\nQuestion: {question}\n Helpful Answer:"

### 2 - variation 1 with inline example

'Use the following pieces of context to answer the question at the end. Make sure to provide step by step instructions if the question is about a particular process or action that a customer support agent or customer might perform. As an example,

Question: make a payment
Helpful answer: To make a payment, follow these steps:

1. From the Bills page, click the box next to each bill you want to pay.
2. Click the "Pay" button to pay the selected bill or bills.
3. Enter your payment information, such as your credit or debit card details.
4. Review your payment details and confirm the payment.

Please note that the "Pay" button may not be visible to experts using the CSR tool.

If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Helpful Answer:'

String used in JSON config: "Use the following pieces of context to answer the question at the end. Make sure to provide step by step instructions if the question is about a particular process or action that a customer support agent or customer might perform. As an example,\n\nQuestion: make a payment\nHelpful answer: To make a payment, follow these steps:\n1. From the Bills page, click the box next to each bill you want to pay.\n2. Click the \"Pay\" button to pay the selected bill or bills.\n3. Enter your payment information, such as your credit or debit card details.\n4. Review your payment details and confirm the payment.\nPlease note that the \"Pay\" button may not be visible to experts using the CSR tool.\n\nIf you don't know the answer, just say that you don't know, don't try to make up an answer.\n\nContext:{context}\n\nQuestion: {question}\nHelpful Answer:"


### 3 - Rewritten based on OpenAI studio example

'You are a helpful AI assistant whose primary goal is to help AT&T customer support agents find the information that they need to help customers. You provide a concise summary of all information provided in the context below to answer the question at the end. Include step-by-step information where applicable so agents know exactly what steps they or the customer would need to take to solve or accomplish the issue stated in the question. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Helpful Answer:'

String used in JSON config: "You are a helpful AI assistant whose primary goal is to help AT&T customer support agents find the information that they need to help customers. You provide a concise summary of all information provided in the context below to answer the question at the end. Include step-by-step information where applicable so agents know exactly what steps they or the customer would need to take to solve or accomplish the issue stated in the question. If you don't know the answer, just say that you don't know, don't try to make up an answer.\n\nContext: {context}\n\nQuestion: {question}\nHelpful Answer:"

### 4 - variation 3 with inline example

'You are a helpful AI assistant whose primary goal is to help AT&T customer support agents find the information that they need to help customers. You provide a concise summary of all information provided in the context below to answer the question at the end. Include step-by-step information where applicable so agents know exactly what steps they or the customer would need to take to solve or accomplish the issue stated in the question. As an example,

Question: make a payment
Helpful answer: To make a payment, follow these steps:

1. From the Bills page, click the box next to each bill you want to pay.
2. Click the "Pay" button to pay the selected bill or bills.
3. Enter your payment information, such as your credit or debit card details.
4. Review your payment details and confirm the payment.

Please note that the "Pay" button may not be visible to experts using the CSR tool.

If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Helpful Answer:'

String used in JSON config: "You are a helpful AI assistant whose primary goal is to help AT&T customer support agents find the information that they need to help customers. You provide a concise summary of all information provided in the context below to answer the question at the end. Include step-by-step information where applicable so agents know exactly what steps they or the customer would need to take to solve or accomplish the issue stated in the question. As an example,\n\nQuestion: make a payment\nHelpful answer: To make a payment, follow these steps:\n1. From the Bills page, click the box next to each bill you want to pay.\n2. Click the \"Pay\" button to pay the selected bill or bills.\n3. Enter your payment information, such as your credit or debit card details.\n4. Review your payment details and confirm the payment.\nPlease note that the \"Pay\" button may not be visible to experts using the CSR tool.\n\nIf you don't know the answer, just say that you don't know, don't try to make up an answer.\n\nContext: {context}\n\nQuestion: {question}\nHelpful Answer:"

### 5 - Question mark and casing used to explicitly ground generated answers in context

'You are a helpful AI assistant whose primary goal is to help AT&T customer support agents using a provided context. Use the context delimited by triple backticks to answer the question at the end. Provide step by step instructions if available. First find the relevant information and then answer the question based on the relevant information. DO NOT ANSWER any question outside of the provided context.

```{context}```

Question: {question}?\n Helpful Answer:'

String used in JSON config: "You are a helpful AI assistant whose primary goal is to help AT&T customer support agents using a provided context. Use the context delimited by triple backticks to answer the question at the end. Provide step by step instructions if available. First find the relevant information and then answer the question based on the relevant information. DO NOT ANSWER any question outside of the provided context. \n```{context}```\n\nQuestion: {question}?\n Helpful Answer:"

## Extensions

We could develop a prompt that has a more general response template that includes potential categories for the LLM to fill out as part of its response (and instruct it to disregard a category if it doesn't apply to a particular query/retrieved context).
These categories would be a rough superset of the potential categories of information we would like the LLM to include in potential responses to queries from agents, based on the 

Potential categories:

- Steps for an agent to complete to address the topic:
- Steps for a customer to complete to address the topic:
- Plan information (includes pricing, eligibility, coverage information):
- Dates that response applies to:

## Results

Here are the experiment results based on prompt engineerting techniques. Note that since Domain Service can work only with the prompts with string formats, we have not used system/assistant/user JSON format in our experiments.

|experiment_id|rouge1|rouge2|rougeL|rougeLsum|bert_recall|bert_precision|bert_f1|bert_score|
|---|---|---|---|---|---|---|---|---|
|1-96a26533-1444-42d8-a38d-597434f07b6e|0.464190318|0.319409832|0.3955629|0.426632753|0.873652458|0.884167433|0.877369285|0.957094467|
|2-cf19ec0a-c4bc-4204-82ce-64e935973a1d|0.420861609|0.268873935|0.338278502|0.38134444|0.881624222|0.863297582|0.87036097|0.95090704|
|3-1145ad8d-e86b-4351-906a-33b736a1c901|0.436871959|0.288814576|0.357325163|0.395683866|0.876718402|0.866972446|0.871882319|0.952520691|
|4-6903642e-ea10-4f79-9b25-858841ed2a2a|0.423434123|0.272625004|0.343890778|0.382959004|0.881981373|0.863449275|0.872004986|0.951750736|
|5-afd960f0-2203-43ba-bd96-272025dbfd77|0.458351226|0.318299079|0.395052585|0.420049516|0.872745872|0.882483482|0.877296925|0.956881044|
|default-6ae14e6e-835a-4bf7-b4ea-dd9e1ff3a879|0.463414155|0.31607014|0.389953448|0.41989279|0.876588345|0.884575009|0.880731583|0.957281759|



As per our stasticall analysis, although we see very minor improvements in the rouge/bert metrics, the results are not statistically different. For further information on our statistical analysis, refer to [the result Excel file](results.xlsx) or [storage account](https://portal.azure.com/#view/Microsoft_Azure_Storage/BlobPropertiesBladeV2/storageAccountId/%2Fsubscriptions%2F81b4ec93-f52f-4194-9ad9-57e636bcd0b6%2FresourceGroups%2Fblackbird-prod-storage-rg%2Fproviders%2FMicrosoft.Storage%2FstorageAccounts%2Fblackbirdproddatastore/path/askatt-experiment-msft-colab%2Fexperiments%2Fcckm_240%2Fv2%2Fleaderboard.csv/isDeleted~/false/tabToload~/3). Note that since the results for prompt 1, 5 and the default prompt were very close, we did only statistical analysis on the results from these three prompts. The other prompts including prompt 2, 3 and 4, in most cases we observed poorer results in comparison to the default prompts. In prompt 2 and 4, we have used a few shot example technique to improve the generated answers but the results implies that providing the shot is not helping LLM.

We performed multiple t-tests to compare different results from different prompts. Here is the test result for BERT F1 scores obtained from the default prompt and the prompt 5. The p-value of this test (0.180449162) was greater than 0.05, indicating that there was no statistically significant difference between the mean scores of the two prompts.


|t-Test: Two-Sample Assuming Unequal Variances||||
|---|---|---|---|
||Default|Prompt 5||
|Mean|0.886117558|0.883262303||
|Variance|0.00237288|0.002486194|
|Observations|498|498|
|Hypothesized Mean Difference|0|||
|df|993|||
|t Stat|0.914076913|||
|P(T<=t) one-tail|0.180449162|||
|t Critical one-tail|1.646389579|||
|P(T<=t) two-tail|0.360898324|||
|t Critical two-tail|1.962355844|||


We also analyzed how the generated answers are grounded based on the provided context. The number of matching chunks for this question after reranking is zero. Here are a few examples of generated answers using the provided contexts:

 Question|Answer|
|---|---|
| Does apple care replacement exclude a device from next up trade-in?|Ground Truth: AT&T AppleCare Purchase Policy AppleCare is only available to be sold with new device purchases: Certified Restored and BYOD devices are excluded.|
|Prompt 1| There is no information provided in the given context about Apple Care replacement excluding a device from Next Up trade-in.|
|Prompt 2| Apple Care replacement does not necessarily exclude a device from the Next Up trade-in program. However, the device must be in good working condition and meet the eligibility requirements for the trade-in program. It is important to ensure that the device is not damaged, has no cracks or water damage, and is functioning correctly. If the Apple Care replacement device meets these criteria, it should be eligible for the Next Up trade-in program.|
|Prompt 3|I don't have enough information to answer this question.|
|Prompt 4|The provided context does not specifically mention if an Apple Care replacement device is excluded from the Next Up trade-in program.|
|Prompt 5|The provided context does not mention any exclusion of Apple Care replacement devices from the Next Up trade-in program.|
|default|Yes, AppleCare replacement devices are eligible for the Next Up trade-in program as long as they meet the program's requirements and are in good working condition.|

In this example, the generated answer using prompt 2 and default are not grounded and so LLM is using its own pre-trained data to answer the question which may not be a valid/updated answer based on the provided the context but for prompt 1, 3, 4 and 5, the generated answer implies that LLM has not been provided with any relevant context to answer the question. Our analysis shows that we have a similar behavior for more than 12% of all questions.

Since most agent looks for a step-by-step guide for their question, we did some basic prompt engineering to instruct LLM to provide a step by step answer if it is possible based on the provided context. Here are the outputs of an example from the test set with the provided answers:


 Question|Answer|
|---|---|
| Number change|Ground Truth: A number change can be done in the context of SIM activations, such as reconnecting or resuming service with a different number. This may occur when a customer moves from one market to another or when combining or splitting accounts.|
|Prompt 1| To change a phone number, follow these steps: <ul><li>Contact your service provider's customer support.</li> <li>Provide them with the necessary information, such as your account details and the reason for the number change.</li> <li>The customer support representative will guide you through the process and inform you of any fees or requirements associated with the number change.</li> <li>Once the process is complete, your phone number will be changed, and you may need to power cycle your device for the changes to take effect.</li></ul>|
|Prompt 2| To change your phone number, follow these steps: <ul><li>Contact customer support to request a number change. They will need to verify your account information and confirm the reason for the number change. <li>Once your request is approved, the customer support agent will provide you with a new phone number.</li> <li>Power off your device and wait for a few minutes.</li> <li>Power on your device, and the new number should be active.</li></ul> Please note that there might be fees associated with changing your phone number, and the process may take some time to complete.|
|Prompt 3| "To change a phone number, the customer must follow these steps: <ul><li> Contact AT&T customer support to request a mobile number change. </li><li>The customer may receive an SMS confirmation during the number change transaction. They will need to respond correctly.</li><li> Once the number change is complete, the customer should power cycle their device (turn it off and on) for the changes to take effect immediately.</li></ul>Note that devices are systematically provisioned within 24-48 hours after the number change.|
|Prompt 4|To change a phone number, follow these steps: <ul><li>Verify the account and user information.</li><li>Check if the customer is eligible for a number change.</li><li>Inform the customer about any fees associated with the number change.</li><li>Process the number change request in the appropriate system.</li><li>Provide the customer with their new phone number.</li><li>Instruct the customer to power cycle their device for the changes to take effect.</li></ul>Please note that certain conditions may apply, and the customer may need to visit a retail location for specific requests.|
|Prompt 5|To change a contact number, follow these procedures:<ul><li>If the FAN Contact's number is listed in FaST, follow the FAN Profile Updates - FaST - BCSS process.</li><li>The change will be effective immediately.</li></ul>|
|default|To change your phone number, you will need to contact your service provider's customer support or visit a retail location. They will guide you through the process and any fees associated with changing your number. Keep in mind that changing your number may also require updating your contact information on various accounts and notifying your contacts of the change.|

As shown in the table above, LLM with the default prompt did not produce a step by step answer for the question but the rest of prompts instructed LLM to generated a step by step answer.

We also investigated another category of questions which they are outside of ATT customer agent scope. Here is an example of generated answers based on all designed prompts:

 Question|Answer|
|---|---|
|What is the meaning of the life||
|Prompt 1| The meaning of life is a philosophical question and cannot be answered based on the provided context.|
|Prompt 2| I don't know the meaning of life, as it is a philosophical question that has been debated for centuries and varies depending on individual beliefs and perspectives.|
|Prompt 3| I'm sorry, but the context provided does not contain information related to the meaning of life.|
|Prompt 4|I'm sorry, but as an AI language model, I am not able to provide a definitive answer to the meaning of life. The meaning of life is a philosophical question that has been debated by humans for centuries and may vary depending on individual beliefs and perspectives.|
|Prompt 5| I cannot answer that question as it is outside of the provided context.|
|default|The meaning of life is a philosophical question and can vary depending on individual beliefs and perspectives. Some may find meaning in personal relationships, career success, or spiritual beliefs, while others may believe life has no inherent meaning and it is up to each individual to create their own purpose.|

As shown in the table above, LLM handles the question which is outside of scope properly and the provided answer explicitly implies that LLM does not answer it since it is outside of the defined scope as per the instructed prompt. We see a similar behavior with the same types of the question from the test sets.

We also added a question mark to the end of the question using the provided prompts that helps LLM to answer the question better. Here is an example of the generated answers with different prompts.

 Question|Answer|
|---|---|
|Payment Arrangement||
|Prompt 5| If Clarify is down, payment arrangement options can be viewed via the standalone ExpressPay link in Quick Links.|
|Default|I'm sorry, but I cannot assist with payment arrangements as I am an AI language model and do not have access to account information. Please contact AT&T customer service for assistance with payment arrangements.|


## Conclusion

As per our statistical analysis, the generated answers from default prompt, variant 1 and 5 have a very similar accuracy and there is no significant changes between the averages of their Rouge and Bert metrics. However, prompt 5 generally provides more grounded answers based human judgments as shown in a few examples in this analysis. We recommend to use prompt 5 since it has a better instruction to handle out side of scope Ask ATT care questions and also handles better the questions that their provided contexts do not have enough information relevant to the question.
