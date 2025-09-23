"""Dynamic prompt constructor for assembling query-specific prompts with relevant examples."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

from kfinance.client.permission_models import Permission
from kfinance.integrations.tool_calling.prompts import BASE_PROMPT

from .models import ParameterDescriptor, ToolExample
from .repository import ExampleRepository
from .search import SimilaritySearchEngine


logger = logging.getLogger(__name__)


class DynamicPromptConstructor:
    """Constructs dynamic prompts with query-specific examples and parameter descriptors."""

    def __init__(
        self,
        example_repository: ExampleRepository,
        similarity_engine: Optional[SimilaritySearchEngine] = None,
        max_examples_per_tool: int = 3,
        max_total_examples: int = 8,
        include_parameter_descriptors: bool = True,
    ):
        """Initialize the dynamic prompt constructor.

        Args:
            example_repository: Repository containing examples and parameter descriptors
            similarity_engine: Engine for similarity search (will create one if None)
            max_examples_per_tool: Maximum examples to include per tool
            max_total_examples: Maximum total examples to include in prompt
            include_parameter_descriptors: Whether to include parameter descriptors
        """
        self.example_repository = example_repository
        self.similarity_engine = similarity_engine or SimilaritySearchEngine(
            embedding_model=example_repository.embedding_model
        )
        self.max_examples_per_tool = max_examples_per_tool
        self.max_total_examples = max_total_examples
        self.include_parameter_descriptors = include_parameter_descriptors

        # Base prompt template
        self.base_prompt = BASE_PROMPT

    def construct_prompt(
        self,
        query: str,
        user_permissions: Set[Permission],
        available_tools: Optional[List[str]] = None,
        min_similarity: float = 0.3,
    ) -> str:
        """Construct a dynamic prompt with query-specific examples.

        Args:
            query: User query to construct prompt for
            user_permissions: User's permissions for filtering examples
            available_tools: List of available tool names (if None, use all)
            min_similarity: Minimum similarity threshold for including examples

        Returns:
            Constructed prompt with relevant examples and descriptors
        """
        # Start with base prompt
        prompt_parts = [self.base_prompt.strip()]

        # Search for relevant examples
        relevant_examples = self._find_relevant_examples(
            query, user_permissions, available_tools, min_similarity
        )

        if relevant_examples:
            # Group examples by tool
            examples_by_tool = self._group_examples_by_tool(relevant_examples)

            # Add examples section
            examples_section = self._build_examples_section(examples_by_tool)
            if examples_section:
                prompt_parts.append(examples_section)

            # Add parameter descriptors if enabled
            if self.include_parameter_descriptors:
                descriptors_section = self._build_parameter_descriptors_section(examples_by_tool)
                if descriptors_section:
                    prompt_parts.append(descriptors_section)

        # Join all parts
        return "\n\n".join(prompt_parts)

    def _find_relevant_examples(
        self,
        query: str,
        user_permissions: Set[Permission],
        available_tools: Optional[List[str]],
        min_similarity: float,
    ) -> List[ToolExample]:
        """Find relevant examples using similarity search."""
        # Search for examples
        similarity_results = self.similarity_engine.search_examples(
            query=query,
            examples=self.example_repository.examples,
            user_permissions=user_permissions,
            tool_names=available_tools,
            top_k=self.max_total_examples * 2,  # Get more candidates for filtering
            min_similarity=min_similarity,
        )

        # Extract examples from similarity results
        examples = [example for _, example in similarity_results]

        # Limit total examples
        return examples[: self.max_total_examples]

    def _group_examples_by_tool(self, examples: List[ToolExample]) -> Dict[str, List[ToolExample]]:
        """Group examples by tool name, respecting per-tool limits."""
        examples_by_tool: Dict[str, List[ToolExample]] = {}

        for example in examples:
            tool_name = example.tool_name
            if tool_name not in examples_by_tool:
                examples_by_tool[tool_name] = []

            # Respect per-tool limit
            if len(examples_by_tool[tool_name]) < self.max_examples_per_tool:
                examples_by_tool[tool_name].append(example)

        return examples_by_tool

    def _build_examples_section(self, examples_by_tool: Dict[str, List[ToolExample]]) -> str:
        """Build the examples section of the prompt."""
        if not examples_by_tool:
            return ""

        section_parts = ["RELEVANT EXAMPLES:"]

        for tool_name, examples in examples_by_tool.items():
            if not examples:
                continue

            section_parts.append(f"\n{tool_name} Examples:")

            for i, example in enumerate(examples, 1):
                example_text = self._format_example(example, i)
                section_parts.append(example_text)

        return "\n".join(section_parts)

    def _format_example(self, example: ToolExample, index: int) -> str:
        """Format a single example for inclusion in the prompt."""
        parts = [f'{index}. Query: "{example.query}"']

        # Format function call
        params_str = ", ".join([f"{k}={repr(v)}" for k, v in example.parameters.items()])
        function_call = f"   Function: {example.tool_name}({params_str})"
        parts.append(function_call)

        # Add context if available
        if example.context:
            parts.append(f"   Context: {example.context}")

        # Add disambiguation note if available
        if example.disambiguation_note:
            parts.append(f"   Note: {example.disambiguation_note}")

        return "\n".join(parts)

    def _build_parameter_descriptors_section(
        self, examples_by_tool: Dict[str, List[ToolExample]]
    ) -> str:
        """Build the parameter descriptors section of the prompt."""
        section_parts: List[str] = []

        for tool_name in examples_by_tool.keys():
            descriptors = self.example_repository.get_parameter_descriptors(tool_name)
            if not descriptors:
                continue

            # Only include descriptors for parameters that appear in the examples
            relevant_descriptors = self._filter_relevant_descriptors(
                descriptors, examples_by_tool[tool_name]
            )

            if relevant_descriptors:
                if not section_parts:
                    section_parts.append("PARAMETER GUIDANCE:")

                section_parts.append(f"\n{tool_name} Parameters:")

                for descriptor in relevant_descriptors:
                    descriptor_text = self._format_parameter_descriptor(descriptor)
                    section_parts.append(descriptor_text)

        return "\n".join(section_parts) if section_parts else ""

    def _filter_relevant_descriptors(
        self, descriptors: List[ParameterDescriptor], examples: List[ToolExample]
    ) -> List[ParameterDescriptor]:
        """Filter parameter descriptors to only include those relevant to the examples."""
        # Get parameter names from examples
        example_params: Set[str] = set()
        for example in examples:
            example_params.update(example.parameters.keys())

        # Filter descriptors
        relevant_descriptors = []
        for descriptor in descriptors:
            if descriptor.parameter_name in example_params:
                relevant_descriptors.append(descriptor)

        return relevant_descriptors

    def _format_parameter_descriptor(self, descriptor: ParameterDescriptor) -> str:
        """Format a parameter descriptor for inclusion in the prompt."""
        parts = [f"- {descriptor.parameter_name}: {descriptor.description}"]

        if descriptor.examples:
            examples_str = ", ".join(f'"{ex}"' for ex in descriptor.examples[:3])  # Limit examples
            parts.append(f"  Examples: {examples_str}")

        if descriptor.common_mistakes:
            mistakes_str = "; ".join(descriptor.common_mistakes[:2])  # Limit mistakes
            parts.append(f"  Common mistakes: {mistakes_str}")

        return "\n".join(parts)

    def get_prompt_stats(self, prompt: str) -> Dict[str, int]:
        """Get statistics about the constructed prompt.

        Args:
            prompt: The constructed prompt

        Returns:
            Dictionary with prompt statistics
        """
        lines = prompt.split("\n")
        words = prompt.split()

        # Count examples
        example_count = prompt.count('Query: "')

        # Count parameter descriptors
        descriptor_count = prompt.count("Parameters:")

        return {
            "total_lines": len(lines),
            "total_words": len(words),
            "total_characters": len(prompt),
            "example_count": example_count,
            "parameter_descriptor_sections": descriptor_count,
        }

    def construct_prompt_with_stats(
        self,
        query: str,
        user_permissions: Set[Permission],
        available_tools: Optional[List[str]] = None,
        min_similarity: float = 0.3,
    ) -> tuple[str, Dict[str, int]]:
        """Construct prompt and return it with statistics.

        Returns:
            Tuple of (prompt, statistics)
        """
        prompt = self.construct_prompt(query, user_permissions, available_tools, min_similarity)
        stats = self.get_prompt_stats(prompt)
        return prompt, stats
