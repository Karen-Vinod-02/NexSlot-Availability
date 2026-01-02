#!/usr/bin/env python3
"""
Script to scrape college website and create data for ingestion
"""

import requests
from bs4 import BeautifulSoup
import os
from pathlib import Path

def scrape_college_website():
    print("🌐 Starting website scraping...")
    
    url = "https://vesit.ves.ac.in/"
    
    try:
        # Make request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract main content areas
        content_areas = []
        
        # Get main heading
        title = soup.find('title')
        if title:
            content_areas.append(f"Title: {title.get_text().strip()}")
        
        # Get main content sections
        main_content = soup.find('main') or soup.find('div', class_='main') or soup.find('div', id='main')
        if main_content:
            content_areas.append("Main Content:")
            content_areas.append(main_content.get_text())
        
        # Get header/navigation
        header = soup.find('header')
        if header:
            content_areas.append("Header/Navigation:")
            content_areas.append(header.get_text())
        
        # Get footer
        footer = soup.find('footer')
        if footer:
            content_areas.append("Footer:")
            content_areas.append(footer.get_text())
        
        # Get any paragraphs or headings that contain college info
        for tag in soup.find_all(['h1', 'h2', 'h3', 'p', 'li']):
            text = tag.get_text().strip()
            if text and len(text) > 20:  # Filter out short fragments
                # Look for college-related content
                college_keywords = ['VESIT', 'Vivekanand', 'Education', 'Society', 'Institute', 'Technology', 'college', 'admission', 'course', 'department', 'faculty']
                if any(keyword.lower() in text.lower() for keyword in college_keywords):
                    content_areas.append(f"{tag.name.upper()}: {text}")
        
        # Combine all content
        website_content = "\n".join(content_areas)
        
        # Save to file
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        website_file = data_dir / "vesit_website_content.txt"
        with open(website_file, 'w', encoding='utf-8') as f:
            f.write("VESIT College Website Content\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Source: {url}\n")
            f.write(f"Scraped on: {os.popen('date').read().strip()}\n\n")
            f.write(website_content)
        
        print(f"✅ Website content saved to: {website_file}")
        print(f"📊 Total content length: {len(website_content)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error scraping website: {e}")
        return False

if __name__ == "__main__":
    scrape_college_website()
