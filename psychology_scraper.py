"""
Psychology Journal Scraper - Top 10 Psychology Journals
Based on journal impact factors and field relevance
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

class PsychologyJournalScraper:
    """Scraper for top psychology journals using CrossRef API"""

    def __init__(self):
        """Initialize with journal mappings for top 10 psychology journals"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

        # Top 10 Psychology Journals with their ISSNs
        self.journal_issns = {
            # Top Tier General Psychology
            'Psychological Bulletin': '0033-2909',
            'Psychological Review': '0033-295X',
            'Annual Review of Psychology': '0066-4308',

            # Top Cognitive/Experimental Psychology
            'Journal of Experimental Psychology: General': '0096-3445',
            'Psychological Science': '0956-7976',

            # Top Social/Personality Psychology
            'Journal of Personality and Social Psychology': '0022-3514',
            'Personality and Social Psychology Review': '1088-8683',

            # Top Clinical/Developmental Psychology
            'Psychological Science in the Public Interest': '1529-1006',
            'Development and Psychopathology': '0954-5794',

            # Top Applied/Methods
            'Perspectives on Psychological Science': '1745-6916'
        }

        # Psychology topic keywords
        self.topic_keywords = {
            'cognitive_psychology': ['attention', 'memory', 'perception', 'cognition', 'cognitive',
                                    'working memory', 'executive function', 'decision making',
                                    'reasoning', 'problem solving', 'learning', 'language processing'],
            'social_psychology': ['social', 'attitudes', 'prejudice', 'stereotypes', 'conformity',
                                 'group behavior', 'social influence', 'persuasion', 'aggression',
                                 'prosocial', 'intergroup', 'social cognition', 'attribution'],
            'developmental_psychology': ['development', 'developmental', 'children', 'childhood',
                                        'adolescence', 'infancy', 'aging', 'lifespan', 'infant',
                                        'toddler', 'attachment', 'parenting', 'maturation'],
            'clinical_psychology': ['depression', 'anxiety', 'psychotherapy', 'treatment',
                                   'mental health', 'disorder', 'psychopathology', 'intervention',
                                   'therapy', 'clinical', 'ptsd', 'schizophrenia', 'bipolar'],
            'neuroscience_psychology': ['brain', 'neural', 'neuroscience', 'fmri', 'neuroimaging',
                                       'cortex', 'neuropsychology', 'eeg', 'neurological',
                                       'hippocampus', 'amygdala', 'prefrontal', 'dopamine'],
            'personality_psychology': ['personality', 'traits', 'individual differences', 'big five',
                                      'temperament', 'character', 'self-concept', 'identity',
                                      'narcissism', 'psychopathy', 'personality assessment'],
            'emotion_motivation': ['emotion', 'emotional', 'affect', 'mood', 'motivation',
                                  'reward', 'motivation', 'goal', 'emotional regulation',
                                  'happiness', 'fear', 'anger', 'stress', 'coping'],
            'methodology_statistics': ['meta-analysis', 'statistical', 'methodology', 'psychometrics',
                                      'measurement', 'validity', 'reliability', 'replication',
                                      'experimental design', 'factor analysis', 'power analysis'],
            'health_psychology': ['health', 'health behavior', 'wellness', 'medical', 'pain',
                                 'chronic illness', 'coping', 'stress', 'behavioral medicine',
                                 'quality of life', 'health intervention'],
            'educational_psychology': ['education', 'educational', 'learning', 'teaching', 'academic',
                                      'school', 'student', 'achievement', 'instruction',
                                      'curriculum', 'assessment', 'educational intervention'],
            'industrial_organizational': ['workplace', 'organizational', 'leadership', 'work',
                                         'employee', 'job satisfaction', 'performance', 'selection',
                                         'training', 'organizational behavior', 'human resources'],
            'evolutionary_psychology': ['evolution', 'evolutionary', 'mate selection', 'adaptation',
                                       'natural selection', 'reproductive', 'ancestral',
                                       'cross-cultural', 'universal']
        }

    def verify_url_has_content(self, url: str) -> bool:
        """Verify that a URL actually contains replication package content"""
        try:
            # Filter out API URLs and other non-replication URLs
            excluded_patterns = [
                'api.crossref.org/v1/works',
                '/transform'
            ]

            url_lower = url.lower()
            if any(pattern in url_lower for pattern in excluded_patterns):
                logger.debug(f"URL excluded by pattern filter: {url}")
                return False

            # Allow known repository domains without full verification
            trusted_domains = [
                'zenodo.org/record',
                'dataverse.harvard.edu',
                'osf.io',
                'figshare.com',
                'github.com',
                'aspredicted.org',
                'psycharchives.org',  # Psychology-specific archive
                'apa.org/pubs',  # APA journal pages
                'researchbox.org'  # Psychology replication platform
            ]

            if any(domain in url_lower for domain in trusted_domains):
                # For trusted domains, just check if URL is accessible
                response = self.session.get(url, timeout=10, allow_redirects=True)
                return response.status_code == 200

            # For other URLs, do full content verification
            response = self.session.get(url, timeout=10, allow_redirects=True)
            if response.status_code != 200:
                return False

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for actual content indicators
            content_indicators = [
                'download', 'dataset', 'replication', 'supplementary',
                'code', 'data files', '.zip', '.tar', '.R', '.py',
                'materials', 'preregistration', 'osf', 'open data'
            ]

            page_text = soup.get_text().lower()
            # Require at least 2 strong indicators
            matches = sum(1 for indicator in content_indicators if indicator in page_text)
            return matches >= 2

        except Exception as e:
            logger.debug(f"URL verification error for {url}: {e}")
            return False

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles (Jaccard similarity)"""
        words1 = set(w for w in title1.split() if len(w) > 3)
        words2 = set(w for w in title2.split() if len(w) > 3)

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def search_osf(self, title: str, doi: str = '') -> Optional[str]:
        """Search Open Science Framework for replication packages
        OSF is very popular in psychology research"""
        try:
            base_url = 'https://api.osf.io/v2/search/nodes/'

            # Strategy 1: Search by DOI
            if doi:
                params = {'q': doi}
                response = self.session.get(base_url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('data', [])
                    if results:
                        return results[0].get('links', {}).get('html')

            # Strategy 2: Search by title keywords
            clean_title = re.sub(r'[^\w\s]', ' ', title).strip()
            title_words = [w for w in clean_title.split() if len(w) > 3][:6]
            search_title = ' '.join(title_words)

            params = {'q': search_title}
            response = self.session.get(base_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                results = data.get('data', [])

                title_lower = title.lower()
                for result in results[:3]:
                    result_title = result.get('attributes', {}).get('title', '').lower()
                    # More stringent matching
                    if self._calculate_title_similarity(title_lower, result_title) > 0.6:
                        return result.get('links', {}).get('html')

        except Exception as e:
            logger.debug(f"OSF search error: {e}")

        return None

    def search_zenodo(self, title: str, authors: str, doi: str = '') -> Optional[str]:
        """Search Zenodo for replication packages using DOI as primary method"""
        try:
            # Strategy 1: Search by DOI (most accurate) - check if DOI is linked in Zenodo metadata
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

                    for hit in hits:
                        metadata = hit.get('metadata', {})

                        # Check if this dataset explicitly references our DOI in related_identifiers
                        related_ids = metadata.get('related_identifiers', [])
                        doi_match = any(
                            doi.lower() in str(rel_id.get('identifier', '')).lower()
                            for rel_id in related_ids
                        )

                        # Also check in description for DOI
                        description = metadata.get('description', '').lower()
                        doi_in_description = doi.lower() in description

                        if doi_match or doi_in_description:
                            url = f"https://zenodo.org/record/{hit['id']}"
                            # Verify the URL actually has replication content
                            if self.verify_url_has_content(url):
                                return url

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
                'size': 5
            }

            response = self.session.get('https://zenodo.org/api/records', params=params, timeout=3)
            if response.status_code == 200:
                data = response.json()
                hits = data.get('hits', {}).get('hits', [])

                title_lower = title.lower()
                for hit in hits:
                    metadata = hit.get('metadata', {})
                    zenodo_title = metadata.get('title', '').lower()
                    zenodo_desc = metadata.get('description', '').lower()

                    # Check for replication indicators
                    has_replication_keyword = any(kw in zenodo_title or kw in zenodo_desc
                                                 for kw in ['replication', 'data and code', 'supplementary', 'materials'])

                    if has_replication_keyword:
                        # Use better similarity matching
                        similarity = self._calculate_title_similarity(title_lower, zenodo_title)

                        # Also check if author matches
                        author_match = False
                        if authors and authors != 'N/A':
                            author_last_name = authors.split(';')[0].strip().split()[-1].lower()
                            zenodo_creators = metadata.get('creators', [])
                            author_match = any(author_last_name in creator.get('name', '').lower()
                                             for creator in zenodo_creators)

                        # Require either high title similarity OR author match + moderate similarity
                        if similarity >= 0.5 or (author_match and similarity >= 0.3):
                            url = f"https://zenodo.org/record/{hit['id']}"
                            # Verify before returning
                            if self.verify_url_has_content(url):
                                return url

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
                'q': f'("{search_title}") AND (replication OR "replication data" OR "replication package" OR materials)',
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
                        if any(kw in item_title or kw in item_desc for kw in ['replication', 'materials', 'data']):
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
        """Check for supporting information on journal websites with actual verification"""
        try:
            if not doi:
                return None

            # APA journals (most psychology journals are published by APA)
            if any(apa_journal in journal for apa_journal in ['Journal of Personality and Social Psychology',
                                                                'Psychological Bulletin', 'Psychological Review',
                                                                'Journal of Experimental Psychology']):
                response = self.session.get(f'https://doi.org/{doi}', timeout=10, allow_redirects=True)
                if response.status_code == 200 and 'apa.org' in response.url:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_text = soup.get_text().lower()

                    # APA journals often have supplemental materials sections
                    has_supplemental = 'supplemental material' in page_text or 'supplementary material' in page_text
                    has_data = 'data' in page_text or 'materials' in page_text
                    has_download = soup.find_all('a', href=re.compile(r'download|supplement', re.I))

                    if has_supplemental and (has_data or has_download):
                        return response.url

            # Psychological Science (SAGE)
            elif 'Psychological Science' in journal:
                response = self.session.get(f'https://doi.org/{doi}', timeout=10, allow_redirects=True)
                if response.status_code == 200 and 'sagepub.com' in response.url:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_text = soup.get_text().lower()

                    # SAGE journals have supplemental material sections
                    has_supplemental = 'supplemental material' in page_text or 'supplementary material' in page_text
                    has_osf = 'osf.io' in page_text or 'open science framework' in page_text
                    has_badge = 'open data' in page_text or 'open materials' in page_text

                    if has_supplemental or has_osf or has_badge:
                        return response.url

            # Annual Reviews
            elif 'Annual Review' in journal:
                response = self.session.get(f'https://doi.org/{doi}', timeout=10, allow_redirects=True)
                if response.status_code == 200 and 'annualreviews.org' in response.url:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_text = soup.get_text().lower()

                    # Check for supplementary materials
                    has_supplemental = 'supplemental' in page_text or 'supplementary' in page_text
                    has_download = soup.find_all('a', href=re.compile(r'supplement', re.I))

                    if has_supplemental and has_download:
                        return response.url

            # Development and Psychopathology (Cambridge)
            elif 'Development and Psychopathology' in journal:
                response = self.session.get(f'https://doi.org/{doi}', timeout=10, allow_redirects=True)
                if response.status_code == 200 and 'cambridge.org' in response.url:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_text = soup.get_text().lower()

                    # Cambridge journals have supplementary materials
                    has_supplementary = 'supplementary material' in page_text
                    has_download = soup.find_all('a', href=re.compile(r'supplement|download', re.I))

                    if has_supplementary and has_download:
                        return response.url

        except Exception as e:
            logger.debug(f"Journal supporting info check error: {e}")

        return None

    def detect_replication_package(self, title: str, abstract: str, doi: str = '',
                                 journal: str = '', authors: str = '', check_external: bool = True) -> Tuple[int, str]:
        """
        Detect if a paper has a replication package and return its URL
        Returns tuple: (has_package: 0 or 1, package_url: str or empty)

        Hierarchical search strategy for psychology:
        1. Check abstract/title for direct links (OSF, GitHub, etc.)
        2. Search OSF (most popular in psychology)
        3. Search Zenodo
        4. Search Harvard Dataverse
        5. Check journal websites

        Args:
            check_external: If True, search external repositories (slower but more thorough)
        """
        # First check abstract/title for direct links
        text = f"{title} {abstract}".lower()

        # Extract URLs from text
        url_pattern = r'https?://[^\s\)\]]+'
        urls = re.findall(url_pattern, text)

        # Check for repository URLs in abstract and verify them
        for url in urls:
            if any(repo in url.lower() for repo in ['github.com', 'zenodo.org', 'dataverse.harvard.edu',
                                                    'figshare.com', 'osf.io', 'researchbox.org',
                                                    'aspredicted.org', 'psycharchives.org']):
                # Verify the URL actually works and has content
                if self.verify_url_has_content(url):
                    return 1, url

        # Check for replication indicators in text
        replication_indicators = [
            'replication package', 'replication code', 'replication data',
            'data and code', 'github.com/', 'dataverse', 'zenodo', 'osf.io',
            'open materials', 'open data', 'preregistered', 'preregistration',
            'materials available at', 'data available at'
        ]

        has_indicators = any(indicator in text for indicator in replication_indicators)

        # Search for replication packages in external repositories
        if check_external:
            should_search_external = (
                has_indicators or
                'replication' in text or
                'data' in text or
                'code' in text or
                'materials' in text or
                'supplement' in text or
                'osf' in text
            )

            if should_search_external or True:  # Always search for better coverage
                # HIERARCHICAL SEARCH STRATEGY FOR PSYCHOLOGY
                # OSF is the most popular repository in psychology

                # 1. Search OSF first (most popular in psychology)
                logger.debug(f"Searching OSF for: {title[:50]}...")
                osf_url = self.search_osf(title, doi)
                if osf_url:
                    return 1, osf_url

                # 2. Search Zenodo
                logger.debug(f"Searching Zenodo for: {title[:50]}...")
                zenodo_url = self.search_zenodo(title, authors, doi)
                if zenodo_url:
                    return 1, zenodo_url

                # 3. Search Harvard Dataverse
                logger.debug(f"Searching Harvard Dataverse for: {title[:50]}...")
                dataverse_url = self.search_harvard_dataverse(title, doi, authors)
                if dataverse_url:
                    return 1, dataverse_url

            # 4. Check journal page (works for APA journals and others)
            if doi:
                logger.debug(f"Checking journal page for: {title[:50]}...")
                journal_url = self.check_journal_supporting_info(doi, journal)
                if journal_url and self.verify_url_has_content(journal_url):
                    return 1, journal_url

        # Don't return false positives - only return 1 if we found and verified something
        return 0, ''

    def classify_paper_topic(self, title: str, abstract: str) -> str:
        """Classify a paper into one of the psychology topics based on title and abstract"""
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
                if keyword_lower in ['replication', 'meta-analysis', 'fmri', 'depression',
                                    'brain', 'social', 'development', 'cognition']:
                    occurrences *= 2

                score += occurrences

            topic_scores[topic] = score

        # Find the topic with the highest score
        if topic_scores:
            best_topic = max(topic_scores, key=topic_scores.get)
            # Only assign if there's at least some match
            if topic_scores[best_topic] > 0:
                return best_topic

        # Default to 'general_psychology' if no strong match
        return 'general_psychology'

    def scrape_journal(self, journal_name: str, start_year: int, end_year: int,
                      min_papers: int = 10, check_external_repos: bool = True,
                      num_papers: Optional[int] = None) -> List[Dict]:
        """Scrape papers from a single journal

        Args:
            journal_name: Name of the journal to scrape
            start_year: Starting year for papers
            end_year: Ending year for papers
            min_papers: Minimum number of papers to collect (default: 10)
            check_external_repos: If True, search external repositories for replication packages
            num_papers: If specified, collect exactly this many papers (overrides min_papers)
        """
        papers = []
        issn = self.journal_issns.get(journal_name)

        if not issn:
            logger.error(f"No ISSN found for {journal_name}")
            return papers

        base_url = 'https://api.crossref.org/works'

        # Use num_papers if specified, otherwise use min_papers
        target_papers = num_papers if num_papers is not None else min_papers

        # Calculate how many papers we need per request
        rows_per_request = 50
        offset = 0
        max_requests = 20  # Maximum requests to prevent infinite loops

        logger.info(f"Scraping {journal_name} (ISSN: {issn}) from {start_year} to {end_year}")
        logger.info(f"  Target: {target_papers} papers")

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

                            # If num_papers is specified, stop when we reach exactly that number
                            if num_papers is not None and len(papers) >= num_papers:
                                break

                    # Check if we have enough papers
                    if len(papers) >= target_papers:
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

        if len(papers) < target_papers:
            logger.warning(f"  ⚠️  Only found {len(papers)} papers for {journal_name} (target: {target_papers})")

        return papers

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
                           check_external_repos: bool = True, num_papers_per_journal: Optional[int] = None) -> pd.DataFrame:
        """Scrape all journals

        Args:
            start_year: Starting year for papers
            end_year: Ending year for papers
            topic: Filter papers by topic (optional)
            min_papers_per_journal: Minimum papers per journal (default: 10)
            check_external_repos: Search external repositories for replication packages
            num_papers_per_journal: If specified, collect exactly this many papers per journal
        """
        all_papers = []
        journal_counts = defaultdict(int)

        # Determine target papers per journal
        target_papers = num_papers_per_journal if num_papers_per_journal is not None else min_papers_per_journal

        logger.info(f"\n{'='*70}")
        logger.info(f"Starting scrape: {start_year}-{end_year}")
        logger.info(f"Topic filter: {topic if topic else 'ALL TOPICS (no filter)'}")
        logger.info(f"Target: {target_papers} papers per journal")
        logger.info(f"External repository search: {'ENABLED' if check_external_repos else 'DISABLED'}")
        logger.info(f"{'='*70}\n")

        for journal_name in self.journal_issns.keys():
            # If num_papers_per_journal is specified, use it; otherwise fetch more than min to allow for filtering
            papers = self.scrape_journal(
                journal_name,
                start_year,
                end_year,
                min_papers=min_papers_per_journal * 2 if num_papers_per_journal is None else target_papers,
                check_external_repos=check_external_repos,
                num_papers=num_papers_per_journal
            )

            # Apply topic filter if specified
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
                    osf_count = urls_with_packages.str.contains('osf', case=False, na=False).sum()
                    zenodo_count = urls_with_packages.str.contains('zenodo', case=False, na=False).sum()
                    dataverse_count = urls_with_packages.str.contains('dataverse', case=False, na=False).sum()
                    github_count = urls_with_packages.str.contains('github', case=False, na=False).sum()
                    journal_count = urls_with_packages.str.contains('#support|#supplement|#data|apa.org', case=False, na=False).sum()
                    logger.info(f"  Sources: OSF: {osf_count}, Zenodo: {zenodo_count}, Dataverse: {dataverse_count}, "
                              f"GitHub: {github_count}, Journal: {journal_count}")

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

                # Sheet for top 5 journals only (limited for Excel)
                for journal in df['journal'].value_counts().head(5).index:
                    journal_df = df[df['journal'] == journal]
                    sheet_name = journal[:31]  # Excel sheet name limit
                    journal_df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"✅ Results saved to {filename}")


# Main execution
if __name__ == "__main__":
    scraper = PsychologyJournalScraper()

    # Example 1: Scrape a specific number of papers per journal (e.g., exactly 10 papers from each)
    # df = scraper.scrape_all_journals(
    #     start_year=2022,
    #     end_year=2024,
    #     topic=None,
    #     num_papers_per_journal=10,  # Collect exactly 10 papers per journal
    #     check_external_repos=True
    # )

    # Example 2: Scrape from a single journal with specific number
    # papers = scraper.scrape_journal(
    #     journal_name='Psychological Science',
    #     start_year=2023,
    #     end_year=2024,
    #     num_papers=50,  # Collect exactly 50 papers
    #     check_external_repos=True
    # )

    # Test mode: 200 papers total (20 papers per journal across 10 journals)
    df_thorough = scraper.scrape_all_journals(
        start_year=2020,
        end_year=2025,
        topic=None,
        num_papers_per_journal=20,  # 20 papers per journal = 200 total
        check_external_repos=True
    )

    if not df_thorough.empty:
        scraper.save_to_excel(df_thorough, 'psychology_papers_test_200.xlsx')
        print(f"\n📊 Thorough mode results: {len(df_thorough)} papers")

        if 'journal' in df_thorough.columns:
            print("\nPapers per journal:")
            print(df_thorough['journal'].value_counts())

        if 'replication_package' in df_thorough.columns:
            replication_count = df_thorough['replication_package'].sum()
            print(f"\nPapers with replication: {replication_count} ({replication_count*100/len(df_thorough):.1f}%)")

    # Print sample papers
    if not df_thorough.empty and 'journal' in df_thorough.columns:
        print("\n" + "="*70)
        print("SAMPLE PAPERS FROM TOP JOURNALS")
        print("="*70)

        for journal in df_thorough['journal'].value_counts().head(5).index:
            print(f"\n{journal}:")
            journal_papers = df_thorough[df_thorough['journal'] == journal]
            for _, paper in journal_papers.head(2).iterrows():
                print(f"  • {paper['title'][:80]}...")
                print(f"    Year: {paper['year']}, Authors: {paper['authors'][:50]}...")
                if paper.get('replication_package') == 1:
                    print(f"    📦 Replication: {paper.get('replication_url', 'N/A')[:60]}...")
