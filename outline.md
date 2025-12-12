# Task 2 – Supermarket Dataset

## 1. Data Structure Design

* Define a mapping from item names to integer IDs
* Implement an in-memory sparse representation of item co-occurrences

  * Dictionary keyed by item ID
  * Values are dictionaries mapping co-purchased item IDs to frequencies
* Ensure symmetry by storing each pair in a consistent order

## 2. Data Ingestion and Construction

* Parse the transaction dataset
* Deduplicate items within each transaction
* Convert items to IDs
* For each transaction, update co-occurrence counts for all item pairs

## 3. Core Query Algorithms

* Query items most frequently bought with a given item
* Identify the top N most frequent item pairs across all transactions
* Check whether two given items are often co-purchased
* Implement sorting and ranking logic for query results

## 4. Persistence Layer

* Design an SQLite schema for storing item pairs and frequencies
* Implement export from the in-memory sparse structure to SQLite
* Implement loading logic to reconstruct the in-memory structure from SQLite

## 5. Dimensionality Reduction

* Construct a matrix representation from the sparse structure
* Apply dimensionality reduction to identify latent purchasing patterns
* Represent items in a lower-dimensional space

## 6. Behavioural Analysis Extension

* Use reduced representations to identify similar items
* Extend the approach to customer or transaction representations if applicable
* Use similarity measures in reduced space to categorise purchasing behaviour

## 7. Visualisation

* Reduce dimensionality further for visualisation purposes
* Produce a 3D plot showing item relationships or behavioural groupings
* Highlight strong associations and clusters
  n
