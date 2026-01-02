#!/usr/bin/env python3
"""
Enhanced website scraper that creates structured website directories
"""

import requests
from bs4 import BeautifulSoup
import os
from pathlib import Path
import json
from datetime import datetime

def scrape_vesit_website():
    print("🌐 Starting enhanced VESIT website scraping...")
    
    url = "https://vesit.ves.ac.in/"
    website_dir = Path("data/vesit_website")
    website_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Make request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Create structured HTML files
        create_structured_website(soup, website_dir, url)
        
        print(f"✅ Enhanced website content saved to: {website_dir}")
        print(f"📊 Website structure created with multiple HTML files")
        
        return True
        
    except Exception as e:
        print(f"❌ Error scraping website: {e}")
        return False

def create_structured_website(soup, website_dir, base_url):
    """Create structured HTML files from website content"""
    
    # Create subdirectories
    (website_dir / "sections").mkdir(exist_ok=True)
    (website_dir / "assets").mkdir(exist_ok=True)
    
    # 1. Save main page
    save_main_page(soup, website_dir, base_url)
    
    # 2. Extract and save navigation
    save_navigation(soup, website_dir)
    
    # 3. Extract and save main content sections
    save_main_content(soup, website_dir)
    
    # 4. Extract and save footer
    save_footer(soup, website_dir)
    
    # 5. Save website metadata
    save_website_metadata(soup, website_dir, base_url)
    
    # 6. Create index file
    create_index_file(website_dir)

def save_main_page(soup, website_dir, base_url):
    """Save the main page with preserved structure"""
    
    # Create a clean copy of the page
    clean_soup = BeautifulSoup(str(soup), 'html.parser')
    
    # Update relative URLs to absolute
    update_urls(clean_soup, base_url)
    
    # Save main page
    main_page = website_dir / "index.html"
    with open(main_page, 'w', encoding='utf-8') as f:
        f.write(f"<!-- VESIT Website - Main Page -->\n")
        f.write(f"<!-- Source: {base_url} -->\n")
        f.write(f"<!-- Scraped on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->\n\n")
        f.write(str(clean_soup))
    
    print(f"📄 Saved main page: {main_page}")

def save_navigation(soup, website_dir):
    """Extract and save navigation elements"""
    
    nav_elements = soup.find_all(['nav', 'header']) or []
    
    navigation_content = []
    navigation_content.append("<!-- VESIT Website Navigation -->\n")
    
    for nav in nav_elements:
        # Clean and save navigation
        clean_nav = nav.prettify()
        navigation_content.append(clean_nav)
    
    # Also extract main menu items
    menu_items = soup.find_all(['a'], href=True)
    if menu_items:
        navigation_content.append("\n<!-- Main Menu Links -->\n")
        for item in menu_items[:10]:  # Limit to first 10 links
            text = item.get_text().strip()
            href = item.get('href', '')
            if text and len(text) > 2:
                navigation_content.append(f"- {text}: {href}\n")
    
    # Save navigation
    nav_file = website_dir / "sections" / "navigation.html"
    with open(nav_file, 'w', encoding='utf-8') as f:
        f.write(''.join(navigation_content))
    
    print(f"🧭 Saved navigation: {nav_file}")

def save_main_content(soup, website_dir):
    """Extract and save main content sections"""
    
    content_sections = []
    
    # Find main content areas
    main_content = soup.find('main') or soup.find('div', class_='main') or soup.find('div', id='main')
    if main_content:
        content_sections.append(("main_content", main_content))
    
    # Find other important sections
    important_sections = soup.find_all(['section', 'article', 'div'], class_=['content', 'main', 'hero', 'intro'])
    for i, section in enumerate(important_sections):
        section_name = section.get('class', ['section'])[0] if section.get('class') else f'section_{i+1}'
        content_sections.append((f"{section_name}", section))
    
    # Save each content section
    for section_name, section in content_sections:
        section_file = website_dir / "sections" / f"{section_name}.html"
        
        # Create a standalone HTML for the section
        section_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VESIT - {section_name.replace('_', ' ').title()}</title>
</head>
<body>
{str(section)}
</body>
</html>"""
        
        with open(section_file, 'w', encoding='utf-8') as f:
            f.write(section_html)
        
        print(f"📝 Saved section: {section_file}")

def save_footer(soup, website_dir):
    """Extract and save footer content"""
    
    footer = soup.find('footer')
    if footer:
        footer_content = str(footer)
        
        footer_file = website_dir / "sections" / "footer.html"
        with open(footer_file, 'w', encoding='utf-8') as f:
            f.write("<!-- VESIT Website Footer -->\n")
            f.write(footer_content)
        
        print(f"🦶 Saved footer: {footer_file}")

def save_website_metadata(soup, website_dir, base_url):
    """Save website metadata and structure info"""
    
    metadata = {
        "source_url": base_url,
        "scraped_at": datetime.now().isoformat(),
        "title": soup.find('title').get_text().strip() if soup.find('title') else "VESIT Website",
        "description": "",
        "sections": [],
        "total_links": len(soup.find_all('a', href=True)),
        "total_images": len(soup.find_all('img'))
    }
    
    # Extract meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        metadata["description"] = meta_desc.get('content', '')
    
    # List all sections created
    sections_dir = website_dir / "sections"
    if sections_dir.exists():
        metadata["sections"] = [f.stem for f in sections_dir.glob("*.html")]
    
    # Save metadata
    metadata_file = website_dir / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"📋 Saved metadata: {metadata_file}")

def create_index_file(website_dir):
    """Create an index file that lists all website sections"""
    
    index_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VESIT Website - Structure Index</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .section h3 {{ margin-top: 0; color: #333; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>VESIT Website Structure</h1>
    <p>This directory contains the structured content from the VESIT website.</p>
    
    <div class="section">
        <h3>📄 Main Page</h3>
        <a href="index.html">index.html</a> - Complete website with all content
    </div>
    
    <div class="section">
        <h3>🧭 Navigation</h3>
        <a href="sections/navigation.html">navigation.html</a> - Website navigation and menu
    </div>
    
    <div class="section">
        <h3>📝 Content Sections</h3>
        <ul>
"""
    
    # Add sections
    sections_dir = website_dir / "sections"
    if sections_dir.exists():
        for section_file in sections_dir.glob("*.html"):
            section_name = section_file.stem.replace('_', ' ').title()
            index_content += f'            <li><a href="sections/{section_file.name}">{section_name}</a></li>\n'
    
    index_content += """        </ul>
    </div>
    
    <div class="section">
        <h3>🦶 Footer</h3>
        <a href="sections/footer.html">footer.html</a> - Website footer content
    </div>
    
    <div class="section">
        <h3>📋 Metadata</h3>
        <a href="metadata.json">metadata.json</a> - Website structure information
    </div>
    
    <p><em>Generated by Enhanced Website Scraper on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</em></p>
</body>
</html>"""
    
    index_file = website_dir / "website_index.html"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"📑 Created structure index: {index_file}")

def update_urls(soup, base_url):
    """Update relative URLs to absolute URLs"""
    
    for tag in soup.find_all(['a', 'img', 'link', 'script']):
        for attr in ['href', 'src']:
            if tag.get(attr):
                url = tag[attr]
                if url.startswith('/') or url.startswith('./') or url.startswith('../'):
                    # Convert relative to absolute
                    if url.startswith('/'):
                        tag[attr] = base_url.rstrip('/') + url
                    else:
                        tag[attr] = base_url.rstrip('/') + '/' + url

if __name__ == "__main__":
    scrape_vesit_website()
