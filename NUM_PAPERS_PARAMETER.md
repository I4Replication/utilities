# Using the `num_papers` Parameter

## Overview

The economics scraper now supports specifying the exact number of papers to collect via the `num_papers` and `num_papers_per_journal` parameters.

## Key Changes

### 1. `scrape_journal()` Function

**New Parameter**: `num_papers` (optional)

```python
def scrape_journal(
    journal_name: str,
    start_year: int,
    end_year: int,
    min_papers: int = 10,
    check_external_repos: bool = True,
    num_papers: Optional[int] = None  # NEW!
) -> List[Dict]
```

**Behavior**:
- If `num_papers` is specified: Collects **exactly** that many papers
- If `num_papers` is `None`: Uses `min_papers` (collects **at least** that many)

### 2. `scrape_all_journals()` Function

**New Parameter**: `num_papers_per_journal` (optional)

```python
def scrape_all_journals(
    start_year: int = 2020,
    end_year: int = 2024,
    topic: Optional[str] = None,
    min_papers_per_journal: int = 10,
    check_external_repos: bool = True,
    num_papers_per_journal: Optional[int] = None  # NEW!
) -> pd.DataFrame
```

**Behavior**:
- If `num_papers_per_journal` is specified: Collects **exactly** that many papers from each journal
- If `num_papers_per_journal` is `None`: Uses `min_papers_per_journal` (collects **at least** that many)

## Usage Examples

### Example 1: Scrape Exactly 50 Papers from AER

```python
from economics_scraper import EconomicsJournalScraper

scraper = EconomicsJournalScraper()

papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2022,
    end_year=2024,
    num_papers=50,  # Collect exactly 50 papers
    check_external_repos=True
)

print(f"Collected {len(papers)} papers")  # Output: Collected 50 papers
```

### Example 2: Scrape 100 Papers from Multiple Journals

```python
scraper = EconomicsJournalScraper()

# Scrape 100 papers from AER
aer_papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2020,
    end_year=2024,
    num_papers=100,
    check_external_repos=True
)

# Scrape 100 papers from QJE
qje_papers = scraper.scrape_journal(
    journal_name='Quarterly Journal of Economics',
    start_year=2020,
    end_year=2024,
    num_papers=100,
    check_external_repos=True
)

print(f"AER: {len(aer_papers)} papers")
print(f"QJE: {len(qje_papers)} papers")
```

### Example 3: Scrape Exactly 10 Papers Per Journal from All Journals

```python
scraper = EconomicsJournalScraper()

df = scraper.scrape_all_journals(
    start_year=2023,
    end_year=2024,
    num_papers_per_journal=10,  # Exactly 10 from each journal
    check_external_repos=True
)

print(f"Total papers: {len(df)}")  # Should be ~150 (15 journals × 10 papers)
print(f"Papers per journal:")
print(df['journal'].value_counts())
```

### Example 4: Scrape 25 Papers Per Journal for Analysis

```python
scraper = EconomicsJournalScraper()

df = scraper.scrape_all_journals(
    start_year=2022,
    end_year=2024,
    num_papers_per_journal=25,
    check_external_repos=True
)

# Analyze replication package availability
with_replication = df['replication_package'].sum()
total = len(df)

print(f"Replication package rate: {with_replication}/{total} ({with_replication*100/total:.1f}%)")

# Save results
scraper.save_to_excel(df, 'analysis_25_papers_per_journal.xlsx')
```

### Example 5: Compare min_papers vs num_papers

```python
scraper = EconomicsJournalScraper()

# Using min_papers (old way) - collects AT LEAST 10 papers
papers_min = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2023,
    end_year=2024,
    min_papers=10,  # Will collect 10+ papers
    check_external_repos=True
)

print(f"With min_papers=10: {len(papers_min)} papers")  # Might be 50, 75, etc.

# Using num_papers (new way) - collects EXACTLY 10 papers
papers_exact = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2023,
    end_year=2024,
    num_papers=10,  # Will collect exactly 10 papers
    check_external_repos=True
)

print(f"With num_papers=10: {len(papers_exact)} papers")  # Will be exactly 10
```

## Differences: `min_papers` vs `num_papers`

| Parameter | Behavior | Use Case |
|-----------|----------|----------|
| `min_papers` | Collects **at least** N papers (may collect more) | When you want a minimum sample size |
| `num_papers` | Collects **exactly** N papers (stops at N) | When you need a specific sample size for analysis |

## Advanced Usage

### Scrape Different Numbers from Different Journals

```python
scraper = EconomicsJournalScraper()

journal_targets = {
    'American Economic Review': 100,
    'Quarterly Journal of Economics': 50,
    'Econometrica': 75,
    'Journal of Political Economy': 60,
}

all_papers = []

for journal, target in journal_targets.items():
    papers = scraper.scrape_journal(
        journal_name=journal,
        start_year=2020,
        end_year=2024,
        num_papers=target,
        check_external_repos=True
    )
    all_papers.extend(papers)
    print(f"{journal}: {len(papers)}/{target} papers")

print(f"\nTotal collected: {len(all_papers)} papers")
```

### Collect Papers Until Target with Error Handling

```python
scraper = EconomicsJournalScraper()

def collect_papers_safely(journal, target, start_year, end_year):
    """Safely collect papers with fallback"""
    try:
        papers = scraper.scrape_journal(
            journal_name=journal,
            start_year=start_year,
            end_year=end_year,
            num_papers=target,
            check_external_repos=True
        )
        return papers
    except Exception as e:
        print(f"Error collecting from {journal}: {e}")
        return []

# Collect from multiple journals
journals = [
    'American Economic Review',
    'Quarterly Journal of Economics',
    'Journal of Political Economy'
]

all_papers = []
for journal in journals:
    papers = collect_papers_safely(journal, 50, 2023, 2024)
    all_papers.extend(papers)
    print(f"{journal}: {len(papers)} papers collected")
```

## Performance Considerations

### Time Estimates

Approximate time to collect papers (with `check_external_repos=True`):

| Papers per Journal | Time per Journal | Total Time (15 journals) |
|-------------------|------------------|--------------------------|
| 10 papers | ~15 seconds | ~4 minutes |
| 25 papers | ~35 seconds | ~9 minutes |
| 50 papers | ~60 seconds | ~15 minutes |
| 100 papers | ~2 minutes | ~30 minutes |

**Note**: Time varies based on:
- Network speed
- External repository response times
- Whether replication packages need to be verified

### Optimizing Performance

For faster scraping when you don't need replication data:

```python
# Disable external repository searches for speed
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2023,
    end_year=2024,
    num_papers=100,
    check_external_repos=False  # Much faster!
)
```

## Tips and Best Practices

### 1. Start Small

When testing or exploring, start with small numbers:

```python
# Test with 5 papers first
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2023,
    end_year=2024,
    num_papers=5,  # Small test sample
    check_external_repos=True
)
```

### 2. Use Appropriate Date Ranges

If you need many papers, use wider date ranges:

```python
# For 100 papers, use wider date range
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2018,  # Wider range
    end_year=2024,
    num_papers=100,
    check_external_repos=True
)
```

### 3. Save Intermediate Results

For large scrapes, save intermediate results:

```python
import pandas as pd

scraper = EconomicsJournalScraper()
journals = ['American Economic Review', 'Econometrica', 'QJE']

for journal in journals:
    papers = scraper.scrape_journal(
        journal_name=journal,
        start_year=2020,
        end_year=2024,
        num_papers=100,
        check_external_repos=True
    )

    # Save immediately
    df = pd.DataFrame(papers)
    filename = f"{journal.replace(' ', '_').lower()}_100_papers.xlsx"
    scraper.save_to_excel(df, filename)
    print(f"✅ Saved {len(papers)} papers from {journal}")
```

### 4. Check Availability First

Some journals may not have enough papers in the date range:

```python
# First check availability
papers_test = scraper.scrape_journal(
    journal_name='Journal of Economic Growth',
    start_year=2023,
    end_year=2024,
    num_papers=5,  # Small test
    check_external_repos=False  # Fast
)

if len(papers_test) < 5:
    print("Warning: Not enough papers in this date range")
    print("Try expanding the date range")
```

## Backward Compatibility

The old way of using `min_papers` still works:

```python
# Old way (still supported)
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2023,
    end_year=2024,
    min_papers=10,  # Old parameter
    check_external_repos=True
)

# New way (more precise)
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2023,
    end_year=2024,
    num_papers=10,  # New parameter - exactly 10 papers
    check_external_repos=True
)
```

## Troubleshooting

### Problem: Not Getting Exact Number Requested

**Cause**: Not enough papers available in date range

**Solution**: Expand the date range

```python
# If this doesn't get 100 papers:
papers = scraper.scrape_journal(
    journal_name='Journal of Economic Growth',
    start_year=2023,
    end_year=2024,
    num_papers=100,
    check_external_repos=True
)

# Try expanding the range:
papers = scraper.scrape_journal(
    journal_name='Journal of Economic Growth',
    start_year=2015,  # Much wider
    end_year=2024,
    num_papers=100,
    check_external_repos=True
)
```

### Problem: Scraping Takes Too Long

**Solution**: Disable external repository searches

```python
# Fast scraping without replication data
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2023,
    end_year=2024,
    num_papers=100,
    check_external_repos=False  # 10x faster
)
```

## Complete Working Example

See [example_usage.py](example_usage.py) for a complete working example with multiple use cases.

```bash
# Run the example
python example_usage.py
```

## Summary

| Feature | Old Way | New Way |
|---------|---------|---------|
| **Single Journal** | `min_papers=N` (at least N) | `num_papers=N` (exactly N) |
| **All Journals** | `min_papers_per_journal=N` | `num_papers_per_journal=N` |
| **Behavior** | Collects ≥ N papers | Collects exactly N papers |
| **Use Case** | Flexible collection | Precise sample sizes |

The new parameters give you precise control over sample sizes, making it easier to:
- Design balanced datasets
- Create consistent test samples
- Conduct controlled comparisons
- Generate reproducible results
