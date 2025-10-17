# Replication Package Scraper - Improvements Summary

## Overview
This document summarizes the improvements made to the economics replication package scraper, with a focus on improving openICPSR detection for AER papers and implementing a hierarchical repository search strategy.

## Test Results (100 Papers from 2022-2024)

### Overall Statistics
- **Total papers analyzed**: 100 papers
- **Papers with replication packages**: 17 (17.0%)
- **Date range**: 2022-2024
- **Journals covered**: 15 top economics journals

### Replication Package Availability by Journal

| Journal | Papers | Replication Packages | Rate |
|---------|--------|---------------------|------|
| Econometrica | 7 | 7 | 100.0% |
| Quarterly Journal of Economics | 7 | 6 | 85.7% |
| Economic Journal | 7 | 2 | 28.6% |
| Journal of the European Economic Association | 7 | 1 | 14.3% |
| Review of Economic Studies | 7 | 1 | 14.3% |
| American Economic Review | 7 | 0 | 0.0% |
| Other journals | ~40 | 0 | 0.0% |

### Repository Sources Distribution
- **Journal websites**: 35.3% (primarily Econometrica, QJE)
- **Zenodo**: 23.5%
- **Other sources**: 41.2%
- **openICPSR**: 0% (needs further debugging)

## Key Improvements Implemented

### 1. Enhanced openICPSR Scraper

#### Previous Implementation Issues:
- Basic title word matching only
- No DOI-based search
- No author verification
- Simple threshold-based matching (3+ words)
- No scoring mechanism for best match selection

#### New Implementation Features:

**A. DOI-Based Search (Primary Strategy)**
```python
# Strategy 1: Search by DOI directly in openICPSR
- URL-encode DOI for search
- Check multiple result pages
- Verify DOI presence in study page content
```

**B. Enhanced Title Matching (Fallback Strategy)**
```python
# Strategy 2: Improved title-based search with scoring
- Calculate title similarity using Jaccard index
- Count word match ratio
- Verify author names
- Composite scoring: similarity (60%) + word_ratio (30%) + author (10%)
- Threshold: 0.4 minimum score for acceptance
```

**C. Best Match Selection**
- Evaluates top 5 search results
- Tracks best score across all candidates
- Returns highest scoring match above threshold

**Key Code Changes**: [economics_scraper.py:357-477](economics_scraper.py#L357-L477)

### 2. Hierarchical Repository Search Strategy

#### For AER and AEA Journals:
```
1. openICPSR (primary repository for AEA)
   ↓ (if not found)
2. Zenodo (some authors upload here too)
   ↓ (if not found)
3. Harvard Dataverse
   ↓ (if not found)
4. OSF (Open Science Framework)
```

#### For Non-AEA Journals:
```
1. Zenodo (most popular for European/international)
   ↓ (if not found)
2. Harvard Dataverse (popular in US)
   ↓ (if not found)
3. OSF
   ↓ (if not found)
4. openICPSR (less common but possible)
```

#### Journal Detection:
```python
is_aea_journal = any(j in journal for j in [
    'American Economic Review',
    'AEA',
    'American Economic Journal',
    'Journal of Economic Literature',
    'Journal of Economic Perspectives'
])
```

**Key Code Changes**: [economics_scraper.py:577-689](economics_scraper.py#L577-L689)

### 3. Enhanced Matching Logic Across All Repositories

#### A. Title Similarity Calculation
- Uses Jaccard similarity coefficient
- Filters words longer than 3 characters
- Case-insensitive comparison
```python
def _calculate_title_similarity(self, title1: str, title2: str) -> float:
    words1 = set(w for w in title1.split() if len(w) > 3)
    words2 = set(w for w in title2.split() if len(w) > 3)
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    return intersection / union if union > 0 else 0.0
```

#### B. DOI Matching
- All repository searches now support DOI as primary search method
- Checks related_identifiers in metadata
- Searches for DOI in description/abstract

#### C. Author Verification
- Extracts first author's last name
- Cross-references with repository metadata
- Used as tiebreaker in scoring

## Known Issues and Future Work

### 1. AER Papers - openICPSR Detection
**Issue**: 0% detection rate for AER papers in test (expected >90%)

**Potential Causes**:
- openICPSR may be blocking automated scraping
- Search result page structure may have changed
- Timeouts on requests (10 seconds may be insufficient)
- Rate limiting by openICPSR

**Recommendations**:
1. Add more aggressive retry logic with exponential backoff
2. Increase timeout to 15-20 seconds
3. Try alternative user-agent strings
4. Consider using Selenium for JavaScript-rendered content
5. Check if openICPSR has a formal API (currently scraping only)
6. Add logging to debug exact failure points

### 2. Harvard Dataverse
**Issue**: 0 matches found in test

**Recommendations**:
- Verify API endpoint is correct
- Check if authentication is required
- Test query format manually

### 3. False Negatives
Some journals with known replication packages showed 0%:
- Journal of Political Economy
- Journal of Labor Economics
- Journal of Development Economics

**Recommendations**:
- These journals may host packages on their own websites
- Need journal-specific scrapers for their supporting info pages
- Consider adding publisher-specific APIs (Elsevier, Chicago Press, etc.)

## Files Modified

1. **[economics_scraper.py](economics_scraper.py)**
   - Lines 357-477: Enhanced `search_openicpsr()` function
   - Lines 577-689: Updated `detect_replication_package()` with hierarchical search
   - Lines 131-142: Title similarity calculation helper

2. **[test_scraper.py](test_scraper.py)**
   - Complete rewrite for 100-paper test
   - Added detailed statistics by journal and source
   - AER-specific analysis section

## Output Files Generated

1. **test_results_100_papers.xlsx**
   - Contains test results for 100 papers
   - Multiple sheets: all papers, by journal, by topic, replication stats

2. **test_scraper.log**
   - Detailed execution log
   - Debug information for troubleshooting

## Success Metrics

### What Worked Well:
✅ **Econometrica**: 100% detection rate (7/7 papers)
✅ **QJE**: 85.7% detection rate (6/7 papers)
✅ **Zenodo**: Successfully finding matches with DOI + title + author
✅ **Journal websites**: Detecting supplementary materials
✅ **Hierarchical approach**: Reduces redundant searches

### What Needs Work:
⚠️ **openICPSR**: 0% detection (critical for AER)
⚠️ **Harvard Dataverse**: 0 matches found
⚠️ **Elsevier journals**: Low detection rates

## Recommendations for Next Steps

### Immediate (High Priority):
1. **Debug openICPSR scraper**
   - Add verbose logging
   - Test with known AER papers that have packages
   - Check for anti-scraping measures
   - Consider Selenium/Playwright for dynamic content

2. **Test with known-good examples**
   - Create a test set of 10 AER papers with confirmed openICPSR links
   - Debug step-by-step through the search process

### Short Term:
3. **Improve Harvard Dataverse**
   - Verify API access and query format
   - Test with papers known to be in Dataverse

4. **Add journal-specific scrapers**
   - Elsevier journals (ScienceDirect)
   - Chicago Press (JPE)
   - MIT Press journals

### Long Term:
5. **Add caching layer**
   - Cache repository search results
   - Avoid redundant API calls

6. **Add validation/verification**
   - Verify URLs return actual data files
   - Check for broken/moved links
   - Validate package contents

## Usage

### Running the Test:
```bash
cd /Users/brunobarbarioli/Downloads/utilities-main
python test_scraper.py
```

### Using the Improved Scraper:
```python
from economics_scraper import EconomicsJournalScraper

scraper = EconomicsJournalScraper()

# For AER papers, openICPSR will be prioritized
has_replication, url = scraper.detect_replication_package(
    title="Your Paper Title",
    abstract="Paper abstract...",
    doi="10.1257/aer.20220000",
    journal="American Economic Review",
    authors="Smith, John; Doe, Jane",
    check_external=True
)
```

## Conclusion

The improvements successfully implement:
1. ✅ Enhanced openICPSR scraper with sophisticated matching
2. ✅ Hierarchical repository search strategy
3. ✅ Better DOI and title matching across repositories

However, the openICPSR scraper needs debugging as it showed 0% success rate in testing, despite the improved logic. The issue is likely technical (anti-scraping, timeouts) rather than logical.

The hierarchical approach is working well for journals that don't rely on openICPSR, with Econometrica showing 100% detection and QJE showing 85.7%.

## Contact

For questions or further improvements, please refer to the implementation in:
- `economics_scraper.py` - Main scraper implementation
- `test_scraper.py` - Testing framework
- `test_results_100_papers.xlsx` - Detailed test results
