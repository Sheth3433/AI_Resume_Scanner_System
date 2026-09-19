# Deep Learning Pipeline

## Overview
The app uses a pretrained sentence-transformer model to convert resume chunks and job descriptions into dense vector embeddings.

## Why this is valid deep learning
The model is a transformer encoder that produces contextual vector representations. It is loaded once during startup and used for inference on each user's resume.

## Embedding flow
Resume text
  ↓
Chunk into meaningful sections or paragraphs
  ↓
SentenceTransformer encoder
  ↓
Dense embedding vector
  ↓
Normalize vector
  ↓
Cosine similarity against job description embeddings

## Aggregation approach
For longer resumes, the text is split into manageable chunks by section and paragraph. Each chunk is embedded separately, then chunk embeddings are averaged to create a single aggregate vector summarizing the resume. This avoids token overflow while preserving section-level semantics.

## Training vs inference
This project does not retrain on each upload. Training is a one-time offline step for the pretrained model. Runtime is inference only on new resumes.
