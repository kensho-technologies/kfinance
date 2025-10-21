"""Dynamic prompt constructor for assembling query-specific prompts with relevant examples."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set, Union

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
                descriptors_section = self._build_parameter_descriptors_section(
                    examples_by_tool, query
                )
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
        self, examples_by_tool: Dict[str, List[ToolExample]], query: str = ""
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
                    # Use contextual formatting with query and examples
                    descriptor_text = self._format_parameter_descriptor_with_context(
                        descriptor, examples_by_tool[tool_name], query
                    )
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

    def _format_parameter_descriptor_with_context(
        self, descriptor: ParameterDescriptor, examples: List[ToolExample], query: str
    ) -> str:
        """Format a parameter descriptor with contextually relevant examples."""
        parts = [f"- {descriptor.parameter_name}: {descriptor.description}"]

        if descriptor.examples:
            # Smart example selection based on context
            relevant_examples = self._select_relevant_examples(
                descriptor.examples, descriptor.parameter_name, examples, query
            )

            # Format examples with descriptions when available
            example_parts = []
            for example_key, example_desc in relevant_examples[:3]:  # Limit to 3
                if example_desc and example_desc.strip():
                    # Include description if available
                    example_parts.append(f'"{example_key}" ({example_desc})')
                else:
                    # Just the key if no description
                    example_parts.append(f'"{example_key}"')

            if example_parts:
                examples_str = ", ".join(example_parts)
                parts.append(f"  Examples: {examples_str}")

        if descriptor.common_mistakes:
            mistakes_str = "; ".join(descriptor.common_mistakes[:2])  # Limit mistakes
            parts.append(f"  Common mistakes: {mistakes_str}")

        return "\n".join(parts)

    def _select_relevant_examples(
        self,
        examples_data: Union[Dict[str, str], List[str]],
        parameter_name: str,
        tool_examples: List[ToolExample],
        query: str,
    ) -> List[tuple]:
        """Select the most relevant examples based on context.

        Returns list of (example_key, example_description) tuples.
        """
        # Handle both dict and list formats for backward compatibility
        if isinstance(examples_data, dict):
            all_examples = list(examples_data.keys())
            example_descriptions = examples_data
        else:  # isinstance(examples_data, list)
            all_examples = examples_data
            example_descriptions = {ex: "" for ex in examples_data}

        if not all_examples:
            return []

        # Priority 1: Examples that appear in the selected tool examples
        used_values = set()
        for tool_example in tool_examples:
            if parameter_name in tool_example.parameters:
                param_value = tool_example.parameters[parameter_name]
                if isinstance(param_value, str) and param_value in all_examples:
                    used_values.add(param_value)

        # Priority 2: Examples that match query terms (case-insensitive)
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Score ALL examples by relevance (including used values for proper ordering)
        all_scored = []
        for example_key in all_examples:
            example_lower = example_key.lower()
            score = 0

            # Exact substring match gets highest score
            if example_lower in query_lower:
                score = 100
            # Word matches get lower scores
            else:
                example_words = set(example_lower.replace("_", " ").split())
                word_matches = len(query_words.intersection(example_words))
                if word_matches > 0:
                    score = word_matches * 10

            # Boost score if it's also a used value (appears in examples)
            if example_key in used_values:
                score += 1000  # High boost for used values

            all_scored.append((score, example_key))

        # Sort by score (highest first)
        all_scored.sort(key=lambda x: x[0], reverse=True)

        # Return examples with descriptions ordered by relevance score (highest first)
        return [(ex, example_descriptions.get(ex, "")) for _, ex in all_scored]

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
