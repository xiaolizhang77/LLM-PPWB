# LLM Project Proposal Writing Benchmark (LLM-PPWB)

<img src=".\favicon.png" alt="favicon" style="zoom:50%;" />
<div align="middle">
  <a href="README.md">English</a> | <a href="README_zh.md">中文</a>
</div>


## Project Introduction

**LLM-PPWB is a benchmark platform designed to evaluate the performance of large language models in project proposal writing tasks.** The platform collects real user evaluations comparing different models' generated project proposals and ranks the models using the ELO rating system and win rates.

## Project Goals

We aim to establish an objective model evaluation system by collecting a large amount of user evaluation data, providing reference for model selection in project proposal writing tasks. After gathering sufficient data, we will organize the backend data into an open-source dataset.

## Main Features

- Model Comparison: Randomly displays responses from two different models to the same question for user evaluation
- Real-time Ranking: Calculates and displays model rankings using the ELO rating system based on user evaluations
- Data Statistics: Records and displays battle results and rating changes between models

## Participating Models

- Ground Truth (Human-written original)
- Deepseek-v3
- Deepseek-r1
- GPT-4o
- Qwen Max
- Qwen3-reason
- Doubao-1.5-pro

## Usage Guide

### Benchmark Website Link

[LLM Project Proposal Writing Benchmark](http://8.140.232.135:54321/)

### Evaluation Features

1. Click "Start Evaluation" to enter the evaluation page, where you can select your area of expertise

   ![image-20250507161231922](.\image\image-20250507161231922.png)

2. Read the project background, context, and responses from two models

   ![image-20250507161345573](.\image\image-20250507161345573.png)

   ![image-20250507161431498](.\image\image-20250507161431498.png)

3. Choose the model response you think is better

   ![image-20250507161431498](.\image\屏幕截图 2025-05-07 161512.png)

4. View the anonymous large model names

   ![](.\image\屏幕截图 2025-05-07 161725.png)

5. Click "Get New Question" or the field name button to get a new evaluation

   ![](.\image\屏幕截图 2025-05-07 162001.png)

### Leaderboard Features

1. Click "Leaderboard" in the navigation bar to enter the leaderboard page

   ![](C:\Users\98750\Desktop\LLM-PPWB\image\屏幕截图 2025-05-07 162102.png)

2. Select your preferred ranking method and data

   ![](C:\Users\98750\Desktop\LLM-PPWB\image\屏幕截图 2025-05-07 162217.png)

## Update Log

[2025.05.05]🎯📢PPWB officially launched: [LLM Project Proposal Writing Benchmark](http://8.140.232.135:54321/).

[2025.05.01]🎯📢Added Qwen3-reason and Doubao-1.5-pro test models.

[2025.04.24]🎯📢PPWB initiated.

## Acknowledgments

We would like to express our gratitude to the National Natural Science Foundation of China, and all the project leaders, participants, and supporting institutions of the National Natural Science Foundation projects.
