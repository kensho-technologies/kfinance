"""Evaluation framework for testing dynamic prompt construction improvements."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from kfinance.client.permission_models import Permission
from .integration import DynamicPromptManager

logger = logging.getLogger(__name__)


@dataclass
class EvaluationCase:
    """Represents a single evaluation test case."""
    
    query: str
    expected_tool: str
    expected_parameters: Dict[str, any]
    description: str
    difficulty: str = "medium"  # easy, medium, hard
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "query": self.query,
            "expected_tool": self.expected_tool,
            "expected_parameters": self.expected_parameters,
            "description": self.description,
            "difficulty": self.difficulty,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> "EvaluationCase":
        """Create from dictionary."""
        return cls(
            query=data["query"],
            expected_tool=data["expected_tool"],
            expected_parameters=data["expected_parameters"],
            description=data["description"],
            difficulty=data.get("difficulty", "medium"),
            tags=data.get("tags", []),
        )


@dataclass
class EvaluationResult:
    """Results from evaluating a single test case."""
    
    case: EvaluationCase
    prompt_used: str
    prompt_stats: Dict[str, any]
    parameter_accuracy: Dict[str, bool]
    overall_accuracy: float
    similarity_scores: List[Tuple[str, float]]
    execution_time_ms: float
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "case": self.case.to_dict(),
            "prompt_stats": self.prompt_stats,
            "parameter_accuracy": self.parameter_accuracy,
            "overall_accuracy": self.overall_accuracy,
            "similarity_scores": self.similarity_scores,
            "execution_time_ms": self.execution_time_ms,
        }


class DynamicPromptEvaluator:
    """Evaluator for testing dynamic prompt construction improvements."""
    
    def __init__(
        self,
        manager: Optional[DynamicPromptManager] = None,
        test_cases_file: Optional[Path] = None,
    ):
        """Initialize the evaluator.
        
        Args:
            manager: Dynamic prompt manager to test
            test_cases_file: Path to JSON file containing test cases
        """
        self.manager = manager or DynamicPromptManager()
        self.test_cases_file = test_cases_file or self._get_default_test_cases_file()
        self.test_cases: List[EvaluationCase] = []
        
        # Load test cases
        self._load_test_cases()
    
    def _get_default_test_cases_file(self) -> Path:
        """Get default test cases file path."""
        return Path(__file__).parent / "evaluation_cases.json"
    
    def _load_test_cases(self) -> None:
        """Load test cases from JSON file."""
        if not self.test_cases_file.exists():
            logger.warning(f"Test cases file not found: {self.test_cases_file}")
            self._create_default_test_cases()
            return
        
        try:
            with open(self.test_cases_file, 'r') as f:
                data = json.load(f)
            
            for case_data in data.get("test_cases", []):
                case = EvaluationCase.from_dict(case_data)
                self.test_cases.append(case)
            
            logger.info(f"Loaded {len(self.test_cases)} test cases")
            
        except Exception as e:
            logger.error(f"Failed to load test cases: {e}")
            self._create_default_test_cases()
    
    def _create_default_test_cases(self) -> None:
        """Create default test cases based on the eval failures from the design doc."""
        default_cases = [
            EvaluationCase(
                query="What is the preferred stock additional paid in capital for Apple?",
                expected_tool="get_financial_line_item_from_identifiers",
                expected_parameters={
                    "identifiers": ["AAPL"],
                    "line_item": "additional_paid_in_capital_preferred_stock"
                },
                description="Test disambiguation between similar preferred stock parameters",
                difficulty="hard",
                tags=["preferred_stock", "disambiguation", "capital"]
            ),
            EvaluationCase(
                query="Show me the convertible preferred stock for Tesla",
                expected_tool="get_financial_line_item_from_identifiers",
                expected_parameters={
                    "identifiers": ["TSLA"],
                    "line_item": "preferred_stock_convertible"
                },
                description="Test correct parameter order for convertible preferred stock",
                difficulty="hard",
                tags=["preferred_stock", "convertible", "disambiguation"]
            ),
            EvaluationCase(
                query="What are the preferred dividends paid by Microsoft?",
                expected_tool="get_financial_line_item_from_identifiers",
                expected_parameters={
                    "identifiers": ["MSFT"],
                    "line_item": "preferred_stock_dividend"
                },
                description="Test preferred dividend parameter naming",
                difficulty="hard",
                tags=["preferred_stock", "dividends", "disambiguation"]
            ),
            EvaluationCase(
                query="Get the total revenue for Google and Amazon",
                expected_tool="get_financial_line_item_from_identifiers",
                expected_parameters={
                    "identifiers": ["GOOGL", "AMZN"],
                    "line_item": "total_revenue"
                },
                description="Test total vs regular revenue distinction",
                difficulty="medium",
                tags=["revenue", "total", "multiple_companies"]
            ),
            EvaluationCase(
                query="Show me the total debt to equity ratio for JPMorgan",
                expected_tool="get_financial_line_item_from_identifiers",
                expected_parameters={
                    "identifiers": ["JPM"],
                    "line_item": "total_debt_to_equity"
                },
                description="Test debt to equity parameter without 'ratio' suffix",
                difficulty="hard",
                tags=["debt", "equity", "ratio", "disambiguation"]
            ),
            EvaluationCase(
                query="Get depreciation and amortization for Ford over the last 3 years",
                expected_tool="get_financial_line_item_from_identifiers",
                expected_parameters={
                    "identifiers": ["F"],
                    "line_item": "total_depreciation_and_amortization",
                    "start_year": 2021,
                    "end_year": 2023
                },
                description="Test total prefix requirement and time range",
                difficulty="medium",
                tags=["depreciation", "amortization", "total", "time_range"]
            ),
            EvaluationCase(
                query="Show me the total receivables for Coca-Cola",
                expected_tool="get_financial_line_item_from_identifiers",
                expected_parameters={
                    "identifiers": ["KO"],
                    "line_item": "total_receivable"
                },
                description="Test singular vs plural parameter naming",
                difficulty="hard",
                tags=["receivables", "total", "singular_form"]
            ),
            EvaluationCase(
                query="Get quarterly revenue for Apple in Q1 2023",
                expected_tool="get_financial_line_item_from_identifiers",
                expected_parameters={
                    "identifiers": ["AAPL"],
                    "line_item": "revenue",
                    "period_type": "quarterly",
                    "start_year": 2023,
                    "start_quarter": 1,
                    "end_year": 2023,
                    "end_quarter": 1
                },
                description="Test quarterly period specification",
                difficulty="medium",
                tags=["quarterly", "revenue", "specific_period"]
            ),
        ]
        
        self.test_cases = default_cases
        
        # Save default cases to file
        self._save_test_cases()
    
    def _save_test_cases(self) -> None:
        """Save test cases to JSON file."""
        data = {
            "description": "Evaluation test cases for dynamic prompt construction",
            "test_cases": [case.to_dict() for case in self.test_cases]
        }
        
        try:
            with open(self.test_cases_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.test_cases)} test cases to {self.test_cases_file}")
        except Exception as e:
            logger.error(f"Failed to save test cases: {e}")
    
    def evaluate_case(
        self,
        case: EvaluationCase,
        user_permissions: Set[Permission],
    ) -> EvaluationResult:
        """Evaluate a single test case.
        
        Args:
            case: Test case to evaluate
            user_permissions: User permissions for the test
            
        Returns:
            Evaluation result
        """
        import time
        
        start_time = time.time()
        
        # Get dynamic prompt and stats
        prompt, stats = self.manager.get_prompt_with_stats(
            query=case.query,
            user_permissions=user_permissions,
        )
        
        # Get similarity scores for analysis
        similar_examples = self.manager.search_similar_examples(
            query=case.query,
            user_permissions=user_permissions,
            top_k=5,
        )
        
        similarity_scores = [
            (example["query"], example["similarity_score"])
            for example in similar_examples
        ]
        
        # Evaluate parameter accuracy
        parameter_accuracy = {}
        correct_params = 0
        total_params = len(case.expected_parameters)
        
        # This is a simplified evaluation - in practice, you'd need to actually
        # run the LLM with the prompt and compare the generated parameters
        for param_name, expected_value in case.expected_parameters.items():
            # For now, we'll check if relevant examples contain the correct parameter
            has_correct_example = any(
                param_name in str(example.get("parameters", {})) and
                expected_value in str(example.get("parameters", {}).get(param_name, ""))
                for example in similar_examples
            )
            parameter_accuracy[param_name] = has_correct_example
            if has_correct_example:
                correct_params += 1
        
        overall_accuracy = correct_params / total_params if total_params > 0 else 0.0
        
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return EvaluationResult(
            case=case,
            prompt_used=prompt,
            prompt_stats=stats,
            parameter_accuracy=parameter_accuracy,
            overall_accuracy=overall_accuracy,
            similarity_scores=similarity_scores,
            execution_time_ms=execution_time,
        )
    
    def run_evaluation(
        self,
        user_permissions: Optional[Set[Permission]] = None,
        difficulty_filter: Optional[str] = None,
        tag_filter: Optional[str] = None,
    ) -> List[EvaluationResult]:
        """Run evaluation on all test cases.
        
        Args:
            user_permissions: User permissions for testing (defaults to StatementsPermission)
            difficulty_filter: Filter by difficulty level
            tag_filter: Filter by tag
            
        Returns:
            List of evaluation results
        """
        if user_permissions is None:
            user_permissions = {Permission.StatementsPermission}
        
        # Filter test cases
        filtered_cases = self.test_cases
        
        if difficulty_filter:
            filtered_cases = [
                case for case in filtered_cases
                if case.difficulty == difficulty_filter
            ]
        
        if tag_filter:
            filtered_cases = [
                case for case in filtered_cases
                if tag_filter in case.tags
            ]
        
        logger.info(f"Running evaluation on {len(filtered_cases)} test cases")
        
        results = []
        for i, case in enumerate(filtered_cases, 1):
            logger.info(f"Evaluating case {i}/{len(filtered_cases)}: {case.query}")
            
            try:
                result = self.evaluate_case(case, user_permissions)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to evaluate case {i}: {e}")
        
        return results
    
    def generate_report(self, results: List[EvaluationResult]) -> Dict[str, any]:
        """Generate evaluation report from results.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Report dictionary
        """
        if not results:
            return {"error": "No results to analyze"}
        
        # Overall statistics
        total_cases = len(results)
        avg_accuracy = sum(r.overall_accuracy for r in results) / total_cases
        avg_execution_time = sum(r.execution_time_ms for r in results) / total_cases
        
        # Accuracy by difficulty
        accuracy_by_difficulty = {}
        for difficulty in ["easy", "medium", "hard"]:
            difficulty_results = [r for r in results if r.case.difficulty == difficulty]
            if difficulty_results:
                accuracy_by_difficulty[difficulty] = {
                    "count": len(difficulty_results),
                    "avg_accuracy": sum(r.overall_accuracy for r in difficulty_results) / len(difficulty_results)
                }
        
        # Parameter-specific accuracy
        parameter_accuracy = {}
        for result in results:
            for param, correct in result.parameter_accuracy.items():
                if param not in parameter_accuracy:
                    parameter_accuracy[param] = {"correct": 0, "total": 0}
                parameter_accuracy[param]["total"] += 1
                if correct:
                    parameter_accuracy[param]["correct"] += 1
        
        # Calculate parameter accuracy percentages
        for param in parameter_accuracy:
            stats = parameter_accuracy[param]
            stats["accuracy"] = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        
        # Prompt statistics
        avg_prompt_stats = {}
        if results:
            stat_keys = results[0].prompt_stats.keys()
            for key in stat_keys:
                values = [r.prompt_stats.get(key, 0) for r in results]
                if all(isinstance(v, (int, float)) for v in values):
                    avg_prompt_stats[key] = sum(values) / len(values)
        
        return {
            "summary": {
                "total_cases": total_cases,
                "average_accuracy": avg_accuracy,
                "average_execution_time_ms": avg_execution_time,
            },
            "accuracy_by_difficulty": accuracy_by_difficulty,
            "parameter_accuracy": parameter_accuracy,
            "prompt_statistics": avg_prompt_stats,
            "detailed_results": [r.to_dict() for r in results],
        }
    
    def save_report(self, report: Dict[str, any], output_file: Path) -> None:
        """Save evaluation report to JSON file."""
        try:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Saved evaluation report to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")


def run_evaluation_suite():
    """Run the complete evaluation suite."""
    print("=== Dynamic Prompt Construction Evaluation ===\n")
    
    evaluator = DynamicPromptEvaluator()
    
    # Run evaluation
    results = evaluator.run_evaluation()
    
    # Generate report
    report = evaluator.generate_report(results)
    
    # Print summary
    print("Evaluation Summary:")
    print(f"Total test cases: {report['summary']['total_cases']}")
    print(f"Average accuracy: {report['summary']['average_accuracy']:.2%}")
    print(f"Average execution time: {report['summary']['average_execution_time_ms']:.1f}ms")
    
    print("\nAccuracy by difficulty:")
    for difficulty, stats in report.get("accuracy_by_difficulty", {}).items():
        print(f"  {difficulty}: {stats['avg_accuracy']:.2%} ({stats['count']} cases)")
    
    print("\nParameter accuracy:")
    for param, stats in report.get("parameter_accuracy", {}).items():
        print(f"  {param}: {stats['accuracy']:.2%} ({stats['correct']}/{stats['total']})")
    
    # Save detailed report
    output_file = Path("evaluation_report.json")
    evaluator.save_report(report, output_file)
    print(f"\nDetailed report saved to: {output_file}")


if __name__ == "__main__":
    run_evaluation_suite()
