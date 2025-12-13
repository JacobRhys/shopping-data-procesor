# CUDA and Latent-Factor Recommendations

## Overview

I would like to use some CUDA librars to give my self the opertunity to learn new skills, my decision to take this aproach is driven by py pask experience using LSA and a desire to use CUDA in a suefull mannor.

The idea is to use a latent factor approach similar to Latent Semantic Analysis (LSA). This document explains on how this and that pipeline could benefit from CUDA/GPU acceleration.

I will impliment this first using numpy and then using CUDA

## From Co-Occurrences to a Matrix

1. Each grocery item is assigned an integer ID and stored in the in-memory `CoOccurrenceStore`.
2. For each basket:
   - Items are deduplicated within the transaction.
   - Undirected co-occurrence counts are updated betwween all items in the basket.
3. Co-occurrence counts are kept sparsely:
   - `counts[min_id][max_id] = frequency`.

From this structure we can construct an item–item matrix `M`:

- Rows and columns correspond to items, in a fixed order.
- Entry `M[i, j]` is the co-occurrence count between `items[i]` and `items[j]`.
- The matrix is symmetric; the diagonal can be zero.

This is analogous to the term–term matrix used in LSA for text.

## Truncated SVD for Item Embeddings

To uncover latent “shopping factors”, we apply truncated Singular Value Decomposition (SVD) to the item–item matrix `M`:

- Compute an approximate factorisation:

  \[
  M \approx U_k \Sigma_k V_k^\top
  \]

  with only the top `k` singular values/vectors kept.

- For a symmetric item–item matrix, \( U_k \approx V_k \), so we can derive a compact embedding matrix:

  - Each row `X[i]` (often constructed from `U_k` and `Σ_k`) is a low-dimensional vector for item `i`.
  - Each dimension of `X` corresponds to a latent “factor” such as breakfast foods, drinks, baking ingredients, etc.

Conceptually, this is the same idea as:

- **LSA** on term–document matrices: words that occur in similar documents end up near each other in the latent space.

Here, items that appear in similar baskets receive similar embeddings.

## Recommendation Using Embeddings

Once we have item embeddings:

- **Single-item recommendation**
  - Given an item `q`, find its vector `v_q`.
  - Compute cosine similarity between `v_q` and every other item vector.
  - Sort by similarity, exclude `q`, and return the top-k items as recommendations.

- **Basket (multi-item) recommendation**
  - For a set of items `{q₁, q₂, …, q_m}`, average their vectors:

    \[
    v_{\text{basket}} = \frac{1}{m} \sum_i v_{q_i}
    \]

  - Compute cosine similarity between `v_basket` and all item vectors.
  - Sort and return the top-k items not already in the basket.

- **Customer offer recomendation**
  - For a set of 'baskets' by a customer find the neerest avarage item that has not been purchaced, so that the 

This latent-space approach goes beyond raw co-occurrence counts by capturing indirect relationships and smoothing noise.

## Where CUDA/GPU Acceleration Fits

In this project the dataset is modest (167 items), so CPU-based SVD is sufficient. However, for larger supermarkets or multi-store datasets with many thousands of items, the SVD step becomes computationally heavy and is the natural target for CUDA acceleration.

The general pattern for GPU use would be:

1. **Matrix construction**
   - Build the sparse item–item matrix `M` on CPU as now (e.g. SciPy sparse), or directly construct it on GPU using a CUDA-aware sparse library.

2. **GPU-based SVD/PCA**
   - Move `M` to GPU memory and apply a GPU-accelerated truncated SVD or PCA implementation (e.g. cuML, cuSolver).
   - This leverages many-core parallelism to handle large matrices significantly faster than a single CPU.

3. **Embedding and recommendation**
   - Obtain the low-dimensional embeddings `X` on GPU.
   - Either:
     - Keep `X` on GPU and perform cosine similarity and nearest-neighbour search there, or
     - Transfer `X` back to CPU for recommendation queries if the embedding is small.

In other words:

- The **data structure and query design** in this project (co-occurrence store, matrix view, recommendation functions) are already compatible with a CUDA-backed pipeline.
- For large-scale deployments, only the matrix factorisation and similarity search layers need to be swapped out for GPU-accelerated equivalents.

## Summary

- We will build a sparse item–item co-occurrence representation from transactional data.
- This structure can be converted into a matrix and factorised via truncated SVD, in the same spirit as LSA and word2vec-style embeddings.
- The resulting embeddings support recommendation-style queries by nearest neighbours in a latent space.
- CUDA/GPU acceleration becomes valuable when scaling SVD and similarity computations to much larger item universes; the current design makes it straightforward to plug in GPU-backed implementations for these steps.