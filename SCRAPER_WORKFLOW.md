# Economics Scraper Workflow

## Visual Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Economics Journal Scraper                     │
│                         (Main Entry Point)                       │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ├──► scrape_journal()          (Single journal)
                 │
                 └──► scrape_all_journals()     (All 15 journals)
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
  ┌─────────────┐                       ┌─────────────┐
  │  CrossRef   │                       │  Parse      │
  │  API Call   │──────────────────────►│  Papers     │
  │             │                       │             │
  └─────────────┘                       └──────┬──────┘
                                               │
                                               │ For each paper
                                               ▼
                                  ┌────────────────────────┐
                                  │ detect_replication_    │
                                  │ package()              │
                                  └────────┬───────────────┘
                                           │
                    ┌──────────────────────┴────────────────────────┐
                    │                                               │
                    ▼                                               ▼
            ┌───────────────┐                              ┌───────────────┐
            │ Abstract/Title│                              │   Is AER/AEA  │
            │ URL Check     │                              │   Journal?    │
            └───────┬───────┘                              └───────┬───────┘
                    │                                              │
                    │ No URL found                                 │
                    │                                              │
                    ▼                                              ▼
            YES ────────► Return URL                    ┌──────────┴──────────┐
                                                        │                     │
                                                        ▼                     ▼
                                            ┌──────────────────┐   ┌──────────────────┐
                                            │ AER Hierarchy    │   │ Other Hierarchy  │
                                            └────────┬─────────┘   └────────┬─────────┘
                                                     │                       │
                          ┌──────────────────────────┴───┐     ┌────────────┴─────────┐
                          │                              │     │                      │
                          ▼                              ▼     ▼                      ▼
                  ┌──────────────┐            ┌──────────────┐│            ┌──────────────┐
                  │ 1. AER Page  │            │ 2. openICPSR ││            │ 1. Zenodo    │
                  │              │            │              ││            │              │
                  │ aeaweb.org/  │            │ Project +    ││            │ API Search   │
                  │ articles?id= │            │ DOI Search   ││            │ DOI + Title  │
                  └──────┬───────┘            └──────┬───────┘│            └──────┬───────┘
                         │                           │        │                   │
                         │ Found?                    │        │                   │
                         ├──YES──► Return            │        │                   ├──YES──► Return
                         │                           │        │                   │
                         NO                          │        │                   NO
                         │                           │        │                   │
                         └───────────────────────────┘        │                   │
                                     │                         │                   │
                                     │ Found?                  │                   │
                                     ├──YES──► Return          │                   │
                                     │                         ▼                   │
                                     NO                ┌──────────────┐            │
                                     │                 │ 2. Harvard   │            │
                                     │                 │  Dataverse   │            │
                                     │                 │              │            │
                                     │                 │ API + DOI    │            │
                                     │                 └──────┬───────┘            │
                                     │                        │                    │
                                     │                        │ Found?             │
                                     │                        ├──YES──► Return     │
                                     │                        │                    │
                                     │                        NO                   │
                                     │                        │                    │
                                     ▼                        ▼                    ▼
                              ┌──────────────┐         ┌──────────────┐    ┌──────────────┐
                              │ 3. Zenodo    │         │ 3. OSF       │    │ 4. Journal   │
                              │              │         │              │    │  Website     │
                              │ Fallback     │         │ DOI + Title  │    │              │
                              └──────┬───────┘         └──────┬───────┘    │ Supplements  │
                                     │                        │             └──────┬───────┘
                                     │ Found?                 │ Found?             │
                                     ├──YES──► Return         ├──YES──► Return    │ Found?
                                     │                        │                    ├──YES──► Return
                                     NO                       NO                   │
                                     │                        │                    NO
                                     └────────────────────────┘                    │
                                                  │                                │
                                                  └────────────────────────────────┘
                                                                 │
                                                                 ▼
                                                       ┌──────────────────┐
                                                       │ No replication   │
                                                       │ package found    │
                                                       └──────────────────┘
```

## Process Flow

### 1. Paper Collection

```
User Input
   ├─► journal_name
   ├─► start_year / end_year
   ├─► num_papers (optional)
   └─► check_external_repos (boolean)
         │
         ▼
CrossRef API
   ├─► Query by ISSN + date range
   ├─► Fetch paper metadata
   └─► Parse: title, authors, DOI, abstract
         │
         ▼
For Each Paper ──► detect_replication_package()
```

### 2. Replication Package Detection

```
detect_replication_package(title, abstract, DOI, journal, authors)
   │
   ├─► Step 1: Check abstract/title for URLs
   │     └─► If found ──► Verify ──► Return
   │
   ├─► Step 2: Determine journal type
   │     ├─► AER/AEA? ──► AER Hierarchy
   │     └─► Other    ──► Standard Hierarchy
   │
   ├─► Step 3: Execute hierarchical search
   │     └─► Stop at first match
   │
   └─► Step 4: Return (has_package, URL)
```

### 3. AER-Specific Flow

```
AER Paper (DOI: 10.1257/aer.XXXXXXXX)
   │
   ▼
1. Access: https://www.aeaweb.org/articles?id=DOI
   │
   ├─► Parse HTML
   │
   ├─► Find <a> with text "Replication Package"
   │
   ├─► Extract href (typically: https://doi.org/10.3886/E######V#)
   │
   └─► Success? ──YES──► Return openICPSR DOI
         │
         NO
         │
         ▼
2. Search openICPSR directly
   │
   ├─► Search by DOI
   ├─► Search by title + author
   └─► Calculate match score
         │
         └─► Best match > 0.4? ──YES──► Return URL
               │
               NO
               │
               ▼
3. Fallback to Zenodo, Dataverse, OSF
```

## Title Matching Algorithm

```
_calculate_title_similarity(title1, title2)
   │
   ├─► Split titles into words
   │
   ├─► Filter words: length > 3 characters
   │
   ├─► Convert to sets (lowercase)
   │
   ├─► Calculate Jaccard similarity:
   │     similarity = |intersection| / |union|
   │
   └─► Return: 0.0 to 1.0
         │
         Example:
         title1 = "The Impact of Climate Change"
         title2 = "Impact Climate Change Policies"

         words1 = {impact, climate, change}
         words2 = {impact, climate, change, policies}

         intersection = {impact, climate, change} = 3
         union = {impact, climate, change, policies} = 4

         similarity = 3/4 = 0.75
```

## Composite Scoring (openICPSR)

```
For each search result:
   │
   ├─► title_similarity = Jaccard(paper_title, result_title)
   │
   ├─► word_match_ratio = matching_words / total_words
   │
   ├─► author_match = 1 if author in result else 0
   │
   └─► final_score = (title_similarity × 0.6)
                    + (word_match_ratio × 0.3)
                    + (author_match × 0.1)
         │
         └─► score ≥ 0.4? ──YES──► Valid match
```

## Data Flow Example

```
Input:
  journal = "American Economic Review"
  year = 2023
  num_papers = 50

Process:
  1. Query CrossRef ───► Get 50 AER papers from 2023
  2. For each paper:
       │
       ├─► Extract: title, DOI, authors
       │
       ├─► Is AER? YES
       │
       ├─► Check https://www.aeaweb.org/articles?id=DOI
       │     │
       │     ├─► Find "Replication Package" link
       │     │
       │     └─► Extract: https://doi.org/10.3886/E199265V1
       │
       └─► Store: {
             'title': '...',
             'doi': '10.1257/aer.20211523',
             'replication_package': 1,
             'replication_url': 'https://doi.org/10.3886/E199265V1',
             ...
           }

Output:
  50 papers with replication data
  38/50 (76%) have replication packages
  All 38 are openICPSR DOIs
```

## Error Handling

```
Try:
   │
   ├─► Access URL
   │
   ├─► Parse response
   │
   └─► Extract data
         │
         ▼
Catch:
   ├─► 403 Forbidden ──► Use alternative access method (AER)
   │
   ├─► Timeout ──► Log and continue
   │
   ├─► Network error ──► Retry once, then skip
   │
   └─► Parse error ──► Log and return empty
         │
         ▼
Always:
   └─► Continue to next paper/repository
```

## Performance Optimization

```
Sequential Processing:
  Paper 1 ─► Repository Search ─► Paper 2 ─► ...
  Time: ~1.2s per paper

Optimization Strategies:
  │
  ├─► 1. Early termination
  │     └─► Stop at first repository match
  │
  ├─► 2. Skip external repos
  │     └─► check_external_repos=False (10x faster)
  │
  ├─► 3. Hierarchical search
  │     └─► Most likely source first
  │
  └─► 4. Caching (future)
        └─► Cache successful DOI→URL mappings
```

## Summary Statistics Flow

```
All Papers
   │
   ├─► Group by journal
   │     └─► Count, replication rate
   │
   ├─► Group by topic
   │     └─► Count, replication rate
   │
   ├─► Group by year
   │     └─► Count, trends
   │
   └─► Export to Excel
         ├─► Sheet: All Papers
         ├─► Sheet: By Journal
         ├─► Sheet: By Topic
         ├─► Sheet: Replication Stats
         └─► Sheet: Papers with Replication
```

## Key Design Decisions

1. **Hierarchical Search**
   - Most likely sources checked first
   - Stops at first match (efficiency)
   - Journal-specific strategies

2. **Title Matching**
   - Jaccard similarity (set-based)
   - Filters short words
   - Combined with author matching

3. **Error Tolerance**
   - Continues on errors
   - Logs but doesn't crash
   - Multiple fallback options

4. **Rate Limiting**
   - 1 second between CrossRef requests
   - Respects API guidelines
   - Prevents server overload

5. **Verification**
   - URLs checked for validity
   - Content verified when possible
   - Reduces false positives
