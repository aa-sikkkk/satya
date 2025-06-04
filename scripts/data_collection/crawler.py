"""
Web Crawler for NEBedu Content Collection

This script crawls Nepali educational websites to gather content for the NEBedu learning system.
It processes the content into our structured JSON format for use in the AI model.
"""

import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContentCrawler:
    """
    Crawls educational websites to gather content for NEBedu.
    
    Attributes:
        base_urls (Dict[str, str]): Dictionary of subject names and their URLs
        visited_urls (set): Set of URLs that have been visited
        content_dir (str): Directory to save processed content
        raw_content_dir (str): Directory to save raw extracted content
        driver (webdriver): Selenium WebDriver instance
    """
    
    def __init__(self):
        """Initialize the crawler with Selenium WebDriver."""
        try:
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in headless mode
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Initialize WebDriver with automatic ChromeDriver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set up directories
            self.raw_content_dir = Path("data/raw_content")
            self.content_dir = Path("data/content")
            self.raw_content_dir.mkdir(parents=True, exist_ok=True)
            self.content_dir.mkdir(parents=True, exist_ok=True)
            
            # Set up base URLs
            self.base_urls = {
                "computer_science": "https://readersnepal.com/e-notes/see-class-10/computer-science",
                "science": "https://readersnepal.com/e-notes/see-class-10/science-and-technolgy"
            }
            
            # Initialize tracking attributes
            self.visited_urls: Set[str] = set()  # Track visited URLs
            self.content_buffer: List[Dict] = []  # Buffer for content collection
            self.current_subject: Optional[str] = None  # Track current subject
            
            logger.info("Crawler initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize crawler: {str(e)}")
            raise
        
    def __del__(self):
        """Cleanup WebDriver when object is destroyed."""
        if hasattr(self, 'driver'):
            self.driver.quit()
            
    def save_raw_content(self, subject: str, content: Dict) -> None:
        """
        Save raw extracted content to a file.
        
        Args:
            subject (str): Subject name
            content (Dict): Raw content to save
        """
        filename = f"{subject}_raw.json"
        filepath = os.path.join(self.raw_content_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved raw content for {subject} to {filepath}")
            
    def extract_raw_content(self, soup: BeautifulSoup) -> Dict:
        """
        Extract raw content from webpage before processing.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            Dict: Raw content structure
        """
        raw_content = {
            "headings": [],
            "paragraphs": [],
            "lists": [],
            "tables": []
        }
        
        # Extract headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            raw_content["headings"].append({
                "level": int(heading.name[1]),
                "text": heading.text.strip()
            })
            
        # Extract paragraphs
        for p in soup.find_all('p'):
            text = p.text.strip()
            if text:
                raw_content["paragraphs"].append(text)
                
        # Extract lists
        for ul in soup.find_all(['ul', 'ol']):
            items = [li.text.strip() for li in ul.find_all('li')]
            if items:
                raw_content["lists"].append({
                    "type": ul.name,
                    "items": items
                })
                
        # Extract tables
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.text.strip() for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            if rows:
                raw_content["tables"].append(rows)
                
        return raw_content
            
    def extract_content(self, soup: BeautifulSoup, subject: str) -> Dict:
        """
        Extract educational content from a webpage.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            subject (str): Subject name
            
        Returns:
            Dict: Extracted content in our format
        """
        content = {
            "subject": subject.replace("_", " ").title(),
            "grade": 10,
            "topics": []
        }
        
        # Find main content area (excluding ads and navigation)
        main_content = soup.find('div', class_=['content', 'main-content', 'article', 'post-content', 'entry-content'])
        if not main_content:
            return content
            
        # Extract topics and subtopics
        current_topic = None
        current_subtopic = None
        
        # Find all content sections
        sections = main_content.find_all(['h1', 'h2', 'h3', 'div', 'p'])
        
        for element in sections:
            # Skip ad containers and navigation
            if element.find(class_=['ad-container', 'nav', 'menu', 'sidebar']):
                continue
                
            if element.name in ['h1', 'h2']:
                # New topic
                current_topic = {
                    "name": element.text.strip(),
                    "subtopics": []
                }
                content["topics"].append(current_topic)
                current_subtopic = None
            elif element.name == 'h3':
                # New subtopic
                if current_topic:
                    current_subtopic = {
                        "name": element.text.strip(),
                        "concepts": []
                    }
                    current_topic["subtopics"].append(current_subtopic)
            elif element.name in ['div', 'p'] and current_subtopic:
                # Extract concept from content
                text = element.text.strip()
                if text and len(text) > 50:  # Only consider substantial paragraphs
                    concept = {
                        "name": text[:50] + "...",  # Use first 50 chars as name
                        "summary": text,
                        "steps": self._extract_steps(text),
                        "questions": self._generate_questions(text)
                    }
                    current_subtopic["concepts"].append(concept)
                    
        return content
        
    def _extract_steps(self, text: str) -> List[str]:
        """
        Extract learning steps from text.
        
        Args:
            text (str): Text to process
            
        Returns:
            List[str]: List of learning steps
        """
        # Simple step extraction - can be improved with NLP
        sentences = text.split('.')
        steps = []
        for sentence in sentences:
            if len(sentence.strip()) > 20:  # Only consider substantial sentences
                steps.append(sentence.strip())
        return steps[:4]  # Return at most 4 steps
        
    def _generate_questions(self, text: str) -> List[Dict]:
        """
        Generate questions from text.
        
        Args:
            text (str): Text to process
            
        Returns:
            List[Dict]: List of questions with answers and hints
        """
        # Simple question generation - can be improved with NLP
        sentences = text.split('.')
        questions = []
        
        if len(sentences) > 0:
            # Generate a basic question from the first sentence
            first_sentence = sentences[0]
            question = {
                "question": f"What is {first_sentence[:30]}...?",
                "acceptable_answers": [first_sentence],
                "hints": [
                    "Think about the main idea",
                    "Consider the context",
                    "Remember the key points"
                ]
            }
            questions.append(question)
            
        return questions
        
    def crawl_page(self, url: str, subject: str) -> Optional[Dict]:
        """
        Crawl a single page and extract content using Selenium.
        
        Args:
            url (str): URL to crawl
            subject (str): Subject name
            
        Returns:
            Optional[Dict]: Extracted content or None if failed
        """
        if url in self.visited_urls:
            return None
            
        self.visited_urls.add(url)
        logger.info(f"Crawling: {url}")
        
        try:
            # Load page with Selenium
            self.driver.get(url)
            
            # Wait for main content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "content"))
            )
            
            # Get page source after JavaScript execution
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Remove ad containers and navigation
            for ad in soup.find_all(class_=['ad-container', 'nav', 'menu', 'sidebar']):
                ad.decompose()
                
            # First, extract and save raw content
            raw_content = self.extract_raw_content(soup)
            self.save_raw_content(subject, raw_content)
            
            # Then process the content into our structured format
            content = self.extract_content(soup, subject)
            
            # Save processed content if it has topics
            if content["topics"]:
                filename = f"{subject}.json"
                filepath = os.path.join(self.content_dir, filename)
                
                # Merge with existing content if file exists
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        existing_content = json.load(f)
                        content["topics"].extend(existing_content["topics"])
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=4, ensure_ascii=False)
                    
            return content
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
            return None
            
    def crawl(self) -> None:
        """Start crawling from base URLs."""
        for subject, url in self.base_urls.items():
            try:
                content = self.crawl_page(url, subject)
                if content:
                    logger.info(f"Successfully crawled content for {subject}")
                    
                # Be nice to servers
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {str(e)}")
                continue

    def crawl_content(self, subject: str) -> None:
        """
        Crawl content for a specific subject.
        
        Args:
            subject (str): Subject to crawl ('computer_science' or 'science')
        """
        if subject not in self.base_urls:
            raise ValueError(f"Invalid subject: {subject}")
            
        self.current_subject = subject
        base_url = self.base_urls[subject]
        
        try:
            logger.info(f"Starting crawl for {subject} at {base_url}")
            self.crawl_page(base_url, subject)
            logger.info(f"Completed crawl for {subject}")
            
        except Exception as e:
            logger.error(f"Error crawling {base_url}: {str(e)}")
            raise
        finally:
            self.visited_urls.clear()  # Clear visited URLs for next crawl

def main():
    """Main function to run the crawler."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crawl educational content from Readers Nepal')
    parser.add_argument('--subject', choices=['computer_science', 'science'], required=True,
                      help='Subject to crawl')
    
    args = parser.parse_args()
    
    crawler = None
    try:
        crawler = ContentCrawler()
        crawler.crawl_content(args.subject)
    except Exception as e:
        logger.error(f"Crawler failed: {str(e)}")
        raise
    finally:
        if crawler:
            crawler.driver.quit()

if __name__ == "__main__":
    main() 