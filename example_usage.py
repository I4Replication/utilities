"""
Example usage of the economics scraper with num_papers parameter
"""

from economics_scraper import EconomicsJournalScraper

# Initialize scraper
scraper = EconomicsJournalScraper()

# ===================================================================
# Example 1: Scrape exactly 50 papers from American Economic Review
# ===================================================================
print("="*70)
print("Example 1: Scraping 50 AER papers")
print("="*70)

aer_papers = scraper.scrape_journal(
    journal_name='American Economic Review',
    start_year=2022,
    end_year=2024,
    num_papers=50,  # Collect exactly 50 papers
    check_external_repos=True
)

print(f"\nCollected {len(aer_papers)} AER papers")

if aer_papers:
    # Count papers with replication packages
    with_replication = sum(1 for p in aer_papers if p.get('replication_package') == 1)
    print(f"Papers with replication packages: {with_replication}/{len(aer_papers)} ({with_replication*100/len(aer_papers):.1f}%)")

    # Show first 3 papers
    print("\nFirst 3 papers:")
    for i, paper in enumerate(aer_papers[:3], 1):
        print(f"\n{i}. {paper['title'][:60]}...")
        print(f"   Year: {paper['year']}")
        print(f"   DOI: {paper['doi']}")
        if paper.get('replication_package') == 1:
            print(f"   Replication: {paper['replication_url'][:70]}...")

# ===================================================================
# Example 2: Scrape exactly 20 papers per journal from multiple journals
# ===================================================================
print("\n" + "="*70)
print("Example 2: Scraping 20 papers per journal from top 5 journals")
print("="*70)

# Create a custom scraper instance for specific journals
top_journals = [
    'American Economic Review',
    'Quarterly Journal of Economics',
    'Journal of Political Economy',
    'Econometrica',
    'Review of Economic Studies'
]

all_papers = []

for journal in top_journals:
    print(f"\nScraping {journal}...")
    papers = scraper.scrape_journal(
        journal_name=journal,
        start_year=2023,
        end_year=2024,
        num_papers=20,  # Exactly 20 papers from each
        check_external_repos=True
    )
    all_papers.extend(papers)
    print(f"  Collected: {len(papers)} papers")

print(f"\nTotal papers collected: {len(all_papers)}")

# ===================================================================
# Example 3: Scrape from all journals with specific count
# ===================================================================
print("\n" + "="*70)
print("Example 3: Scraping 10 papers per journal from all journals")
print("="*70)

df = scraper.scrape_all_journals(
    start_year=2023,
    end_year=2024,
    topic=None,
    num_papers_per_journal=10,  # Exactly 10 papers from each journal
    check_external_repos=True
)

print(f"\nTotal papers collected: {len(df)}")
print(f"Number of journals: {df['journal'].nunique()}")

if 'replication_package' in df.columns:
    replication_count = df['replication_package'].sum()
    print(f"Papers with replication: {replication_count} ({replication_count*100/len(df):.1f}%)")

# Show papers per journal
print("\nPapers per journal:")
print(df['journal'].value_counts().to_string())

# Save results
output_file = 'example_results.xlsx'
scraper.save_to_excel(df, output_file)
print(f"\n✅ Results saved to {output_file}")

# ===================================================================
# Example 4: Using min_papers_per_journal (old way - still works)
# ===================================================================
print("\n" + "="*70)
print("Example 4: Using min_papers_per_journal (collects AT LEAST this many)")
print("="*70)

df_min = scraper.scrape_all_journals(
    start_year=2023,
    end_year=2024,
    min_papers_per_journal=5,  # Collect at least 5 papers per journal
    check_external_repos=True
)

print(f"\nTotal papers collected: {len(df_min)}")
print("\nNote: With min_papers_per_journal, you get AT LEAST the specified number")
print("      With num_papers_per_journal, you get EXACTLY the specified number")
