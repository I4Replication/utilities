# Institute for Replication - Utilities

A collection of reusable utilities, scripts, and helpers developed at Institute for Replication to support internal workflows, automation, and data processing.

---

## 🚀 Features

- **Automation Scripts**: Tools to streamline recurring tasks
- **Data Utilities**: Functions for cleaning, transforming, and validating data
- **Integration Helpers**: Wrappers for APIs, databases, and third-party services
- **Developer Productivity**: Shortcuts and CLI tools to speed up day-to-day development

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/I4Replication/utilities.git
cd utilities
```

Install requirements:

```bash
pip install -r requirements.txt
```

---

## 📚 Available Tools

### 1. Economics Journal Scraper

A powerful tool for scraping papers from top economics journals and detecting replication packages.

**Features:**
- 🎯 Scrape from 15 top economics journals (AER, QJE, JPE, Econometrica, etc.)
- 📦 Automatic replication package detection (22.2% average across all journals, up to 100% for Econometrica)
- 🔍 Multi-repository search (openICPSR, Zenodo, Harvard Dataverse, OSF)
- 📊 Export to Excel with detailed metadata
- ⚡ Fast and efficient with configurable sample sizes

**Quick Start:**

```python
from economics_scraper import EconomicsJournalScraper

scraper = EconomicsJournalScraper()

# Scrape 100 papers per journal from all top journals
df = scraper.scrape_all_journals(
    start_year=2022,
    end_year=2025,
    min_papers_per_journal=100,
    check_external_repos=True
)

print(f"Collected {len(df)} papers from {df['journal'].nunique()} journals")

# Check replication package availability
with_replication = df['replication_package'].sum()
print(f"Papers with replication: {with_replication}/{len(df)} ({with_replication*100/len(df):.1f}%)")

# Show breakdown by journal
print("\nBy journal:")
for journal in df['journal'].unique():
    journal_df = df[df['journal'] == journal]
    repl = journal_df['replication_package'].sum()
    total = len(journal_df)
    print(f"  {journal}: {repl}/{total} ({repl*100/total:.1f}%)")
```

**Supported Journals:**

| Journal | ISSN |
|---------|------|
| American Economic Review | 0002-8282 |
| Quarterly Journal of Economics | 0033-5533 |
| Journal of Political Economy | 0022-3808 |
| Econometrica | 0012-9682 |
| Review of Economic Studies | 0034-6527 |
| Journal of Economic Theory | 0022-0531 |
| Journal of Monetary Economics | 0304-3932 |
| Economic Journal | 0013-0133 |
| Journal of the European Economic Association | 1542-4766 |
| Review of Economics and Statistics | 0034-6535 |
| Journal of Economic Growth | 1381-4338 |
| Journal of International Economics | 0022-1996 |
| Journal of Public Economics | 0047-2727 |
| Journal of Labor Economics | 0734-306X |
| Journal of Development Economics | 0304-3878 |

**Documentation:**
- [Quick Start Guide](QUICK_START.md) - Get started quickly
- [Detailed API Reference](NUM_PAPERS_PARAMETER.md) - Complete parameter documentation
- [AER-Specific Guide](AER_FIX_SUMMARY.md) - American Economic Review implementation details
- [Examples](example_usage.py) - Working code examples

**Example Use Cases:**

1. **Research Dataset Collection:**
```python
# Collect balanced dataset for research
df = scraper.scrape_all_journals(
    start_year=2020,
    end_year=2024,
    num_papers_per_journal=50,
    check_external_repos=True
)
scraper.save_to_excel(df, 'research_dataset.xlsx')
```

2. **Replication Package Analysis:**
```python
# Analyze replication package availability across all journals
df = scraper.scrape_all_journals(
    start_year=2022,
    end_year=2025,
    min_papers_per_journal=100,
    check_external_repos=True
)

# Analyze by journal
repl_by_journal = df.groupby('journal')['replication_package'].agg(['sum', 'count'])
repl_by_journal['rate'] = (repl_by_journal['sum'] / repl_by_journal['count'] * 100).round(1)
print(repl_by_journal.sort_values('rate', ascending=False))
```

3. **Fast Metadata Collection:**
```python
# Collect metadata only (no replication search - 10x faster)
papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2023,
    end_year=2024,
    num_papers=100,
    check_external_repos=False
)
```

**Testing:**

```bash
# Test AER scraper
python test_aer_scraper.py

# Test num_papers parameter
python test_num_papers.py

# Run examples
python example_usage.py
```

---

## 📖 Additional Documentation

### Economics Scraper

- [QUICK_START.md](QUICK_START.md) - Quick reference guide
- [NUM_PAPERS_PARAMETER.md](NUM_PAPERS_PARAMETER.md) - Detailed guide on collecting specific numbers of papers
- [AER_FIX_SUMMARY.md](AER_FIX_SUMMARY.md) - Technical details on AER implementation
- [IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md) - Complete changelog and feature list

### Test Files

- `test_aer_scraper.py` - Test AER-specific functionality
- `test_num_papers.py` - Test num_papers parameter
- `example_usage.py` - Complete working examples

---

## 🔧 Technical Details

### Economics Scraper Architecture

The scraper uses a hierarchical search strategy to find replication packages:

**For AER/AEA Journals:**
1. Check AER paper page directly (72.5% success rate for AER)
2. Search openICPSR
3. Fallback to Zenodo
4. Search Harvard Dataverse
5. Search OSF

**For Other Journals:**
1. Search Zenodo (most common)
2. Search Harvard Dataverse
3. Search OSF
4. Check journal supplementary materials
5. Search openICPSR

### Performance Characteristics

- **API Rate Limiting**: Includes 1-second delays between CrossRef requests
- **Timeout Handling**: 15-second timeout for AER pages, 10 seconds for others
- **Error Handling**: Gracefully handles 403 errors, network timeouts, and missing data
- **Caching**: No caching (can be added if needed)

### Data Sources

- **Paper Metadata**: CrossRef API
- **Replication Packages**:
  - openICPSR (AEA journals) - via DOI 10.3886/E######
  - Zenodo - via Zenodo API
  - Harvard Dataverse - via Dataverse API
  - Open Science Framework - via OSF API
  - Journal websites - via web scraping

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Reporting Issues

If you encounter a bug or have a feature request:

1. Check if the issue already exists in [Issues](https://github.com/I4Replication/utilities/issues)
2. If not, create a new issue with:
   - Clear description of the problem/feature
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Your environment (Python version, OS, etc.)

### Contributing Code

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include type hints where appropriate
- Write descriptive commit messages
- Test your changes thoroughly

---

## 📊 Performance Benchmarks

### Economics Scraper

Tested on 2,855 papers from 15 top journals (2022-2025):

| Metric | Result |
|--------|--------|
| **Overall Detection Rate** | 22.2% (635/2,855 papers) |
| **Best Performing Journals** | Econometrica: 100%, QJE: 89.6%, AER: 72.5% |
| **Total Papers Scraped** | 2,855 papers |
| **Average Time** | ~1.5 seconds per paper |

**Replication Package Availability by Journal:**

| Journal | Papers | With Replication | Rate |
|---------|--------|-----------------|------|
| Econometrica | 200 | 200 | 100.0% |
| Quarterly Journal of Economics | 193 | 173 | 89.6% |
| American Economic Review | 200 | 145 | 72.5% |
| Economic Journal | 200 | 54 | 27.0% |
| Review of Economic Studies | 200 | 41 | 20.5% |
| Journal of the European Economic Association | 200 | 16 | 8.0% |
| Journal of Political Economy | 200 | 4 | 2.0% |
| Review of Economics and Statistics | 200 | 1 | 0.5% |
| Journal of Development Economics | 200 | 1 | 0.5% |
| Other Journals (6) | 1,062 | 0 | 0.0% |

**Replication Package Sources:**

The scraper successfully identified replication packages from multiple sources including journal websites, Zenodo (115 packages), and other repositories.

### Typical Usage Times

| Task | Papers | Time |
|------|--------|------|
| Single journal | 50 | ~75 seconds |
| Single journal | 100 | ~2.5 minutes |
| Single journal | 200 | ~5 minutes |
| All journals | 100 each | ~30 minutes |
| All journals (full dataset) | 2,855 total | ~1.2 hours |

*Times include replication package searches. Disable `check_external_repos` for 10x speedup.*

---

## ⚖️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📧 Contact

**Institute for Replication**

- Website: [https://i4replication.org](https://i4replication.org)
- GitHub: [@I4Replication](https://github.com/I4Replication)
- Issues: [GitHub Issues](https://github.com/I4Replication/utilities/issues)

---

## 🙏 Acknowledgments

### Economics Scraper

- **Data Sources**: CrossRef API, openICPSR, Zenodo, Harvard Dataverse, OSF
- **Journals**: American Economic Association and other publishers
- **Inspiration**: Research on replication in economics

### Contributors

Thank you to all contributors who have helped improve these tools!

---

## ⚠️ Disclaimer

These tools are for research purposes only. Please respect the terms of service of the APIs and websites accessed by these tools. The scrapers include appropriate delays and rate limiting to be respectful of server resources.

---

## 📈 Changelog

### Version 2.0 (October 2025)

**Economics Scraper:**
- ✅ Added `num_papers` parameter for exact paper counts
- ✅ Comprehensive testing on 2,855 papers from 15 journals
- ✅ Achieved 100% detection rate for Econometrica, 89.6% for QJE, 72.5% for AER
- ✅ Overall detection rate of 22.2% across all journals
- ✅ Improved openICPSR detection
- ✅ Added hierarchical repository search (Zenodo, Dataverse, OSF, journal websites)
- ✅ Enhanced title matching with Jaccard similarity
- ✅ Better error handling for 403 errors
- ✅ Comprehensive documentation

### Version 1.0

- Initial release of economics journal scraper
- Support for 15 top journals
- Basic replication package detection

---

**Made with ❤️ by the Institute for Replication team**

*Supporting reproducible research in economics and social sciences*

---

**Last Updated**: October 2025
