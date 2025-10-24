# Institute for Replication - Journal Scrapers

Tools for scraping academic papers from top journals and detecting replication packages.

---

## 📦 Installation

```bash
git clone https://github.com/I4Replication/utilities.git
cd utilities
pip install -r requirements.txt
```

---

## 🔧 Available Tools

### Economics Journal Scraper

Scrapes papers from 15 top economics journals and finds replication packages.

**Supported Journals:**
- American Economic Review
- Quarterly Journal of Economics
- Journal of Political Economy
- Econometrica
- Review of Economic Studies
- Journal of Economic Theory
- Journal of Monetary Economics
- Economic Journal
- Journal of the European Economic Association
- Review of Economics and Statistics
- Journal of Economic Growth
- Journal of International Economics
- Journal of Public Economics
- Journal of Labor Economics
- Journal of Development Economics

**Basic Usage:**

```python
from economics_scraper import EconomicsJournalScraper

scraper = EconomicsJournalScraper()

# Scrape 20 papers per journal
df = scraper.scrape_all_journals(
    start_year=2022,
    end_year=2025,
    num_papers_per_journal=20,
    check_external_repos=True
)

# Save to Excel
scraper.save_to_excel(df, 'economics_papers.xlsx')

# Check replication packages
print(f"Total papers: {len(df)}")
print(f"With replication: {df['replication_package'].sum()}")
```

**Where it searches for replication packages:**
- openICPSR (for AER and AEA journals)
- Zenodo
- Harvard Dataverse
- Open Science Framework (OSF)
- Journal supplementary materials pages

---

### Psychology Journal Scraper

Scrapes papers from 10 top psychology journals and finds replication packages.

**Supported Journals:**
- Psychological Bulletin
- Psychological Review
- Annual Review of Psychology
- Journal of Experimental Psychology: General
- Psychological Science
- Journal of Personality and Social Psychology
- Personality and Social Psychology Review
- Psychological Science in the Public Interest
- Development and Psychopathology
- Perspectives on Psychological Science

**Basic Usage:**

```python
from psychology_scraper import PsychologyJournalScraper

scraper = PsychologyJournalScraper()

# Scrape 20 papers per journal
df = scraper.scrape_all_journals(
    start_year=2022,
    end_year=2025,
    num_papers_per_journal=20,
    check_external_repos=True
)

# Save to Excel
scraper.save_to_excel(df, 'psychology_papers.xlsx')

# Check replication packages
print(f"Total papers: {len(df)}")
print(f"With replication: {df['replication_package'].sum()}")
```

**Where it searches for replication packages:**
- Open Science Framework (OSF) - most popular in psychology
- Zenodo
- Harvard Dataverse
- PsychArchives
- ResearchBox
- AsPredicted
- Journal supplementary materials pages

---

## 📊 Output Format

Both scrapers save data to Excel with multiple sheets:

**Main Data:**
- Title, authors, journal, year, DOI
- Topic classification (automatically detected)
- Replication package status (0 or 1)
- Replication package URL (if found)

**Summary Sheets:**
- Papers by journal
- Papers by topic
- Replication package rates by journal
- Replication package rates by topic
- Papers with replication packages (separate list)

---

## ⚡ Common Options

### Control Number of Papers

```python
# Get exactly 50 papers per journal
df = scraper.scrape_all_journals(
    start_year=2022,
    end_year=2025,
    num_papers_per_journal=50
)

# Get at least 100 papers per journal (may get more)
df = scraper.scrape_all_journals(
    start_year=2022,
    end_year=2025,
    min_papers_per_journal=100
)
```

### Fast Mode (Skip Replication Search)

Skip external repository searches for 10x faster scraping:

```python
df = scraper.scrape_all_journals(
    start_year=2023,
    end_year=2024,
    num_papers_per_journal=100,
    check_external_repos=False  # 10x faster
)
```

### Single Journal

```python
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2023,
    end_year=2024,
    num_papers=50
)
```

### Filter by Topic

```python
# Economics topics: 'macroeconomics', 'microeconomics', 'labor_economics',
# 'public_economics', 'international_economics', 'development_economics',
# 'econometrics', 'behavioral_economics', 'environmental_economics',
# 'health_economics', 'urban_economics', 'political_economy'

df = scraper.scrape_all_journals(
    start_year=2022,
    end_year=2024,
    topic='labor_economics',
    num_papers_per_journal=20
)
```

```python
# Psychology topics: 'cognitive_psychology', 'social_psychology',
# 'developmental_psychology', 'clinical_psychology', 'neuroscience_psychology',
# 'personality_psychology', 'emotion_motivation', 'methodology_statistics',
# 'health_psychology', 'educational_psychology', 'industrial_organizational',
# 'evolutionary_psychology'

df = scraper.scrape_all_journals(
    start_year=2022,
    end_year=2024,
    topic='social_psychology',
    num_papers_per_journal=20
)
```

---

## 🎯 Performance

**Speed:**
- ~1-2 seconds per paper with replication search
- ~0.1 seconds per paper without replication search

**Accuracy:**
- Economics: 22% average replication detection (100% for Econometrica, 72% for AER)
- Psychology: Varies by journal and year

---

## ⚠️ Important Notes

- Includes automatic rate limiting (1 second between requests)
- Respects API terms of service
- For research purposes only
- Some journals may require institutional access for full text

---

## 📧 Contact

**Institute for Replication**
- Website: [https://i4replication.org](https://i4replication.org)
- GitHub: [@I4Replication](https://github.com/I4Replication)

---

## ⚖️ License

MIT License - see LICENSE file for details.

---

**Last Updated**: October 2025
