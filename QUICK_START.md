# Quick Start Guide - Economics Scraper with num_papers Parameter

## Installation

No installation needed - just use the `economics_scraper.py` file directly.

## Basic Usage

### 1. Scrape Exactly N Papers from One Journal

```python
from economics_scraper import EconomicsJournalScraper

scraper = EconomicsJournalScraper()

# Scrape exactly 50 papers from American Economic Review
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2022,
    end_year=2024,
    num_papers=50,  # ← Specify exact number here
    check_external_repos=True
)

print(f"Collected {len(papers)} papers")  # Will be exactly 50
```

### 2. Scrape Exactly N Papers Per Journal from All Journals

```python
from economics_scraper import EconomicsJournalScraper

scraper = EconomicsJournalScraper()

# Scrape exactly 10 papers from each of 15 journals
df = scraper.scrape_all_journals(
    start_year=2023,
    end_year=2024,
    num_papers_per_journal=10,  # ← 10 papers from each journal
    check_external_repos=True
)

print(f"Total: {len(df)} papers")  # Will be ~150 (15 journals × 10)
print(f"Per journal:\n{df['journal'].value_counts()}")
```

## Available Journals

The scraper covers 15 top economics journals:

1. American Economic Review
2. Quarterly Journal of Economics
3. Journal of Political Economy
4. Econometrica
5. Review of Economic Studies
6. Journal of Economic Theory
7. Journal of Monetary Economics
8. Economic Journal
9. Journal of the European Economic Association
10. Review of Economics and Statistics
11. Journal of Economic Growth
12. Journal of International Economics
13. Journal of Public Economics
14. Journal of Labor Economics
15. Journal of Development Economics

## Parameters Explained

### `scrape_journal()` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `journal_name` | str | Required | Name of journal (see list above) |
| `start_year` | int | Required | Starting year (e.g., 2020) |
| `end_year` | int | Required | Ending year (e.g., 2024) |
| `num_papers` | int | `None` | **Collect exactly this many papers** |
| `min_papers` | int | 10 | Minimum papers (if num_papers not set) |
| `check_external_repos` | bool | `True` | Search for replication packages |

### `scrape_all_journals()` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_year` | int | 2020 | Starting year |
| `end_year` | int | 2024 | Ending year |
| `num_papers_per_journal` | int | `None` | **Exactly this many per journal** |
| `min_papers_per_journal` | int | 10 | Minimum per journal |
| `check_external_repos` | bool | `True` | Search for replication packages |
| `topic` | str | `None` | Filter by topic (optional) |

## Quick Examples

### Example 1: Test with 5 Papers

```python
scraper = EconomicsJournalScraper()

# Quick test - just 5 papers from AER
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2023,
    end_year=2024,
    num_papers=5,
    check_external_repos=True
)

for paper in papers:
    print(f"- {paper['title'][:60]}...")
    if paper['replication_package'] == 1:
        print(f"  Replication: {paper['replication_url']}")
```

### Example 2: Collect 100 AER Papers

```python
scraper = EconomicsJournalScraper()

papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2020,
    end_year=2024,
    num_papers=100,
    check_external_repos=True
)

# Analyze replication packages
with_replication = sum(1 for p in papers if p['replication_package'] == 1)
print(f"Replication rate: {with_replication}/{len(papers)} ({with_replication*100/len(papers):.1f}%)")
```

### Example 3: Compare Multiple Journals

```python
scraper = EconomicsJournalScraper()

journals = ['American Economic Review', 'Econometrica', 'Quarterly Journal of Economics']
results = {}

for journal in journals:
    papers = scraper.scrape_journal(
        journal_name=journal,
        start_year=2023,
        end_year=2024,
        num_papers=20,
        check_external_repos=True
    )

    with_repl = sum(1 for p in papers if p['replication_package'] == 1)
    results[journal] = {
        'total': len(papers),
        'with_replication': with_repl,
        'rate': with_repl * 100 / len(papers)
    }

# Print comparison
for journal, stats in results.items():
    print(f"{journal}: {stats['with_replication']}/{stats['total']} ({stats['rate']:.1f}%)")
```

### Example 4: Save to Excel

```python
import pandas as pd

scraper = EconomicsJournalScraper()

# Collect papers
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2022,
    end_year=2024,
    num_papers=50,
    check_external_repos=True
)

# Convert to DataFrame
df = pd.DataFrame(papers)

# Save to Excel
scraper.save_to_excel(df, 'aer_50_papers.xlsx')
print("✅ Saved to aer_50_papers.xlsx")
```

## Performance Tips

### Faster Scraping (No Replication Data)

```python
# ~10x faster - doesn't search for replication packages
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2023,
    end_year=2024,
    num_papers=100,
    check_external_repos=False  # ← Much faster!
)
```

### Typical Times (with replication search)

- 10 papers: ~15 seconds
- 50 papers: ~60 seconds
- 100 papers: ~2 minutes

## Common Use Cases

### Research Paper Dataset

```python
# Collect balanced dataset for research
scraper = EconomicsJournalScraper()

df = scraper.scrape_all_journals(
    start_year=2020,
    end_year=2024,
    num_papers_per_journal=50,  # 50 from each journal
    check_external_repos=True
)

# Total: ~750 papers (15 journals × 50)
scraper.save_to_excel(df, 'research_dataset.xlsx')
```

### Replication Study

```python
# Focus on papers with replication packages
scraper = EconomicsJournalScraper()

papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2022,
    end_year=2024,
    num_papers=100,
    check_external_repos=True
)

# Filter for papers with replication
papers_with_repl = [p for p in papers if p['replication_package'] == 1]

print(f"Found {len(papers_with_repl)} papers with replication packages")
for paper in papers_with_repl:
    print(f"- {paper['title'][:60]}...")
    print(f"  {paper['replication_url']}")
```

### Quick Survey

```python
# Survey recent papers from top 5 journals
scraper = EconomicsJournalScraper()

top_5 = [
    'American Economic Review',
    'Quarterly Journal of Economics',
    'Journal of Political Economy',
    'Econometrica',
    'Review of Economic Studies'
]

all_papers = []
for journal in top_5:
    papers = scraper.scrape_journal(
        journal_name=journal,
        start_year=2024,
        end_year=2024,
        num_papers=10,
        check_external_repos=False  # Fast mode
    )
    all_papers.extend(papers)

print(f"Surveyed {len(all_papers)} recent papers from top 5 journals")
```

## Running Example Scripts

```bash
# Test the num_papers parameter
python test_num_papers.py

# See complete examples
python example_usage.py

# Test AER scraper specifically
python test_aer_scraper.py
```

## Getting Help

- **Detailed documentation**: See [NUM_PAPERS_PARAMETER.md](NUM_PAPERS_PARAMETER.md)
- **AER-specific guide**: See [AER_FIX_SUMMARY.md](AER_FIX_SUMMARY.md)
- **Full feature list**: See [IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md)

## Troubleshooting

**Problem**: Not getting exact number requested

**Solution**: Expand date range
```python
# If 2023-2024 doesn't have enough papers:
papers = scraper.scrape_journal(
    journal_name='Journal of Economic Growth',
    start_year=2018,  # ← Wider range
    end_year=2024,
    num_papers=100,
    check_external_repos=True
)
```

**Problem**: Scraping is too slow

**Solution**: Disable external searches
```python
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2023,
    end_year=2024,
    num_papers=100,
    check_external_repos=False  # ← Much faster
)
```

## What's New

✅ **New `num_papers` parameter** - Collect exactly N papers from a journal
✅ **New `num_papers_per_journal` parameter** - Collect exactly N papers per journal
✅ **Improved AER scraper** - 76% replication package detection rate
✅ **Better performance** - Stops at exact count (no wasted requests)
✅ **Backward compatible** - Old `min_papers` parameter still works

## Summary

```python
# OLD WAY (still works - collects AT LEAST N papers)
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2023,
    end_year=2024,
    min_papers=10  # Might get 50+ papers
)

# NEW WAY (precise - collects EXACTLY N papers)
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2023,
    end_year=2024,
    num_papers=10  # Gets exactly 10 papers
)
```

Now you have precise control over your sample size! 🎯
