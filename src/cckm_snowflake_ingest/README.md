# CCKM Snowflake Ingest <!-- omit in toc -->

## Table of Contents <!-- omit in toc -->

- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Installing Necessary Dependencies](#installing-necessary-dependencies)
  - [Setting .ENV](#setting-env)
  - [Ingesting CCKM Data](#ingesting-cckm-data)

## Overview

This directory contains programs related to ingesting CCKM data from snowflake.
This project is temporary and should be deprecated once the end-to-end ADLS Gen 2 integration work is finished.

## Getting Started

Before following the steps below, ensure you poetry environment is setup.
To setup your poetry environment, please review [this document](../../README.md#installation)

### Installing Necessary Dependencies

To install the dependencies run the following command:

```bash
poetry install --with ingest
```

The command above installs all the dependencies that are required for the ingestion logic but not experimentation.

### Setting .ENV

Before running the program, you `.env` file needs to be configured.
Start with copying the `.sample.env` to get started with your `.env` file.
To copy the `.sample.env` file into `.env`, run the following command.

```bash
cp .sample.env .env
```

Ensure the variables are updated to the correct values.
The variables that need to be set are:

- **SNOWFLAKE_USERNAME**: Your AT&T ID.
- **SNOWFLAKE_PASSWORD**: Your upstart password.
- **SNOWFLAKE_ACCOUNT**: The snowflake account name.
- **SNOWFLAKE_WAREHOUSE**: The snowflake warehouse with the CCKM data.
- **SNOWFLAKE_DATABASE**: The snowflake database with the CCKM data.

### Ingesting CCKM Data

To ingest the data run the following command:

```bash
python -m main \
    --sub-folder <path-to-output-data>
```

There are a few flags for this program:

- **--sub-folder** [REQUIRED]: The sub-folder to write the data to under the ./output folder.
- **--article-number-key** [DEFAULT=ArticleNumber]: The article number (used as the file name).
