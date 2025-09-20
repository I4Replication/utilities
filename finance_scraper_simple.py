"""
Simplified Finance Journal Scraper - Focus on CrossRef API
"""

import requests
import pandas as pd
from datetime import datetime
import time
import logging
from typing import List, Dict, Optional
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleFinanceScraper:
    """Simple scraper focusing on CrossRef API which works reliably"""

    def __init__(self):
        """Initialize with journal mappings"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Academic Research Bot 1.0 (mailto:research@university.edu)',
            'Accept': 'application/json',
        })

        # Journal ISSN mapping for CrossRef
        self.journal_issns = {
            'Journal of Finance': '1540-6261',
            'Journal of Financial Economics': '0304-405X',
            'Review of Financial Studies': '1465-7368',
            'Journal of Financial and Quantitative Analysis': '0022-1090',
            'Review of Finance': '1572-3097'
        }

        # Finance topics keywords
        self.topic_keywords = {
            'corporate_finance': ['capital structure', 'dividend', 'merger', 'acquisition', 'corporate governance',
                                'executive compensation', 'IPO', 'corporate investment'],
            'asset_pricing': ['CAPM', 'factor', 'risk premium', 'anomaly', 'momentum', 'value', 'portfolio'],
            'market_microstructure': ['liquidity', 'market making', 'price discovery', 'trading'],
            'behavioral_finance': ['sentiment', 'behavioral', 'bias', 'psychology'],
            'banking': ['bank', 'lending', 'credit risk', 'financial crisis', 'regulation'],
            'derivatives': ['option', 'futures', 'swap', 'hedging', 'volatility'],
            'international_finance': ['exchange rate', 'currency', 'emerging markets', 'capital flows'],
            'fintech': ['blockchain', 'cryptocurrency', 'bitcoin', 'digital']
        }

    def scrape_journal(self, journal_name: str, start_year: int, end_year: int,
                      min_papers: int = 10) -> List[Dict]:
        """Scrape papers from a single journal"""
        papers = []
        issn = self.journal_issns.get(journal_name)

        if not issn:
            logger.error(f"No ISSN found for {journal_name}")
            return papers

        base_url = 'https://api.crossref.org/works'

        # Calculate how many papers we need per request
        rows_per_request = 50
        offset = 0
        max_requests = 10  # Maximum requests to prevent infinite loops

        logger.info(f"Scraping {journal_name} (ISSN: {issn}) from {start_year} to {end_year}")

        for request_num in range(max_requests):
            params = {
                'filter': f'issn:{issn},from-pub-date:{start_year},until-pub-date:{end_year}',
                'rows': rows_per_request,
                'offset': offset,
                'select': 'title,author,published-print,published-online,DOI,abstract,container-title',
                'sort': 'published',
                'order': 'desc'
            }

            try:
                time.sleep(1)  # Be polite to the API
                response = self.session.get(base_url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    items = data.get('message', {}).get('items', [])
                    total_results = data.get('message', {}).get('total-results', 0)

                    logger.info(f"  Request {request_num + 1}: Got {len(items)} papers (Total available: {total_results})")

                    for item in items:
                        paper = self._parse_paper(item, journal_name)
                        if paper:
                            papers.append(paper)

                    # Check if we have enough papers
                    if len(papers) >= min_papers:
                        logger.info(f"  ✅ Collected {len(papers)} papers for {journal_name}")
                        break

                    # Check if there are more results
                    if len(items) < rows_per_request:
                        break  # No more results

                    offset += rows_per_request

                else:
                    logger.error(f"  API error: {response.status_code}")
                    break

            except Exception as e:
                logger.error(f"  Error fetching data: {e}")
                break

        if len(papers) < min_papers:
            logger.warning(f"  ⚠️  Only found {len(papers)} papers for {journal_name} (target: {min_papers})")

        return papers

    def classify_paper_topic(self, title: str, abstract: str) -> str:
        """Classify a paper into one of the finance topics based on title and abstract"""
        text = f"{title} {abstract}".lower()

        # Score each topic based on keyword matches
        topic_scores = {}

        for topic, keywords in self.topic_keywords.items():
            score = 0
            for keyword in keywords:
                # Count occurrences (weighted by keyword importance)
                keyword_lower = keyword.lower()
                occurrences = text.count(keyword_lower)

                # Give extra weight to certain important keywords
                if keyword_lower in ['ipo', 'merger', 'acquisition', 'capm', 'liquidity',
                                      'blockchain', 'cryptocurrency', 'bank', 'option']:
                    occurrences *= 2

                score += occurrences

            topic_scores[topic] = score

        # Find the topic with the highest score
        if topic_scores:
            best_topic = max(topic_scores, key=topic_scores.get)
            # Only assign if there's at least some match
            if topic_scores[best_topic] > 0:
                return best_topic

        # Default to 'general_finance' if no strong match
        return 'general_finance'

    def detect_replication_package(self, title: str, abstract: str, doi: str = '') -> int:
        """
        Detect if a paper has a replication package
        Returns 1 if replication package indicators found, 0 otherwise
        """
        # Combine text for searching
        text = f"{title} {abstract}".lower()

        # Keywords that indicate replication package availability
        replication_indicators = [
            'replication package',
            'replication code',
            'replication data',
            'replication files',
            'supplementary material',
            'supplemental material',
            'online appendix',
            'data and code',
            'code availability',
            'data availability',
            'github.com',
            'dataverse',
            'figshare',
            'zenodo',
            'osf.io',
            'openicpsr',
            'replication materials',
            'reproduction package',
            'reproducible',
            'available upon request',
            'available from the author',
            'companion website',
            'supplementary data'
        ]

        # Check for replication indicators
        for indicator in replication_indicators:
            if indicator in text:
                return 1

        # Check DOI - some journals have standard supplementary material patterns
        if doi:
            # JFE often has supplementary materials
            if 'jfineco' in doi.lower() and 'supplementary' in text:
                return 1

        # Check for specific patterns
        import re

        # Pattern for URLs to code repositories
        if re.search(r'(github|gitlab|bitbucket|dataverse|figshare|zenodo|osf)', text):
            return 1

        # Pattern for "data/code available at..."
        if re.search(r'(data|code|replication).{0,20}available.{0,20}(at|from|on)', text):
            return 1

        # No indicators found
        return 0

    def _parse_paper(self, item: dict, journal_name: str) -> Optional[Dict]:
        """Parse a single paper from CrossRef response"""
        try:
            # Title
            title = ' '.join(item.get('title', ['N/A']))
            if title == 'N/A':
                return None

            # Authors
            authors_list = item.get('author', [])
            if authors_list:
                authors = '; '.join([
                    f"{author.get('given', '')} {author.get('family', '')}".strip()
                    for author in authors_list[:10]  # Limit to first 10 authors
                ])
            else:
                authors = 'N/A'

            # Date
            pub_date = item.get('published-print', item.get('published-online'))
            if pub_date and 'date-parts' in pub_date and pub_date['date-parts']:
                date_parts = pub_date['date-parts'][0]
                year = date_parts[0] if date_parts else 'N/A'
                month = date_parts[1] if len(date_parts) > 1 else 1
                day = date_parts[2] if len(date_parts) > 2 else 1
                date = f"{year}-{month:02d}-{day:02d}"
            else:
                date = 'N/A'
                year = 'N/A'

            # DOI and link
            doi = item.get('DOI', '')
            link = f"https://doi.org/{doi}" if doi else 'N/A'

            # Abstract (keep full for classification, but store limited version)
            abstract_full = item.get('abstract', 'N/A')
            abstract = abstract_full[:500] + '...' if abstract_full != 'N/A' and len(abstract_full) > 500 else abstract_full

            # Classify topic based on title and abstract
            topic = self.classify_paper_topic(title, abstract_full if abstract_full != 'N/A' else title)

            # Detect replication package (1 if present, 0 otherwise)
            replication_package = self.detect_replication_package(
                title,
                abstract_full if abstract_full != 'N/A' else title,
                doi
            )

            return {
                'title': title[:300],  # Limit title length
                'authors': authors[:500],  # Limit authors length
                'journal': journal_name,
                'topic': topic,  # Add classified topic
                'replication_package': replication_package,  # Binary: 1 if has replication, 0 otherwise
                'year': str(year),
                'date': date,
                'doi': doi,
                'link': link,
                'abstract': abstract
            }

        except Exception as e:
            logger.debug(f"Error parsing paper: {e}")
            return None

    def scrape_all_journals(self, start_year: int = 2020, end_year: int = 2024,
                           topic: Optional[str] = None, min_papers_per_journal: int = 10) -> pd.DataFrame:
        """Scrape all journals"""
        all_papers = []
        journal_counts = defaultdict(int)

        logger.info(f"\n{'='*70}")
        logger.info(f"Starting scrape: {start_year}-{end_year}")
        logger.info(f"Topic filter: {topic if topic else 'ALL TOPICS (no filter)'}")
        logger.info(f"Target: {min_papers_per_journal}+ papers per journal")
        logger.info(f"{'='*70}\n")

        for journal_name in self.journal_issns.keys():
            papers = self.scrape_journal(journal_name, start_year, end_year, min_papers_per_journal * 2)

            # Apply topic filter if specified
            # Since papers now have topics pre-classified, just filter by the topic field
            if topic and topic in self.topic_keywords:
                filtered_papers = [p for p in papers if p.get('topic') == topic]
                logger.info(f"  After topic filter: {len(filtered_papers)} papers (from {len(papers)} total)")
                papers = filtered_papers

            all_papers.extend(papers)
            journal_counts[journal_name] = len(papers)

        # Summary
        logger.info(f"\n{'='*70}")
        logger.info("FINAL SUMMARY")
        logger.info(f"{'='*70}")

        success_count = 0
        for journal, count in journal_counts.items():
            if count >= min_papers_per_journal:
                logger.info(f"✅ {journal}: {count} papers")
                success_count += 1
            else:
                logger.info(f"❌ {journal}: {count} papers (need {min_papers_per_journal})")

        logger.info(f"\nSuccess rate: {success_count}/{len(self.journal_issns)} journals")
        logger.info(f"Total papers: {len(all_papers)}")

        # Convert to DataFrame
        df = pd.DataFrame(all_papers)

        # Sort by journal and year
        if not df.empty and 'journal' in df.columns:
            df = df.sort_values(['journal', 'year', 'date'], ascending=[True, False, False])

            # Log topic distribution
            if 'topic' in df.columns:
                logger.info(f"\nTopic Distribution:")
                topic_counts = df['topic'].value_counts()
                for topic, count in topic_counts.items():
                    logger.info(f"  {topic}: {count} papers")

            # Log replication package statistics
            if 'replication_package' in df.columns:
                replication_count = df['replication_package'].sum()
                replication_pct = (replication_count / len(df)) * 100
                logger.info(f"\nReplication Package Availability:")
                logger.info(f"  Papers with replication: {replication_count}/{len(df)} ({replication_pct:.1f}%)")

        return df

    def save_to_excel(self, df: pd.DataFrame, filename: str):
        """Save results to Excel file"""
        if df.empty:
            logger.warning("No data to save")
            return

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # All papers
            df.to_excel(writer, sheet_name='All Papers', index=False)

            # Summary by journal
            if 'journal' in df.columns:
                summary = df['journal'].value_counts().to_frame()
                summary.columns = ['Paper Count']
                summary.to_excel(writer, sheet_name='Summary by Journal')

                # Topic summary
                if 'topic' in df.columns:
                    topic_summary = df['topic'].value_counts().to_frame()
                    topic_summary.columns = ['Paper Count']
                    topic_summary.to_excel(writer, sheet_name='Summary by Topic')

                    # Cross-tabulation: journals vs topics
                    cross_tab = pd.crosstab(df['journal'], df['topic'], margins=True)
                    cross_tab.to_excel(writer, sheet_name='Journal-Topic Matrix')

                # Replication package summary
                if 'replication_package' in df.columns:
                    # Summary by journal
                    replication_by_journal = df.groupby('journal')['replication_package'].agg(['sum', 'count', 'mean'])
                    replication_by_journal.columns = ['Has Replication', 'Total Papers', 'Replication Rate']
                    replication_by_journal['Replication Rate'] = (replication_by_journal['Replication Rate'] * 100).round(1)
                    replication_by_journal.to_excel(writer, sheet_name='Replication by Journal')

                    # Summary by topic if topics exist
                    if 'topic' in df.columns:
                        replication_by_topic = df.groupby('topic')['replication_package'].agg(['sum', 'count', 'mean'])
                        replication_by_topic.columns = ['Has Replication', 'Total Papers', 'Replication Rate']
                        replication_by_topic['Replication Rate'] = (replication_by_topic['Replication Rate'] * 100).round(1)
                        replication_by_topic.to_excel(writer, sheet_name='Replication by Topic')

                # Sheet for each journal
                for journal in df['journal'].unique()[:5]:  # Limit to 5 journals for Excel
                    journal_df = df[df['journal'] == journal]
                    sheet_name = journal[:31]  # Excel sheet name limit
                    journal_df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"✅ Results saved to {filename}")


# Main execution
if __name__ == "__main__":
    scraper = SimpleFinanceScraper()

    # Test 1: All topics (no filter) for 4 years
    print("\n" + "="*70)
    print("TEST 1: All topics from 2020-2024")
    print("="*70)

    df_all = scraper.scrape_all_journals(
        start_year=2020,
        end_year=2024,
        topic=None,  # No topic filter = all papers
        min_papers_per_journal=10
    )

    if not df_all.empty:
        scraper.save_to_excel(df_all, 'finance_papers_2020_2024_all_topics.xlsx')
        print(f"\n📊 Results: {len(df_all)} total papers")
        if 'journal' in df_all.columns:
            print("\nPapers per journal:")
            print(df_all['journal'].value_counts())

    # Test 2: Specific topic
    print("\n" + "="*70)
    print("TEST 2: Asset pricing papers from 2020-2024")
    print("="*70)

    df_asset = scraper.scrape_all_journals(
        start_year=2020,
        end_year=2024,
        topic='asset_pricing',
        min_papers_per_journal=10
    )

    if not df_asset.empty:
        scraper.save_to_excel(df_asset, 'finance_papers_2020_2024_asset_pricing.xlsx')
        print(f"\n📊 Asset pricing papers: {len(df_asset)}")

    # Print sample papers
    if not df_all.empty:
        print("\n" + "="*70)
        print("SAMPLE PAPERS FROM EACH JOURNAL")
        print("="*70)

        for journal in df_all['journal'].unique()[:5]:
            print(f"\n{journal}:")
            journal_papers = df_all[df_all['journal'] == journal]
            for _, paper in journal_papers.head(2).iterrows():
                print(f"  • {paper['title'][:80]}...")
                print(f"    Year: {paper['year']}, Authors: {paper['authors'][:50]}...")