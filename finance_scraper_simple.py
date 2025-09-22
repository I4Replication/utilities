"""
Simplified Finance Journal Scraper - Focus on CrossRef API
"""

import requests
import pandas as pd
import time
import logging
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import re
from bs4 import BeautifulSoup

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
                      min_papers: int = 10, check_external_repos: bool = True) -> List[Dict]:
        """Scrape papers from a single journal

        Args:
            check_external_repos: If True, search Zenodo and Harvard Dataverse for replication packages
        """
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
                        paper = self._parse_paper(item, journal_name, check_external_repos)
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

    def search_zenodo(self, title: str, authors: str, doi: str = '') -> Optional[str]:
        """Search Zenodo for replication packages using DOI as primary method"""
        try:
            # Strategy 1: Search by DOI (most accurate)
            if doi:
                # Search for datasets related to this DOI
                params = {
                    'q': f'related.identifier:"{doi}" OR "{doi}"',
                    'type': 'dataset',
                    'size': 5
                }

                response = self.session.get('https://zenodo.org/api/records', params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    hits = data.get('hits', {}).get('hits', [])
                    if hits:
                        # Return first match with DOI relation
                        return f"https://zenodo.org/record/{hits[0]['id']}"

            # Strategy 2: Search by title and author (fallback)
            clean_title = re.sub(r'[^\w\s]', ' ', title).strip()
            title_words = [w for w in clean_title.split() if len(w) > 3][:5]
            search_title = ' '.join(title_words)

            query = f'"{search_title}" replication'
            if authors and authors != 'N/A':
                author_parts = authors.split(';')[0].strip().split()
                if author_parts:
                    last_name = author_parts[-1]
                    query = f'"{search_title}" {last_name}'

            params = {
                'q': query,
                'type': 'dataset',
                'size': 3
            }

            response = self.session.get('https://zenodo.org/api/records', params=params, timeout=3)
            if response.status_code == 200:
                data = response.json()
                hits = data.get('hits', {}).get('hits', [])

                # Check if any result is a close match
                title_lower = title.lower()
                for hit in hits:
                    zenodo_title = hit.get('metadata', {}).get('title', '').lower()
                    # Check for replication package indicators
                    if 'replication' in zenodo_title or 'data and code' in zenodo_title:
                        # Verify it's related to our paper
                        title_words_set = set(w for w in title_lower.split() if len(w) > 3)
                        zenodo_words_set = set(w for w in zenodo_title.split() if len(w) > 3)
                        common = len(title_words_set.intersection(zenodo_words_set))
                        if common >= 3:  # At least 3 common words
                            return f"https://zenodo.org/record/{hit['id']}"

        except Exception as e:
            logger.debug(f"Zenodo search error: {e}")

        return None

    def search_harvard_dataverse(self, title: str, doi: str = '', authors: str = '') -> Optional[str]:
        """Search Harvard Dataverse for replication packages using DOI as primary method"""
        try:
            base_url = 'https://dataverse.harvard.edu/api/search'

            # Strategy 1: Search by DOI (most accurate)
            if doi:
                # Search for datasets that reference this DOI
                search_queries = [
                    f'publicationIdValue:"{doi}"',  # Direct DOI reference
                    f'"{doi}"',  # DOI mentioned anywhere
                    f'relatedPublication:"{doi}"'  # Related publication field
                ]

                for query in search_queries:
                    params = {
                        'q': query,
                        'type': 'dataset',
                        'per_page': 5
                    }

                    response = self.session.get(base_url, params=params, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get('data', {}).get('items', [])
                        if items:
                            # Return the first matching dataset
                            global_id = items[0].get('global_id', '')
                            if global_id:
                                if global_id.startswith('doi:'):
                                    return f"https://doi.org/{global_id.replace('doi:', '')}"
                                elif global_id.startswith('hdl:'):
                                    return f"https://hdl.handle.net/{global_id.replace('hdl:', '')}"
                                else:
                                    return f"https://dataverse.harvard.edu/dataset.xhtml?persistentId={global_id}"

            # Strategy 2: Search by title (fallback)
            clean_title = re.sub(r'[^\w\s]', ' ', title).strip()
            title_words = [w for w in clean_title.split() if len(w) > 3][:5]
            search_title = ' '.join(title_words)

            # Search for replication datasets with title keywords
            params = {
                'q': f'("{search_title}") AND (replication OR "replication data" OR "replication package")',
                'type': 'dataset',
                'per_page': 5
            }

            response = self.session.get(base_url, params=params, timeout=3)
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', {}).get('items', [])

                if items:
                    title_lower = title.lower()
                    title_words_set = set(w for w in title_lower.split() if len(w) > 3)

                    for item in items[:3]:
                        item_title = item.get('name', '').lower()
                        item_desc = item.get('description', '').lower()

                        # Check if this is likely a replication package for our paper
                        if 'replication' in item_title or 'replication' in item_desc:
                            item_words = set(w for w in item_title.split() if len(w) > 3)
                            common = len(title_words_set.intersection(item_words))

                            if common >= 3:  # At least 3 common significant words
                                global_id = item.get('global_id', '')
                                if global_id:
                                    if global_id.startswith('doi:'):
                                        return f"https://doi.org/{global_id.replace('doi:', '')}"
                                    elif global_id.startswith('hdl:'):
                                        return f"https://hdl.handle.net/{global_id.replace('hdl:', '')}"
                                    else:
                                        return f"https://dataverse.harvard.edu/dataset.xhtml?persistentId={global_id}"

        except Exception as e:
            logger.debug(f"Harvard Dataverse search error: {e}")

        return None

    def check_journal_supporting_info(self, doi: str, journal: str) -> Optional[str]:
        """Check for supporting information on journal websites"""
        try:
            if not doi:
                return None

            # For Journal of Finance, check Wiley Online Library
            if 'Journal of Finance' in journal:
                # The DOI link often redirects to the Wiley page
                response = self.session.get(f'https://doi.org/{doi}', timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Look for supporting information section
                    # Wiley typically has a section with class 'support-info' or similar
                    support_section = soup.find_all(['a', 'div'], string=re.compile(r'Supporting Information|Supplementary', re.I))
                    if support_section:
                        # Return the main article URL as supporting info is available there
                        return f"https://doi.org/{doi}#support-information-section"

            # For JFE (Elsevier), check ScienceDirect
            elif 'Journal of Financial Economics' in journal:
                response = self.session.get(f'https://doi.org/{doi}', timeout=10, allow_redirects=True)
                if response.status_code == 200 and 'sciencedirect.com' in response.url:
                    # ScienceDirect typically includes supplementary material links
                    soup = BeautifulSoup(response.text, 'html.parser')
                    if soup.find_all(string=re.compile(r'Supplementary|Data in Brief|Research Data', re.I)):
                        return f"{response.url}#supplementary-content"

            # For RFS (Oxford), check Oxford Academic
            elif 'Review of Financial Studies' in journal:
                response = self.session.get(f'https://doi.org/{doi}', timeout=10, allow_redirects=True)
                if response.status_code == 200 and 'academic.oup.com' in response.url:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    if soup.find_all(string=re.compile(r'Supplementary data|Supplementary material', re.I)):
                        return f"{response.url}#supplementary-data"

        except Exception as e:
            logger.debug(f"Journal supporting info check error: {e}")

        return None

    def detect_replication_package(self, title: str, abstract: str, doi: str = '',
                                 journal: str = '', authors: str = '', check_external: bool = True) -> Tuple[int, str]:
        """
        Detect if a paper has a replication package and return its URL
        Returns tuple: (has_package: 0 or 1, package_url: str or empty)

        Args:
            check_external: If True, search external repositories (slower but more thorough)
        """
        # First check abstract/title for direct links
        text = f"{title} {abstract}".lower()

        # Extract URLs from text
        url_pattern = r'https?://[^\s\)\]]+'
        urls = re.findall(url_pattern, text)

        # Check for repository URLs in abstract
        for url in urls:
            if any(repo in url.lower() for repo in ['github.com', 'zenodo.org', 'dataverse.harvard.edu',
                                                    'figshare.com', 'osf.io', 'openicpsr.org']):
                return 1, url

        # Check for replication indicators in text
        replication_indicators = [
            'replication package', 'replication code', 'replication data',
            'supplementary material', 'supplemental material', 'online appendix',
            'data and code', 'github.com/', 'dataverse', 'zenodo', 'osf.io'
        ]

        has_indicators = any(indicator in text for indicator in replication_indicators)

        # For Journal of Finance, almost all recent papers have supporting information
        if 'Journal of Finance' in journal and doi:
            # Most JoF papers from recent years have supporting info at Wiley
            return 1, f"https://doi.org/{doi}#support-information-section"

        # For other finance journals with known patterns
        if doi:
            # JFE (Elsevier) often has supplementary materials
            if 'Journal of Financial Economics' in journal and ('supplement' in text or 'online appendix' in text):
                return 1, f"https://doi.org/{doi}#supplementary-content"

            # RFS (Oxford) often has supplementary data
            if 'Review of Financial Studies' in journal and ('supplement' in text or 'online appendix' in text):
                return 1, f"https://doi.org/{doi}#supplementary-data"

        # Search for replication packages in external repositories (only if enabled)
        if check_external:
            # Try external searches only if there are indicators or for specific journals
            should_search_external = (
                has_indicators or
                'replication' in text or
                'data' in text or
                'code' in text or
                'supplement' in text
            )

            if should_search_external:
                # 1. Search Zenodo (pass DOI for better matching)
                zenodo_url = self.search_zenodo(title, authors, doi)
                if zenodo_url:
                    return 1, zenodo_url

                # 2. Search Harvard Dataverse (DOI is already passed)
                dataverse_url = self.search_harvard_dataverse(title, doi, authors)
                if dataverse_url:
                    return 1, dataverse_url

        # If we found indicators but no specific URL, return generic indicator
        if has_indicators:
            if doi:
                # Return DOI link as fallback
                return 1, f"https://doi.org/{doi}#supplementary"
            return 1, "Available (check paper for details)"

        return 0, ''

    def _parse_paper(self, item: dict, journal_name: str, check_external_repos: bool = True) -> Optional[Dict]:
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

            # Abstract (keep full for classification)
            abstract_full = item.get('abstract', 'N/A')

            # Classify topic based on title and abstract
            topic = self.classify_paper_topic(title, abstract_full if abstract_full != 'N/A' else title)

            # Detect replication package and get URL
            has_replication, replication_url = self.detect_replication_package(
                title,
                abstract_full if abstract_full != 'N/A' else title,
                doi,
                journal_name,
                authors,
                check_external=check_external_repos  # Control external API calls
            )

            return {
                'title': title[:300],  # Limit title length
                'authors': authors[:500],  # Limit authors length
                'journal': journal_name,
                'topic': topic,  # Add classified topic
                'replication_package': has_replication,  # Binary: 1 if has replication, 0 otherwise
                'replication_url': replication_url,  # URL to replication package
                'year': str(year),
                'date': date,
                'doi': doi,
                'link': link
            }

        except Exception as e:
            logger.debug(f"Error parsing paper: {e}")
            return None

    def scrape_all_journals(self, start_year: int = 2020, end_year: int = 2024,
                           topic: Optional[str] = None, min_papers_per_journal: int = 10,
                           check_external_repos: bool = True) -> pd.DataFrame:
        """Scrape all journals"""
        all_papers = []
        journal_counts = defaultdict(int)

        logger.info(f"\n{'='*70}")
        logger.info(f"Starting scrape: {start_year}-{end_year}")
        logger.info(f"Topic filter: {topic if topic else 'ALL TOPICS (no filter)'}")
        logger.info(f"Target: {min_papers_per_journal}+ papers per journal")
        logger.info(f"{'='*70}\n")

        for journal_name in self.journal_issns.keys():
            papers = self.scrape_journal(journal_name, start_year, end_year,
                                        min_papers_per_journal * 2, check_external_repos)

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

                # Log breakdown by source
                if 'replication_url' in df.columns:
                    urls_with_packages = df[df['replication_package'] == 1]['replication_url']
                    zenodo_count = urls_with_packages.str.contains('zenodo', case=False, na=False).sum()
                    dataverse_count = urls_with_packages.str.contains('dataverse', case=False, na=False).sum()
                    journal_count = urls_with_packages.str.contains('#support|#supplement', case=False, na=False).sum()
                    logger.info(f"  Sources: Zenodo: {zenodo_count}, Dataverse: {dataverse_count}, Journal: {journal_count}")

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

                    # Papers with replication packages (separate sheet)
                    if 'replication_url' in df.columns:
                        papers_with_replication = df[df['replication_package'] == 1][['title', 'authors', 'journal', 'year', 'replication_url']]
                        if not papers_with_replication.empty:
                            papers_with_replication.to_excel(writer, sheet_name='Papers with Replication', index=False)

                # Sheet for each journal
                for journal in df['journal'].unique()[:5]:  # Limit to 5 journals for Excel
                    journal_df = df[df['journal'] == journal]
                    sheet_name = journal[:31]  # Excel sheet name limit
                    journal_df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"✅ Results saved to {filename}")


# Main execution
if __name__ == "__main__":
    scraper = SimpleFinanceScraper()

    #Thorough mode - with external searches (smaller sample)
    print("\n" + "="*70)
    print("TEST 2: THOROUGH MODE - Including Zenodo/Dataverse search (2023-2024)")
    print("="*70)

    df_all = scraper.scrape_all_journals(
        start_year=2022,
        end_year=2024,
        topic=None,
        min_papers_per_journal=3,
        check_external_repos=True  # Thorough mode
    )

    if not df_all.empty:
        scraper.save_to_excel(df_all, 'finance_papers_all_topics.xlsx')
        print(f"\n📊 Results: {len(df_all)} total papers")
        if 'journal' in df_all.columns:
            print("\nPapers per journal:")
            print(df_all['journal'].value_counts())


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