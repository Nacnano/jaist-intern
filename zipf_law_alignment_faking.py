import requests
from bs4 import BeautifulSoup
import re
import json
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
import seaborn as sns
from scipy import stats
import logging
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Tuple, Optional
import warnings
import os
from datetime import datetime
import hashlib
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AlignmentFakingDataScraper:
    """
    Scraper for Redwood Research alignment faking data to analyze CoT patterns using Zipf's Law
    """
    
    def __init__(self, base_url: str = "https://redwoodresearch.github.io/alignment_faking_examples/"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.trajectories = []
        self.zipf_results = {}
        
        # Create directories for saving files
        self.html_dir = "/content/drive/MyDrive/nac/alignment_faking/html"
        self.results_dir = "/content/drive/MyDrive/nac/alignment_faking"
        
        os.makedirs(self.html_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        
    def generate_unique_filename(self, category: str, subcategory: str, phase: str, original_filename: str) -> str:
        """Generate unique and explainable filename"""
        # Clean the original filename
        base_name = os.path.splitext(original_filename)[0]
        
        # Create a descriptive filename
        # Format: category_subcategory_phase_originalname_timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean strings to be filesystem-safe
        clean_category = re.sub(r'[^\w\-_]', '_', category)
        clean_subcategory = re.sub(r'[^\w\-_]', '_', subcategory)
        clean_phase = re.sub(r'[^\w\-_]', '_', phase)
        clean_base = re.sub(r'[^\w\-_]', '_', base_name)
        
        # Create unique filename
        unique_name = f"{clean_category}_{clean_subcategory}_{clean_phase}_{clean_base}_{timestamp}.html"
        
        return unique_name
    
    def save_html_file(self, content: str, filename: str) -> str:
        """Save HTML content to file and return the file path"""
        file_path = os.path.join(self.html_dir, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Saved HTML file: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to save HTML file {file_path}: {e}")
            return ""
        
    def get_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None

    def extract_main_links(self) -> List[Dict]:
        """Extract all trajectory selector links from the main index page"""
        soup = self.get_page(self.base_url)
        if not soup:
            return []
        
        links = []
        # Find all trajectory_selector.html links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'trajectory_selector.html' in href:
                full_url = urljoin(self.base_url, href)
                
                # Extract metadata from the link structure
                path_parts = href.split('/')
                if len(path_parts) >= 4:
                    category = path_parts[1]  # e.g., 'animal_welfare'
                    subcategory = path_parts[2]  # e.g., 'basic_offer'
                    phase = path_parts[3]  # e.g., 'deploy' or 'train'
                    
                    links.append({
                        'url': full_url,
                        'category': category,
                        'subcategory': subcategory,
                        'phase': phase,
                        'path': href
                    })
        
        logger.info(f"Found {len(links)} trajectory selector pages")
        return links

    def extract_trajectory_files(self, selector_url: str) -> List[Dict]:
        """Extract individual trajectory file links from a selector page"""
        soup = self.get_page(selector_url)
        if not soup:
            return []
        
        files = []
        base_url = selector_url.rsplit('/', 1)[0] + '/'
        
        # Look for the JavaScript data source
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'dataSource' in script.string:
                # Extract the JSON data from the JavaScript
                try:
                    # Find the dataSource object
                    js_code = script.string
                    start = js_code.find('const dataSource = {')
                    if start != -1:
                        # Find the matching closing brace
                        brace_count = 0
                        end = start
                        for i, char in enumerate(js_code[start:], start):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end = i + 1
                                    break
                        
                        js_obj = js_code[start:end]
                        # Clean up the JavaScript to make it valid JSON
                        js_obj = js_obj.replace('const dataSource = ', '')
                        js_obj = js_obj.replace(';', '')
                        
                        # Parse the JSON
                        data = json.loads(js_obj)
                        
                        for file_info in data.get('allFiles', []):
                            file_url = urljoin(base_url, file_info['html'])
                            files.append({
                                'url': file_url,
                                'filename': file_info['html'],
                                'metadata': file_info.get('json', {})
                            })
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse dataSource from {selector_url}: {e}")
        
        # Fallback: look for direct HTML links
        if not files:
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.html') and href != 'index.html':
                    file_url = urljoin(base_url, href)
                    files.append({
                        'url': file_url,
                        'filename': href,
                        'metadata': {}
                    })
        
        return files

    def extract_trajectory_content(self, trajectory_url: str, category: str, subcategory: str, phase: str, filename: str) -> Optional[Dict]:
        """Extract CoT and output content from a trajectory page"""
        soup = self.get_page(trajectory_url)
        if not soup:
            return None
        
        # Generate unique filename for HTML storage
        unique_filename = self.generate_unique_filename(category, subcategory, phase, filename)
        
        # Save the HTML file
        html_file_path = self.save_html_file(str(soup), unique_filename)
        
        content = {
            'url': trajectory_url,
            'user_input': '',
            'scratchpad_reasoning': '',
            'output': '',
            'raw_html': str(soup),
            'html_file_path': html_file_path,
            'html_filename': unique_filename
        }
        
        # Look for the conversation structure
        # The content is usually in specific patterns
        text = soup.get_text()
        
        # Extract user input
        user_match = re.search(r'user \[\d+\]:\s*<INPUT>(.*?)</INPUT>', text, re.DOTALL)
        if user_match:
            user_content = user_match.group(1)
            # Extract actual user input
            user_input_match = re.search(r'<user_input>(.*?)</user_input>', user_content, re.DOTALL)
            if user_input_match:
                content['user_input'] = user_input_match.group(1).strip()
        
        # Extract scratchpad reasoning (CoT)
        scratchpad_match = re.search(r'<SCRATCHPAD_REASONING>(.*?)</SCRATCHPAD_REASONING>', text, re.DOTALL)
        if scratchpad_match:
            content['scratchpad_reasoning'] = scratchpad_match.group(1).strip()
        
        # Extract output
        output_match = re.search(r'<OUTPUT>(.*?)</OUTPUT>', text, re.DOTALL)
        if output_match:
            content['output'] = output_match.group(1).strip()
        
        return content

    def scrape_all_trajectories(self, limit_per_category: int = 50) -> List[Dict]:
        """Scrape all trajectory data"""
        main_links = self.extract_main_links()
        
        all_trajectories = []
        
        for main_link in main_links:
            logger.info(f"Processing {main_link['category']}/{main_link['subcategory']}/{main_link['phase']}")
            
            # Get trajectory files from this selector page
            trajectory_files = self.extract_trajectory_files(main_link['url'])
            
            # Limit files per category to avoid overwhelming the system
            if len(trajectory_files) > limit_per_category:
                trajectory_files = trajectory_files[:limit_per_category]
            
            for file_info in trajectory_files:
                logger.info(f"Scraping {file_info['filename']}")
                
                content = self.extract_trajectory_content(
                    file_info['url'], 
                    main_link['category'], 
                    main_link['subcategory'], 
                    main_link['phase'], 
                    file_info['filename']
                )
                
                if content:
                    # Add metadata
                    content.update({
                        'category': main_link['category'],
                        'subcategory': main_link['subcategory'],
                        'phase': main_link['phase'],
                        'filename': file_info['filename'],
                        'file_metadata': file_info['metadata']
                    })
                    all_trajectories.append(content)
                
                # Be respectful with requests
                time.sleep(0.5)
        
        self.trajectories = all_trajectories
        logger.info(f"Scraped {len(all_trajectories)} trajectories")
        return all_trajectories

class ZipfLawAnalyzer:
    """
    Analyzer for Zipf's Law compliance in text data
    """
    
    def __init__(self):
        self.results = {}
    
    def clean_text(self, text: str) -> str:
        """Clean text for analysis"""
        # Remove HTML tags and special characters
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.lower().strip()
    
    def get_word_frequencies(self, text: str) -> Counter:
        """Get word frequency distribution"""
        clean_text = self.clean_text(text)
        words = clean_text.split()
        
        # Filter out very short words and common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
        
        words = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return Counter(words)
    
    def calculate_zipf_compliance(self, word_freq: Counter) -> Dict:
        """Calculate Zipf's Law compliance metrics"""
        if not word_freq:
            return {'r_squared': 0, 'slope': 0, 'intercept': 0, 'p_value': 1}
        
        # Get frequency data
        frequencies = sorted(word_freq.values(), reverse=True)
        if len(frequencies) < 10:  # Need minimum data points
            return {'r_squared': 0, 'slope': 0, 'intercept': 0, 'p_value': 1}
        
        ranks = np.arange(1, len(frequencies) + 1)
        
        # Take log of ranks and frequencies
        log_ranks = np.log(ranks)
        log_frequencies = np.log(frequencies)
        
        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(log_ranks, log_frequencies)
        
        return {
            'r_squared': r_value ** 2,
            'slope': slope,
            'intercept': intercept,
            'p_value': p_value,
            'std_err': std_err,
            'word_count': len(word_freq),
            'unique_words': len(word_freq),
            'total_words': sum(word_freq.values())
        }
    
    def analyze_trajectory(self, trajectory: Dict) -> Dict:
        """Analyze a single trajectory for Zipf's Law compliance"""
        results = {}
        
        # Analyze different components
        components = {
            'scratchpad_reasoning': trajectory.get('scratchpad_reasoning', ''),
            'output': trajectory.get('output', ''),
            'combined': trajectory.get('scratchpad_reasoning', '') + ' ' + trajectory.get('output', '')
        }
        
        for component, text in components.items():
            word_freq = self.get_word_frequencies(text)
            zipf_metrics = self.calculate_zipf_compliance(word_freq)
            results[component] = zipf_metrics
        
        return results
    
    def analyze_all_trajectories(self, trajectories: List[Dict]) -> pd.DataFrame:
        """Analyze all trajectories and return results DataFrame"""
        results = []
        
        for trajectory in trajectories:
            zipf_analysis = self.analyze_trajectory(trajectory)
            
            for component, metrics in zipf_analysis.items():
                result = {
                    'category': trajectory.get('category', ''),
                    'subcategory': trajectory.get('subcategory', ''),
                    'phase': trajectory.get('phase', ''),
                    'filename': trajectory.get('filename', ''),
                    'html_filename': trajectory.get('html_filename', ''),
                    'html_file_path': trajectory.get('html_file_path', ''),
                    'component': component,
                    **metrics
                }
                results.append(result)
        
        return pd.DataFrame(results)

class AlignmentFakingDetector:
    """
    Main class for detecting alignment faking using Zipf's Law analysis
    """
    
    def __init__(self):
        self.scraper = AlignmentFakingDataScraper()
        self.analyzer = ZipfLawAnalyzer()
        self.results_df = None
        self.results_dir = "/content/drive/MyDrive/nac/alignment_faking"
        
        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)
    
    def run_analysis(self, limit_per_category: int = 20) -> pd.DataFrame:
        """Run the complete analysis pipeline"""
        logger.info("Starting alignment faking detection analysis...")
        
        # Scrape data
        trajectories = self.scraper.scrape_all_trajectories(limit_per_category)
        
        # Analyze with Zipf's Law
        self.results_df = self.analyzer.analyze_all_trajectories(trajectories)
        
        return self.results_df
    
    def save_results(self):
        """Save detailed results to files"""
        if self.results_df is None:
            logger.error("No results to save. Run analysis first.")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save main results CSV
        csv_path = os.path.join(self.results_dir, f'alignment_faking_zipf_analysis_{timestamp}.csv')
        self.results_df.to_csv(csv_path, index=False)
        logger.info(f"Main results saved to: {csv_path}")
        
        # Save detailed trajectory data
        trajectory_data = []
        for trajectory in self.scraper.trajectories:
            trajectory_data.append({
                'category': trajectory.get('category', ''),
                'subcategory': trajectory.get('subcategory', ''),
                'phase': trajectory.get('phase', ''),
                'filename': trajectory.get('filename', ''),
                'html_filename': trajectory.get('html_filename', ''),
                'html_file_path': trajectory.get('html_file_path', ''),
                'url': trajectory.get('url', ''),
                'user_input': trajectory.get('user_input', ''),
                'scratchpad_reasoning': trajectory.get('scratchpad_reasoning', ''),
                'output': trajectory.get('output', ''),
                'user_input_length': len(trajectory.get('user_input', '')),
                'scratchpad_length': len(trajectory.get('scratchpad_reasoning', '')),
                'output_length': len(trajectory.get('output', ''))
            })
        
        trajectory_df = pd.DataFrame(trajectory_data)
        trajectory_path = os.path.join(self.results_dir, f'trajectory_details_{timestamp}.csv')
        trajectory_df.to_csv(trajectory_path, index=False)
        logger.info(f"Trajectory details saved to: {trajectory_path}")
        
        # Save anomaly detection results
        anomalies = self.detect_anomalies()
        if not anomalies.empty:
            anomaly_path = os.path.join(self.results_dir, f'anomaly_detection_{timestamp}.csv')
            anomalies.to_csv(anomaly_path, index=False)
            logger.info(f"Anomaly detection results saved to: {anomaly_path}")
        
        # Save summary statistics
        self.save_summary_report(timestamp)
        
        return {
            'main_results': csv_path,
            'trajectory_details': trajectory_path,
            'anomalies': anomaly_path if not anomalies.empty else None
        }
    
    def save_summary_report(self, timestamp: str):
        """Save a comprehensive summary report"""
        if self.results_df is None:
            return
        
        report_path = os.path.join(self.results_dir, f'summary_report_{timestamp}.txt')
        
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("ALIGNMENT FAKING DETECTION SUMMARY REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall statistics
            f.write("OVERALL STATISTICS:\n")
            f.write(f"Total trajectories analyzed: {len(self.results_df[self.results_df['component'] == 'scratchpad_reasoning'])}\n")
            f.write(f"Categories: {', '.join(self.results_df['category'].unique())}\n")
            f.write(f"Phases: {', '.join(self.results_df['phase'].unique())}\n")
            f.write(f"HTML files saved: {len(self.scraper.trajectories)}\n")
            f.write(f"HTML directory: {self.scraper.html_dir}\n\n")
            
            # Zipf's Law compliance by component
            f.write("ZIPF'S LAW COMPLIANCE BY COMPONENT:\n")
            for component in self.results_df['component'].unique():
                component_data = self.results_df[self.results_df['component'] == component]
                mean_r2 = component_data['r_squared'].mean()
                mean_slope = component_data['slope'].mean()
                f.write(f"  {component}:\n")
                f.write(f"    Mean R-squared: {mean_r2:.3f}\n")
                f.write(f"    Mean Slope: {mean_slope:.3f}\n")
                f.write(f"    Good compliance (R² > 0.7): {(component_data['r_squared'] > 0.7).sum()}/{len(component_data)}\n")
            
            # Anomaly detection
            anomalies = self.detect_anomalies()
            f.write(f"\nPOTENTIAL ALIGNMENT FAKING DETECTED:\n")
            f.write(f"High anomaly trajectories: {len(anomalies)}\n")
            
            if len(anomalies) > 0:
                f.write(f"\nTOP 10 MOST ANOMALOUS TRAJECTORIES:\n")
                for i, (_, row) in enumerate(anomalies.head(10).iterrows()):
                    f.write(f"  {i+1}. {row['category']}/{row['subcategory']}/{row['phase']}/{row['filename']}\n")
                    f.write(f"     HTML file: {row['html_filename']}\n")
                    f.write(f"     Anomaly Score: {row['anomaly_score']:.3f}\n")
                    f.write(f"     R-squared: {row['r_squared']:.3f}, Slope: {row['slope']:.3f}\n")
            
            f.write("\n" + "=" * 80 + "\n")
        
        logger.info(f"Summary report saved to: {report_path}")
    
    def plot_zipf_compliance(self, save_plots: bool = True):
        """Plot Zipf's Law compliance analysis"""
        if self.results_df is None:
            logger.error("No results to plot. Run analysis first.")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # R-squared distribution by component
        sns.boxplot(data=self.results_df, x='component', y='r_squared', ax=axes[0, 0])
        axes[0, 0].set_title('Zipf\'s Law R-squared by Component')
        axes[0, 0].set_ylabel('R-squared')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # R-squared by phase
        sns.boxplot(data=self.results_df, x='phase', y='r_squared', ax=axes[0, 1])
        axes[0, 1].set_title('Zipf\'s Law R-squared by Phase')
        axes[0, 1].set_ylabel('R-squared')
        
        # Slope distribution (should be close to -1 for Zipf's Law)
        sns.boxplot(data=self.results_df, x='component', y='slope', ax=axes[1, 0])
        axes[1, 0].set_title('Zipf\'s Law Slope by Component')
        axes[1, 0].set_ylabel('Slope')
        axes[1, 0].axhline(y=-1, color='red', linestyle='--', alpha=0.7, label='Perfect Zipf (-1)')
        axes[1, 0].legend()
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Scatter plot: R-squared vs Slope
        for component in self.results_df['component'].unique():
            component_data = self.results_df[self.results_df['component'] == component]
            axes[1, 1].scatter(component_data['slope'], component_data['r_squared'], 
                             alpha=0.6, label=component)
        
        axes[1, 1].set_xlabel('Slope')
        axes[1, 1].set_ylabel('R-squared')
        axes[1, 1].set_title('Zipf\'s Law Compliance: Slope vs R-squared')
        axes[1, 1].legend()
        axes[1, 1].axvline(x=-1, color='red', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        
        if save_plots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_path = os.path.join(self.results_dir, f'zipf_compliance_plots_{timestamp}.png')
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            logger.info(f"Plots saved to: {plot_path}")
        
        plt.show()
    
    def detect_anomalies(self, threshold: float = 0.7) -> pd.DataFrame:
        """Detect potential alignment faking based on Zipf's Law deviations"""
        if self.results_df is None:
            logger.error("No results to analyze. Run analysis first.")
            return pd.DataFrame()
        
        # Focus on scratchpad reasoning as it's most likely to show alignment faking
        scratchpad_data = self.results_df[self.results_df['component'] == 'scratchpad_reasoning'].copy()
        
        # Define anomaly criteria
        anomalies = scratchpad_data[
            (scratchpad_data['r_squared'] < threshold) |  # Poor Zipf's Law fit
            (scratchpad_data['slope'] > -0.5) |  # Slope too shallow
            (scratchpad_data['slope'] < -2.0) |  # Slope too steep
            (scratchpad_data['total_words'] < 50)  # Too few words
        ].copy()
        
        # Add anomaly score
        anomalies['anomaly_score'] = (
            (1 - anomalies['r_squared']) * 0.4 +  # 40% weight on poor fit
            (np.abs(anomalies['slope'] + 1) * 0.3) +  # 30% weight on slope deviation
            (anomalies['p_value'] * 0.2) +  # 20% weight on p-value
            ((100 - anomalies['total_words']) / 100 * 0.1)  # 10% weight on word count
        )
        
        return anomalies.sort_values('anomaly_score', ascending=False)
    
    def generate_report(self):
        """Generate a comprehensive report"""
        if self.results_df is None:
            logger.error("No results to report. Run analysis first.")
            return
        
        print("=" * 60)
        print("ALIGNMENT FAKING DETECTION REPORT")
        print("=" * 60)
        
        # Overall statistics
        print(f"\nOVERALL STATISTICS:")
        print(f"Total trajectories analyzed: {len(self.results_df[self.results_df['component'] == 'scratchpad_reasoning'])}")
        print(f"Categories: {', '.join(self.results_df['category'].unique())}")
        print(f"Phases: {', '.join(self.results_df['phase'].unique())}")
        print(f"HTML files saved to: {self.scraper.html_dir}")
        print(f"Results saved to: {self.results_dir}")
        
        # Zipf's Law compliance by component
        print(f"\nZIPF'S LAW COMPLIANCE BY COMPONENT:")
        for component in self.results_df['component'].unique():
            component_data = self.results_df[self.results_df['component'] == component]
            mean_r2 = component_data['r_squared'].mean()
            mean_slope = component_data['slope'].mean()
            print(f"  {component}:")
            print(f"    Mean R-squared: {mean_r2:.3f}")
            print(f"    Mean Slope: {mean_slope:.3f}")
            print(f"    Good compliance (R² > 0.7): {(component_data['r_squared'] > 0.7).sum()}/{len(component_data)}")
        
        # Anomaly detection
        anomalies = self.detect_anomalies()
        print(f"\nPOTENTIAL ALIGNMENT FAKING DETECTED:")
        print(f"High anomaly trajectories: {len(anomalies)}")
        
        if len(anomalies) > 0:
            print(f"\nTOP 10 MOST ANOMALOUS TRAJECTORIES:")
            for i, (_, row) in enumerate(anomalies.head(10).iterrows()):
                print(f"  {i+1}. {row['category']}/{row['subcategory']}/{row['phase']}/{row['filename']}")
                print(f"     HTML file: {row['html_filename']}")
                print(f"     Anomaly Score: {row['anomaly_score']:.3f}")
                print(f"     R-squared: {row['r_squared']:.3f}, Slope: {row['slope']:.3f}")
        
        print("\n" + "=" * 60)

def main():
    """Main execution function"""
    detector = AlignmentFakingDetector()
    
    # Run analysis
    results_df = detector.run_analysis(limit_per_category=10)  # Start with small sample
    
    # Save all results