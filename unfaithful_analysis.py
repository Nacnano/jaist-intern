import json
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import re
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any
import argparse
from pathlib import Path
import textwrap

class UnfaithfulReasoningAnalyzer:
    """
    Comprehensive analyzer for unfaithful reasoning patterns in Chain-of-Thought evaluations.
    
    This class provides detailed analysis of:
    1. Unfaithful reasoning cases
    2. Hidden CoT patterns
    3. Model-specific failure modes
    4. Dataset-specific reasoning issues
    5. Edge cases and interesting examples
    """
    
    def __init__(self, results_file: str):
        """
        Initialize the analyzer with evaluation results.
        
        Args:
            results_file (str): Path to the evaluation_results.jsonl file
        """
        self.results_file = results_file
        self.data = []
        self.df = None
        self.unfaithful_cases = []
        self.hidden_cot_cases = []
        self.faithful_cases = []
        self.load_data()
        self.categorize_cases()
    
    def load_data(self):
        """Load and parse the JSONL evaluation results file."""
        print(f"Loading data from {self.results_file}...")
        
        if not Path(self.results_file).exists():
            raise FileNotFoundError(f"Results file not found: {self.results_file}")
        
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            self.data.append(record)
                        except json.JSONDecodeError as e:
                            print(f"Warning: Skipping malformed JSON on line {line_num}: {e}")
            
            self.df = pd.DataFrame(self.data)
            print(f"Successfully loaded {len(self.data)} evaluation records.")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
    
    def categorize_cases(self):
        """Categorize cases based on faithfulness verdicts."""
        print("Categorizing cases by faithfulness verdict...")
        
        for record in self.data:
            verdict = record.get('faithfulness_judgment', {}).get('faithfulness_verdict', 'unknown')
            
            if verdict == 'unfaithful_reasoning':
                self.unfaithful_cases.append(record)
            elif verdict == 'hidden_cot':
                self.hidden_cot_cases.append(record)
            elif verdict == 'faithful':
                self.faithful_cases.append(record)
        
        print(f"Found {len(self.unfaithful_cases)} unfaithful reasoning cases")
        print(f"Found {len(self.hidden_cot_cases)} hidden CoT cases")
        print(f"Found {len(self.faithful_cases)} faithful cases")
    
    def generate_summary_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive summary statistics."""
        print("\nGenerating summary statistics...")
        
        stats = {
            'total_cases': len(self.data),
            'by_verdict': {},
            'by_model': defaultdict(lambda: defaultdict(int)),
            'by_dataset': defaultdict(lambda: defaultdict(int)),
            'accuracy_stats': {},
            'reasoning_quality': {}
        }
        
        # Verdict distribution
        verdict_counts = Counter()
        for record in self.data:
            verdict = record.get('faithfulness_judgment', {}).get('faithfulness_verdict', 'unknown')
            verdict_counts[verdict] += 1
        
        stats['by_verdict'] = dict(verdict_counts)
        
        # Model performance breakdown
        for record in self.data:
            model = record.get('model_id', 'unknown')
            verdict = record.get('faithfulness_judgment', {}).get('faithfulness_verdict', 'unknown')
            is_correct = record.get('is_answer_correct', False)
            
            stats['by_model'][model][verdict] += 1
            stats['by_model'][model]['total'] += 1
            if is_correct:
                stats['by_model'][model]['correct_answers'] += 1
        
        # Dataset performance breakdown
        for record in self.data:
            dataset = record.get('dataset_id', 'unknown')
            verdict = record.get('faithfulness_judgment', {}).get('faithfulness_verdict', 'unknown')
            is_correct = record.get('is_answer_correct', False)
            
            stats['by_dataset'][dataset][verdict] += 1
            stats['by_dataset'][dataset]['total'] += 1
            if is_correct:
                stats['by_dataset'][dataset]['correct_answers'] += 1
        
        return stats
    
    def analyze_unfaithful_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in unfaithful reasoning cases."""
        print("\nAnalyzing unfaithful reasoning patterns...")
        
        patterns = {
            'common_error_types': [],
            'reasoning_length_analysis': {},
            'mathematical_errors': [],
            'logical_fallacies': [],
            'examples_by_severity': {'high': [], 'medium': [], 'low': []}
        }
        
        reasoning_lengths = []
        error_keywords = [
            'mathematical error', 'calculation error', 'logical error', 'incorrect step',
            'wrong assumption', 'faulty logic', 'contradiction', 'inconsistent'
        ]
        
        for case in self.unfaithful_cases:
            reasoning = case.get('parsed_reasoning', '')
            explanation = case.get('faithfulness_judgment', {}).get('explanation', '')
            
            # Analyze reasoning length
            word_count = len(reasoning.split())
            reasoning_lengths.append(word_count)
            
            # Look for error indicators in explanations
            explanation_lower = explanation.lower()
            for keyword in error_keywords:
                if keyword in explanation_lower:
                    patterns['common_error_types'].append({
                        'keyword': keyword,
                        'case': case,
                        'explanation': explanation
                    })
            
            # Categorize by severity (based on explanation content)
            if any(severe in explanation_lower for severe in ['major error', 'completely wrong', 'fundamental flaw']):
                patterns['examples_by_severity']['high'].append(case)
            elif any(moderate in explanation_lower for moderate in ['minor error', 'small mistake', 'slight']):
                patterns['examples_by_severity']['low'].append(case)
            else:
                patterns['examples_by_severity']['medium'].append(case)
        
        patterns['reasoning_length_analysis'] = {
            'mean': np.mean(reasoning_lengths) if reasoning_lengths else 0,
            'median': np.median(reasoning_lengths) if reasoning_lengths else 0,
            'std': np.std(reasoning_lengths) if reasoning_lengths else 0,
            'min': min(reasoning_lengths) if reasoning_lengths else 0,
            'max': max(reasoning_lengths) if reasoning_lengths else 0
        }
        
        return patterns
    
    def analyze_hidden_cot_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in hidden CoT cases."""
        print("\nAnalyzing hidden CoT patterns...")
        
        patterns = {
            'lucky_guesses': [],
            'shortcut_reasoning': [],
            'incomplete_but_correct': [],
            'reasoning_vs_answer_mismatch': []
        }
        
        for case in self.hidden_cot_cases:
            reasoning = case.get('parsed_reasoning', '').lower()
            explanation = case.get('faithfulness_judgment', {}).get('explanation', '').lower()
            
            # Categorize hidden CoT types based on explanation
            if any(term in explanation for term in ['lucky', 'coincidence', 'guess']):
                patterns['lucky_guesses'].append(case)
            elif any(term in explanation for term in ['shortcut', 'skip', 'jump']):
                patterns['shortcut_reasoning'].append(case)
            elif any(term in explanation for term in ['incomplete', 'partial', 'missing']):
                patterns['incomplete_but_correct'].append(case)
            else:
                patterns['reasoning_vs_answer_mismatch'].append(case)
        
        return patterns
    
    def find_edge_cases(self, top_k: int = 10) -> Dict[str, List[Dict]]:
        """Find the most interesting edge cases for further analysis."""
        print(f"\nFinding top {top_k} edge cases...")
        
        edge_cases = {
            'most_unfaithful': [],
            'most_surprising_hidden_cot': [],
            'longest_unfaithful_reasoning': [],
            'shortest_hidden_cot': [],
            'model_specific_failures': [],
            'dataset_specific_issues': []
        }
        
        # Most unfaithful (based on explanation severity)
        unfaithful_scored = []
        for case in self.unfaithful_cases:
            explanation = case.get('faithfulness_judgment', {}).get('explanation', '').lower()
            severity_score = 0
            
            # Score based on severity indicators
            severity_indicators = {
                'completely wrong': 5, 'major error': 4, 'fundamental flaw': 4,
                'significant error': 3, 'logical fallacy': 3, 'contradiction': 3,
                'minor error': 1, 'small mistake': 1
            }
            
            for indicator, score in severity_indicators.items():
                if indicator in explanation:
                    severity_score += score
            
            unfaithful_scored.append((severity_score, case))
        
        unfaithful_scored.sort(reverse=True, key=lambda x: x[0])
        edge_cases['most_unfaithful'] = [case for _, case in unfaithful_scored[:top_k]]
        
        # Most surprising hidden CoT
        hidden_cot_scored = []
        for case in self.hidden_cot_cases:
            reasoning = case.get('parsed_reasoning', '')
            reasoning_length = len(reasoning.split())
            
            # Score based on reasoning length vs correctness surprise
            surprise_score = max(0, 50 - reasoning_length)  # Shorter reasoning = more surprising
            hidden_cot_scored.append((surprise_score, case))
        
        hidden_cot_scored.sort(reverse=True, key=lambda x: x[0])
        edge_cases['most_surprising_hidden_cot'] = [case for _, case in hidden_cot_scored[:top_k]]
        
        # Longest unfaithful reasoning
        unfaithful_by_length = sorted(
            self.unfaithful_cases,
            key=lambda x: len(x.get('parsed_reasoning', '').split()),
            reverse=True
        )
        edge_cases['longest_unfaithful_reasoning'] = unfaithful_by_length[:top_k]
        
        # Shortest hidden CoT
        hidden_cot_by_length = sorted(
            self.hidden_cot_cases,
            key=lambda x: len(x.get('parsed_reasoning', '').split())
        )
        edge_cases['shortest_hidden_cot'] = hidden_cot_by_length[:top_k]
        
        return edge_cases
    
    def create_detailed_report(self, output_file: str = "unfaithful_analysis_report.txt"):
        """Create a comprehensive text report of the analysis."""
        print(f"\nGenerating detailed report: {output_file}")
        
        stats = self.generate_summary_statistics()
        unfaithful_patterns = self.analyze_unfaithful_patterns()
        hidden_cot_patterns = self.analyze_hidden_cot_patterns()
        edge_cases = self.find_edge_cases()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("UNFAITHFUL REASONING ANALYSIS REPORT\n")
            f.write("="*80 + "\n\n")
            
            # Summary Statistics
            f.write("1. SUMMARY STATISTICS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total evaluation cases: {stats['total_cases']}\n\n")
            
            f.write("Faithfulness Verdict Distribution:\n")
            for verdict, count in stats['by_verdict'].items():
                percentage = (count / stats['total_cases']) * 100
                f.write(f"  {verdict}: {count} ({percentage:.1f}%)\n")
            f.write("\n")
            
            # Model Performance
            f.write("2. MODEL PERFORMANCE BREAKDOWN\n")
            f.write("-" * 40 + "\n")
            for model, metrics in stats['by_model'].items():
                f.write(f"\nModel: {model}\n")
                total = metrics['total']
                for verdict, count in metrics.items():
                    if verdict != 'total':
                        percentage = (count / total) * 100 if total > 0 else 0
                        f.write(f"  {verdict}: {count} ({percentage:.1f}%)\n")
            f.write("\n")
            
            # Dataset Analysis
            f.write("3. DATASET ANALYSIS\n")
            f.write("-" * 40 + "\n")
            for dataset, metrics in stats['by_dataset'].items():
                f.write(f"\nDataset: {dataset}\n")
                total = metrics['total']
                for verdict, count in metrics.items():
                    if verdict != 'total':
                        percentage = (count / total) * 100 if total > 0 else 0
                        f.write(f"  {verdict}: {count} ({percentage:.1f}%)\n")
            f.write("\n")
            
            # Unfaithful Patterns
            f.write("4. UNFAITHFUL REASONING PATTERNS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total unfaithful cases: {len(self.unfaithful_cases)}\n\n")
            
            lengths = unfaithful_patterns['reasoning_length_analysis']
            f.write("Reasoning Length Statistics:\n")
            f.write(f"  Mean: {lengths['mean']:.1f} words\n")
            f.write(f"  Median: {lengths['median']:.1f} words\n")
            f.write(f"  Std Dev: {lengths['std']:.1f} words\n")
            f.write(f"  Range: {lengths['min']}-{lengths['max']} words\n\n")
            
            # Hidden CoT Patterns
            f.write("5. HIDDEN CHAIN-OF-THOUGHT PATTERNS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total hidden CoT cases: {len(self.hidden_cot_cases)}\n\n")
            
            for pattern_type, cases in hidden_cot_patterns.items():
                f.write(f"{pattern_type.replace('_', ' ').title()}: {len(cases)} cases\n")
            f.write("\n")
            
            # Edge Cases
            f.write("6. EDGE CASES AND EXAMPLES\n")
            f.write("-" * 40 + "\n")
            
            # Most unfaithful examples
            f.write("6.1 MOST UNFAITHFUL REASONING EXAMPLES\n")
            f.write("-" * 30 + "\n")
            for i, case in enumerate(edge_cases['most_unfaithful'][:5], 1):
                f.write(f"\nExample {i}:\n")
                f.write(f"Model: {case.get('model_id', 'Unknown')}\n")
                f.write(f"Dataset: {case.get('dataset_id', 'Unknown')}\n")
                f.write(f"Question: {textwrap.fill(case.get('question', 'N/A'), width=70)}\n")
                f.write(f"Ground Truth: {case.get('ground_truth_answer', 'N/A')}\n")
                f.write(f"Model Answer: {case.get('parsed_answer', 'N/A')}\n")
                f.write(f"Reasoning: {textwrap.fill(case.get('parsed_reasoning', 'N/A')[:200], width=70)}...\n")
                f.write(f"Judge Explanation: {case.get('faithfulness_judgment', {}).get('explanation', 'N/A')}\n")
                f.write("-" * 50 + "\n")
            
            # Hidden CoT examples
            f.write("\n6.2 MOST SURPRISING HIDDEN COT EXAMPLES\n")
            f.write("-" * 30 + "\n")
            for i, case in enumerate(edge_cases['most_surprising_hidden_cot'][:5], 1):
                f.write(f"\nExample {i}:\n")
                f.write(f"Model: {case.get('model_id', 'Unknown')}\n")
                f.write(f"Dataset: {case.get('dataset_id', 'Unknown')}\n")
                f.write(f"Question: {textwrap.fill(case.get('question', 'N/A'), width=70)}\n")
                f.write(f"Ground Truth: {case.get('ground_truth_answer', 'N/A')}\n")
                f.write(f"Model Answer: {case.get('parsed_answer', 'N/A')}\n")
                f.write(f"Reasoning: {textwrap.fill(case.get('parsed_reasoning', 'N/A'), width=70)}\n")
                f.write(f"Judge Explanation: {case.get('faithfulness_judgment', {}).get('explanation', 'N/A')}\n")
                f.write("-" * 50 + "\n")
        
        print(f"Report generated successfully: {output_file}")
    
    def export_edge_cases_json(self, output_file: str = "edge_cases.json"):
        """Export edge cases to JSON for further analysis."""
        print(f"\nExporting edge cases to: {output_file}")
        
        edge_cases = self.find_edge_cases(top_k=20)
        
        # Convert to serializable format
        serializable_edge_cases = {}
        for category, cases in edge_cases.items():
            serializable_edge_cases[category] = cases
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_edge_cases, f, indent=2, ensure_ascii=False)
        
        print(f"Edge cases exported successfully: {output_file}")
    
    def create_visualizations(self, output_dir: str = "visualizations"):
        """Create visualizations for the analysis."""
        print(f"\nCreating visualizations in: {output_dir}")
        
        Path(output_dir).mkdir(exist_ok=True)
        
        # Set style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # 1. Faithfulness verdict distribution
        verdict_counts = Counter()
        for record in self.data:
            verdict = record.get('faithfulness_judgment', {}).get('faithfulness_verdict', 'unknown')
            verdict_counts[verdict] += 1
        
        plt.figure(figsize=(10, 6))
        verdicts, counts = zip(*verdict_counts.items())
        plt.bar(verdicts, counts)
        plt.title('Distribution of Faithfulness Verdicts')
        plt.xlabel('Verdict')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/faithfulness_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Model performance heatmap
        models = list(set(record.get('model_id', 'unknown') for record in self.data))
        verdicts = list(verdict_counts.keys())
        
        heatmap_data = []
        for model in models:
            row = []
            for verdict in verdicts:
                count = sum(1 for record in self.data 
                           if record.get('model_id') == model and 
                           record.get('faithfulness_judgment', {}).get('faithfulness_verdict') == verdict)
                row.append(count)
            heatmap_data.append(row)
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(heatmap_data, xticklabels=verdicts, yticklabels=models, 
                   annot=True, fmt='d', cmap='YlOrRd')
        plt.title('Model Performance Heatmap')
        plt.xlabel('Faithfulness Verdict')
        plt.ylabel('Model')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/model_performance_heatmap.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Reasoning length distribution
        reasoning_lengths = []
        verdicts_for_lengths = []
        
        for record in self.data:
            reasoning = record.get('parsed_reasoning', '')
            length = len(reasoning.split())
            verdict = record.get('faithfulness_judgment', {}).get('faithfulness_verdict', 'unknown')
            
            reasoning_lengths.append(length)
            verdicts_for_lengths.append(verdict)
        
        plt.figure(figsize=(12, 6))
        df_lengths = pd.DataFrame({'length': reasoning_lengths, 'verdict': verdicts_for_lengths})
        sns.boxplot(data=df_lengths, x='verdict', y='length')
        plt.title('Reasoning Length Distribution by Faithfulness Verdict')
        plt.xlabel('Faithfulness Verdict')
        plt.ylabel('Reasoning Length (words)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/reasoning_length_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Visualizations created successfully in: {output_dir}")
    
    def interactive_case_explorer(self):
        """Interactive explorer for examining specific cases."""
        print("\n" + "="*60)
        print("INTERACTIVE CASE EXPLORER")
        print("="*60)
        print("Commands:")
        print("  'unfaithful' - Browse unfaithful reasoning cases")
        print("  'hidden' - Browse hidden CoT cases")
        print("  'model [model_name]' - Filter by specific model")
        print("  'dataset [dataset_name]' - Filter by specific dataset")
        print("  'stats' - Show summary statistics")
        print("  'quit' - Exit explorer")
        print("-" * 60)
        
        current_cases = self.data.copy()
        
        while True:
            command = input("\nEnter command: ").strip().lower()
            
            if command == 'quit':
                break
            elif command == 'unfaithful':
                current_cases = self.unfaithful_cases
                print(f"Showing {len(current_cases)} unfaithful reasoning cases")
                self._display_cases_summary(current_cases[:5])
            elif command == 'hidden':
                current_cases = self.hidden_cot_cases
                print(f"Showing {len(current_cases)} hidden CoT cases")
                self._display_cases_summary(current_cases[:5])
            elif command.startswith('model '):
                model_name = command[6:].strip()
                filtered_cases = [c for c in current_cases if model_name in c.get('model_id', '').lower()]
                current_cases = filtered_cases
                print(f"Filtered to {len(current_cases)} cases for model containing '{model_name}'")
                self._display_cases_summary(current_cases[:5])
            elif command.startswith('dataset '):
                dataset_name = command[8:].strip()
                filtered_cases = [c for c in current_cases if dataset_name in c.get('dataset_id', '').lower()]
                current_cases = filtered_cases
                print(f"Filtered to {len(current_cases)} cases for dataset containing '{dataset_name}'")
                self._display_cases_summary(current_cases[:5])
            elif command == 'stats':
                self._show_quick_stats(current_cases)
            else:
                print("Unknown command. Type 'quit' to exit.")
    
    def _display_cases_summary(self, cases: List[Dict], max_cases: int = 5):
        """Display a summary of cases."""
        for i, case in enumerate(cases[:max_cases], 1):
            print(f"\n--- Case {i} ---")
            print(f"Model: {case.get('model_id', 'Unknown')}")
            print(f"Dataset: {case.get('dataset_id', 'Unknown')}")
            print(f"Question: {textwrap.fill(case.get('question', 'N/A')[:100], width=60)}...")
            print(f"Verdict: {case.get('faithfulness_judgment', {}).get('faithfulness_verdict', 'Unknown')}")
            print(f"Explanation: {textwrap.fill(case.get('faithfulness_judgment', {}).get('explanation', 'N/A'), width=60)}")
    
    def _show_quick_stats(self, cases: List[Dict]):
        """Show quick statistics for current cases."""
        if not cases:
            print("No cases to analyze.")
            return
        
        verdict_counts = Counter()
        model_counts = Counter()
        dataset_counts = Counter()
        
        for case in cases:
            verdict = case.get('faithfulness_judgment', {}).get('faithfulness_verdict', 'unknown')
            model = case.get('model_id', 'unknown')
            dataset = case.get('dataset_id', 'unknown')
            
            verdict_counts[verdict] += 1
            model_counts[model] += 1
            dataset_counts[dataset] += 1
        
        print(f"\nQuick Stats for {len(cases)} cases:")
        print(f"Verdicts: {dict(verdict_counts)}")
        print(f"Top models: {dict(model_counts.most_common(3))}")
        print(f"Top datasets: {dict(dataset_counts.most_common(3))}")


def main():
    """Main function to run the analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze unfaithful reasoning patterns in Chain-of-Thought evaluations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python unfaithful_analysis.py evaluation_results.jsonl
  python unfaithful_analysis.py results.jsonl --interactive
  python unfaithful_analysis.py results.jsonl --output-dir analysis_output
        """
    )
    
    parser.add_argument('results_file', help='Path to evaluation results JSONL file')
    parser.add_argument('--output-dir', default='analysis_output', 
                       help='Output directory for reports and visualizations')
    parser.add_argument('--interactive', action='store_true',
                       help='Launch interactive case explorer')
    parser.add_argument('--skip-viz', action='store_true',
                       help='Skip generating visualizations (useful if matplotlib not available)')
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = UnfaithfulReasoningAnalyzer(args.results_file)
        
        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Generate comprehensive report
        report_file = output_dir / "unfaithful_analysis_report.txt"
        analyzer.create_detailed_report(str(report_file))
        
        # Export edge cases
        edge_cases_file = output_dir / "edge_cases.json"
        analyzer.export_edge_cases_json(str(edge_cases_file))
        
        # Create visualizations (if not skipped)
        if not args.skip_viz:
            try:
                viz_dir = output_dir / "visualizations"
                analyzer.create_visualizations(str(viz_dir))
            except ImportError:
                print("Warning: Matplotlib/Seaborn not available. Skipping visualizations.")
                print("Install with: pip install matplotlib seaborn")
        
        # Launch interactive explorer if requested
        if args.interactive:
            analyzer.interactive_case_explorer()
        
        print(f"\nAnalysis complete! Results saved to: {output_dir}")
        print(f"Key files:")
        print(f"  - Detailed report: {report_file}")
        print(f"  - Edge cases: {edge_cases_file}")
        if not args.skip_viz:
            print(f"  - Visualizations: {output_dir}/visualizations/")
    
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())