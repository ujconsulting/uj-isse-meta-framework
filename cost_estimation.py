"""
Cost and Time Estimation Module for ISEE Framework

This module provides functionality to estimate API costs and execution time
based on parameter selections in the ISEE Command Wizard.

Part of the UX Enhancement Roadmap - Step 1.1: Cost and Time Estimation
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import math
import json
import re
import logging
import os
from pathlib import Path

# Token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

# Constants for cost estimation
#
# STATIC FALLBACK ONLY — not the source of truth. This comment used to claim "based on
# publicly available pricing as of May 2024, updated for 2025 models"; as of 2026-09-05
# neither half holds: no entry below carries a fetch date, and most of the currently
# configured portfolio (openrouter_config.json's 2026 models) has no entry here at all.
# The trustworthy price is the `pricing` block embedded in each model's own config
# entry (prompt_per_mtok/completion_per_mtok, dated by `fetched`), which
# `_get_model_cost_rate` always prefers when present. A model only reaches this table
# when its configuration carries no price — treat every number below as unverified and
# possibly years stale.
MODEL_COSTS = {
    # Anthropic Claude models - Updated 2025 pricing (per 1M input tokens / 1M output tokens in USD)
    "claude-opus-4-1-20250805": {"input": 15, "output": 75},
    "claude-sonnet-4-20250514": {"input": 3, "output": 15},
    "claude-3-7-sonnet-20250219": {"input": 3, "output": 15},
    "claude-3-5-sonnet-20241022": {"input": 3, "output": 15},
    "claude-3-5-haiku-20241022": {"input": 0.8, "output": 4},
    "claude-3-opus-20240229": {"input": 15, "output": 75},
    "claude-3-sonnet-20240229": {"input": 3, "output": 15},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    
    # OpenAI GPT models - Updated 2025 pricing (per 1M tokens in USD)
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    "gpt-4-turbo": {"input": 10, "output": 30},
    "gpt-4": {"input": 30, "output": 60},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    
    # Google Gemini models - Updated 2025 pricing (per 1M tokens in USD)
    "gemini-2.5-pro": {"input": 3.5, "output": 10.5},
    "models/gemini-2.5-pro": {"input": 3.5, "output": 10.5},
    "models/gemini-1.5-pro": {"input": 3.5, "output": 10.5},
    "models/gemini-1.0-pro": {"input": 3.5, "output": 10.5},
    
    # Globant Enterprise AI pricing (per 1M tokens in USD)
    # Note: Enterprise pricing may include premium fees for SLA, security, and support
    # These are estimated based on typical enterprise markups over standard API pricing
    "globant:claude-sonnet-4-20250514": {"input": 4.5, "output": 22.5, "provider": "globant"},
    "globant:claude-3-5-haiku-20241022": {"input": 1.2, "output": 6, "provider": "globant"},
    "globant:gpt-4o-mini": {"input": 0.225, "output": 0.9, "provider": "globant"},
    "globant:gpt-4-turbo": {"input": 15, "output": 45, "provider": "globant"},
    "globant:gpt-4": {"input": 45, "output": 90, "provider": "globant"},
    "globant:gpt-3.5-turbo": {"input": 0.75, "output": 2.25, "provider": "globant"},
    "globant:gemini-2.5-pro": {"input": 5.25, "output": 15.75, "provider": "globant"},
    
    # OpenRouter models (unified API pricing - may include small markup)
    "openrouter:anthropic/claude-sonnet-4": {"input": 3, "output": 15, "provider": "openrouter"},
    "openrouter:anthropic/claude-3.5-haiku": {"input": 0.8, "output": 4, "provider": "openrouter"},
    "openrouter:openai/gpt-4o-mini": {"input": 0.15, "output": 0.6, "provider": "openrouter"},
    "openrouter:openai/gpt-4-turbo": {"input": 10, "output": 30, "provider": "openrouter"},
    "openrouter:google/gemini-2.5-pro": {"input": 3.5, "output": 10.5, "provider": "openrouter"},
    
    # Default rates for unknown models by tier
    "default-large": {"input": 10, "output": 30},
    "default-medium": {"input": 3, "output": 15},
    "default-small": {"input": 0.5, "output": 1.5},
    
    # Ollama models have no direct cost (they run locally)
    "ollama": {"input": 0, "output": 0}
}

# Map from model aliases to actual model costs
MODEL_ALIASES = {
    # Anthropic models
    "claude-3-opus": "claude-3-opus-20240229",
    "claude-3-sonnet": "claude-3-sonnet-20240229", 
    "claude-3-haiku": "claude-3-haiku-20240307",
    
    # OpenAI models
    "gpt-4-0125-preview": "gpt-4-turbo",
    "gpt-4-1106-preview": "gpt-4-turbo",
    "gpt-3.5-turbo-0125": "gpt-3.5-turbo",
    
    # Google models
    "gemini-pro": "models/gemini-1.0-pro",
    
    # Ollama models (all zero cost)
    "llama2": "ollama",
    "llama3": "ollama",
    "mistral": "ollama",
    "mixtral": "ollama",
    "phi3": "ollama",
    "codellama": "ollama"
}

# Approximate token sizes for prompt components
PROMPT_TOKEN_SIZES = {
    "short_query": 25,       # ~25 tokens for a short query
    "medium_query": 50,      # ~50 tokens for a medium query
    "long_query": 100,       # ~100 tokens for a long query
    "instruction": 150,      # ~150 tokens for an instruction template
    "domain_context": 50,    # ~50 tokens for domain context
    "system_overhead": 100,  # ~100 tokens for system overhead
}

# Expected output tokens per call — MEASURED, not assumed.
#
# 23 real responses across the configured 14-model portfolio on 2026-09-02 ran
# 4,075-15,565 characters, mean ≈8,760, i.e. roughly 2,190 tokens. 2,500 is that rounded
# up. This is the first cost figure in this project derived from observation rather than
# from a guess that looked like one.
#
# ⚠️ One query, one day, one portfolio. Reasoning-heavy prompts will exceed it. Treat the
# resulting estimate as an order of magnitude, not a quote — and re-measure when the
# portfolio changes. `performance_tracker.py` is where a running average belongs once the
# usage figures the API returns are actually persisted.
TYPICAL_RESPONSE_TOKENS = 2500

# Average tokens per minute for model processing
MODEL_PROCESSING_SPEEDS = {
    "claude-3-opus-20240229": 3000,  # Tokens per minute
    "claude-3-sonnet-20240229": 4000,
    "claude-3-haiku-20240307": 5000,
    "gpt-4-turbo": 4000,
    "gpt-4": 3000,
    "gpt-3.5-turbo": 6000,
    "models/gemini-1.5-pro": 4000,
    "models/gemini-1.0-pro": 4000,
    
    # Ollama processing speeds vary by hardware
    "llama3:8b": 4000,      # Estimated on consumer hardware
    "mistral:7b": 4000,
    "mixtral:8x7b": 2000,   # Slower due to model size
    "phi3:mini": 5000,      # Faster due to smaller size
    
    # Defaults for model categories
    "default-large": 3000,
    "default-medium": 4000,
    "default-small": 5000
}

# Cost warnings thresholds (in USD)
COST_WARNING_THRESHOLDS = {
    "notice": 0.5,     # $0.50 - Just a notice
    "warning": 2.0,    # $2.00 - Warning level
    "high": 10.0,      # $10.00 - High cost warning
    "very_high": 50.0  # $50.00 - Very high cost warning
}

# Real execution runs every combination through ONE shared worker pool, not one worker
# per model (see main.py's ParallelExecutionEngine / --max-workers, default 8). Summing
# each model's own processing time as if models ran one after another — which this
# module did until 2026-09-05 — reported a serial total for a run that is actually
# parallel, inflating the displayed wall-clock estimate. A caller that knows the run's
# real worker count should pass it as params["max_workers"]; this is only the fallback
# for when it does not.
DEFAULT_CONCURRENCY = 8

# Time warnings thresholds (in minutes)
TIME_WARNING_THRESHOLDS = {
    "notice": 2,      # 2 minutes - Just a notice
    "warning": 5,     # 5 minutes - Warning level
    "high": 15,       # 15 minutes - High time warning
    "very_high": 60   # 60 minutes - Very high time warning
}


def _normalise_model_name(name: str) -> str:
    """Reduce a model name to something comparable across providers.

    The same model appears under three spellings in MODEL_COSTS depending on who
    sells it: "anthropic/claude-sonnet-4" from OpenRouter (vendor path, no date),
    "claude-sonnet-4-20250514" from Globant (dated), and the bare dated name for a
    direct account. Comparing prices across providers means comparing these, so the
    vendor prefix and a trailing release date are dropped.

    Deliberately narrow: it strips a vendor path segment and an 8-digit date, and
    nothing else. Anything cleverer would start matching models that merely look
    alike, and a cost comparison that silently pairs the wrong two is worse than
    one that reports a provider missing.
    """
    base = name.split("/")[-1]
    base = re.sub(r"-20\d{6}$", "", base)
    return base.strip().lower()


class CostEstimator:
    """Estimates API costs and execution time for ISEE commands."""
    
    def __init__(self):
        """Initialize the cost estimator."""
        # Populated by _load_models_info() when a *config*.json exists but cannot be
        # listed, read, or parsed. estimate_cost() copies this into its return value so
        # a broken config produces a visible warning instead of a plausible-looking
        # price for a hardcoded 2024 portfolio that will not actually run — see the
        # HIGH finding in docs/audit/2026-09-03-baseline.md, cost_estimation.py #1.
        self.config_errors: List[str] = []
        self.models_info = self._load_models_info()
    
    @staticmethod
    def _model_is_usable(model: Dict[str, Any]) -> bool:
        """Whether a configured model should be considered at all.

        Only the explicit `disabled` flag. An earlier version of this also required the
        model's `requires` environment variable to be set — which looked principled and
        was a trap: this module never loads `.env`, so in any context that had not already
        imported the API layer the check silently emptied the pool and the estimator fell
        back to five hardcoded models from 2024. A filter whose failure mode is "quietly
        estimate something else" is worse than no filter.

        Which models are actually reachable is decided where the credentials live, not
        here. Preferring the ones we can price is handled in
        `_get_available_models_for_params`.
        """
        return not model.get("disabled")

    def _load_models_info(self) -> Dict[str, Dict[str, Any]]:
        """Load models information from configuration files.

        The hardcoded fallback portfolio (`_get_fallback_models_info`) is only the
        right answer when there is genuinely nothing to read — no *config*.json in the
        working directory at all. Every other failure mode here (can't list the
        directory, a config file that doesn't parse, a config that parses but declares
        no usable models) is a real problem with a specific file, and is recorded in
        `self.config_errors` instead of being swallowed, so estimate_cost() can surface
        it rather than quietly pricing models that will never run.

        Returns:
            Dictionary mapping model IDs to model information.
        """
        models_info = {}

        # Look for configuration files
        config_files = []
        try:
            for file in os.listdir():
                if file.endswith('.json') and ('config' in file.lower()):
                    config_files.append(file)
        except OSError as e:
            # Can't even see what configuration exists (missing/unreadable cwd). This
            # is a failure, not "no configuration" — the intended silent fallback below
            # never applies here.
            self.config_errors.append(
                f"could not list the working directory for *config*.json files: {e}")
            return self._get_fallback_models_info()

        if not config_files:
            # Genuinely nothing to read. This is the ONE place the hardcoded fallback
            # is the intended behaviour rather than a failure being papered over, so it
            # stays silent — nothing went wrong, there was just no configuration.
            return self._get_fallback_models_info()

        # Try to load models from configuration files
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # Process models in the config file
                if "models" in config:
                    # Check if models is a dictionary with sections or a flat list
                    if isinstance(config["models"], dict):
                        for section in ("api_models", "ollama_models"):
                            for model in config["models"].get(section, []):
                                if self._model_is_usable(model):
                                    models_info[model.get("id")] = model
                    else:
                        # Handle flat list of models
                        for model in config["models"]:
                            if self._model_is_usable(model):
                                models_info[model.get("id")] = model
            except (OSError, json.JSONDecodeError, UnicodeDecodeError, AttributeError, TypeError) as e:
                # A file that matched the *config*.json glob but could not be read as
                # configuration is exactly what the audit flagged: silently skipping it
                # let a malformed config produce a plausible price quote for a
                # portfolio that would never actually run. Record which file and why.
                self.config_errors.append(f"{config_file}: could not be read as a model configuration ({e})")
                continue

        # If no models were found, that is now an error case (we had files to read;
        # they just did not yield anything usable), not the "no configuration" case
        # handled above — record it unless a more specific per-file reason already was.
        if not models_info:
            if not self.config_errors:
                self.config_errors.append(
                    f"{', '.join(config_files)}: parsed but declared no usable models")
            return self._get_fallback_models_info()

        return models_info
    
    def _get_fallback_models_info(self) -> Dict[str, Dict[str, Any]]:
        """Provide fallback model information when config files are not available.
        
        Returns:
            Dictionary mapping model IDs to model information.
        """
        return {
            "anthropic_claude": {
                "id": "anthropic_claude",
                "name": "Claude 3 Sonnet",
                "provider": "anthropic",
                "parameters": {"model": "claude-3-sonnet-20240229"}
            },
            "openai_gpt4": {
                "id": "openai_gpt4",
                "name": "GPT-4 Turbo",
                "provider": "openai",
                "parameters": {"model": "gpt-4-turbo"}
            },
            "openai_gpt35": {
                "id": "openai_gpt35",
                "name": "GPT-3.5 Turbo",
                "provider": "openai",
                "parameters": {"model": "gpt-3.5-turbo"}
            },
            "google_gemini": {
                "id": "google_gemini",
                "name": "Gemini 1.5 Pro",
                "provider": "google",
                "parameters": {"model": "models/gemini-1.5-pro"}
            },
            "ollama_llama3": {
                "id": "ollama_llama3",
                "name": "Llama 3 (8B)",
                "provider": "ollama",
                "parameters": {"model": "llama3:8b"}
            }
        }
    
    def get_provider_model_cost_key(self, model_name: str, provider: str) -> str:
        """Generate provider-specific cost key for a model.
        
        Args:
            model_name: The base model name (e.g., "claude-sonnet-4-20250514")
            provider: The provider name (e.g., "globant", "openrouter")
            
        Returns:
            Provider-specific cost key (e.g., "globant:claude-sonnet-4-20250514")
        """
        if provider in ["globant", "openrouter"]:
            return f"{provider}:{model_name}"
        return model_name
    
    def get_cost_comparison(self, model_name: str) -> Dict[str, Dict[str, float]]:
        """Get cost comparison across providers for a given model.
        
        Args:
            model_name: The base model name to compare
            
        Returns:
            Dictionary mapping provider names to their cost structures
        """
        costs = {}

        # OpenRouter keys are not shaped like the others, and building one by
        # concatenation could never match.
        #
        # MODEL_COSTS holds three shapes: "openrouter:anthropic/claude-sonnet-4"
        # (vendor path, no date), "globant:claude-sonnet-4-20250514" (bare name with
        # date) and "claude-opus-4-1-20250805" (bare, direct). This method is called
        # with one name and used to build "openrouter:" + that name, so the
        # OpenRouter branch was structurally dead for every model in the table —
        # the cross-provider comparison silently reported one provider fewer than it
        # had. Match on the normalised model name instead.
        wanted = _normalise_model_name(model_name)

        for key, entry in MODEL_COSTS.items():
            provider, _, name = key.partition(":")
            if not _:                              # no colon: a direct entry
                provider, name = "direct", key
            if _normalise_model_name(name) != wanted:
                continue
            # A direct entry must not displace a provider-specific one.
            if provider not in costs:
                costs[provider] = entry

        return costs
    
    def _get_model_cost_rate(self, model_info: Dict[str, Any]) -> Dict[str, float]:
        """Get the cost rate for a model, considering provider-specific pricing.
        
        Args:
            model_info: Model information dictionary.
            
        Returns:
            Dictionary with input and output token costs per 1M tokens.
        """
        # Extract model name and provider from parameters
        model_params = model_info.get("parameters", {})
        model_name = model_params.get("model", "")
        provider = model_info.get("provider", "").lower()

        # Prices recorded in the configuration win over every table and heuristic below.
        # They were taken from the provider's own catalogue and travel with the model
        # entry, so they cannot drift apart from the id they belong to — which is exactly
        # how MODEL_COSTS came to hold nothing for any currently configured model.
        embedded = model_info.get("pricing")
        if isinstance(embedded, dict) and "prompt_per_mtok" in embedded:
            return {
                "input": embedded["prompt_per_mtok"],
                "output": embedded["completion_per_mtok"],
                "provider": provider or "openrouter",
                "source": f"config ({embedded.get('fetched', 'undated')})",
            }
        
        # Generate provider-specific cost key
        provider_model_key = self.get_provider_model_cost_key(model_name, provider)
        
        # Check if we have exact match for the provider-specific model
        if provider_model_key in MODEL_COSTS:
            return MODEL_COSTS[provider_model_key]
        
        # Check if we have exact match for the base model
        if model_name in MODEL_COSTS:
            return MODEL_COSTS[model_name]
        
        # Check if we have an alias for the model
        for alias, target in MODEL_ALIASES.items():
            if alias in model_name.lower():
                return MODEL_COSTS[target]
        
        # Use provider-based fallback with enterprise markup for Globant
        if provider == "globant":
            # Apply enterprise markup (typically 1.5x for security, support, SLA)
            base_cost = self._get_base_provider_cost(model_name, "anthropic")
            if base_cost:
                return {
                    "input": base_cost["input"] * 1.5,
                    "output": base_cost["output"] * 1.5,
                    "provider": "globant"
                }
        elif provider == "openrouter":
            # ⛔ No guessing. This used to price ANY unknown OpenRouter model as though it
            # were an Anthropic one — for upstage/solar-pro4 ($0.03/$0.12) that is wrong by
            # roughly sixty times, and it presented the result with the same confidence as
            # a real price. OpenRouter fronts 400+ models from a dozen houses; "unknown"
            # carries no information about cost.
            #
            # An estimate that is absent is a visible gap. An estimate that is wrong by two
            # orders of magnitude is a decision made on fiction. Record the price in the
            # model's configuration entry (see `pricing` in openrouter_config.json) and
            # this branch is never reached.
            logging.getLogger(__name__).warning(
                "No price known for OpenRouter model %r and none recorded in its "
                "configuration entry; it is excluded from the cost estimate. "
                "Add a 'pricing' block to its openrouter_config.json entry.",
                model_name,
            )
            return {"input": 0.0, "output": 0.0, "provider": "openrouter",
                    "price_unavailable": True, "model": model_name}
        elif provider == "anthropic":
            return MODEL_COSTS["default-medium"]  # Medium cost model
        elif provider == "openai":
            if "gpt-4" in model_name.lower():
                return MODEL_COSTS["default-large"]  # Large cost model
            else:
                return MODEL_COSTS["default-small"]  # Small cost model
        elif provider == "google":
            return MODEL_COSTS["default-medium"]  # Medium cost model
        elif provider == "ollama":
            return MODEL_COSTS["ollama"]  # Zero cost
        
        # Default fallback
        return MODEL_COSTS["default-medium"]
    
    def _get_base_provider_cost(self, model_name: str, base_provider: str) -> Optional[Dict[str, float]]:
        """Get base cost for a model from a specific provider.
        
        Args:
            model_name: Model name to find base cost for
            base_provider: Base provider to check (e.g., "anthropic")
            
        Returns:
            Cost dictionary or None if not found
        """
        # Map common model patterns to base costs
        if "claude" in model_name.lower():
            if "sonnet-4" in model_name.lower():
                return MODEL_COSTS.get("claude-sonnet-4-20250514")
            elif "haiku" in model_name.lower():
                return MODEL_COSTS.get("claude-3-5-haiku-20241022")
            elif "sonnet" in model_name.lower():
                return MODEL_COSTS.get("claude-3-5-sonnet-20241022")
        elif "gpt-4o-mini" in model_name.lower():
            return MODEL_COSTS.get("gpt-4o-mini")
        elif "gpt-4" in model_name.lower():
            return MODEL_COSTS.get("gpt-4-turbo")
        elif "gemini" in model_name.lower():
            return MODEL_COSTS.get("gemini-2.5-pro")
        
        return None
    
    def _get_model_processing_speed(self, model_info: Dict[str, Any]) -> int:
        """Get the processing speed for a model (tokens per minute).
        
        Args:
            model_info: Model information dictionary.
            
        Returns:
            Processing speed in tokens per minute.
        """
        # Extract model name from parameters
        model_params = model_info.get("parameters", {})
        model_name = model_params.get("model", "")
        
        # Check if we have exact match for the model
        if model_name in MODEL_PROCESSING_SPEEDS:
            return MODEL_PROCESSING_SPEEDS[model_name]
        
        # Use provider-based fallback
        provider = model_info.get("provider", "").lower()
        if provider == "anthropic":
            return MODEL_PROCESSING_SPEEDS["default-medium"]
        elif provider == "openai":
            if "gpt-4" in model_name.lower():
                return MODEL_PROCESSING_SPEEDS["default-large"]
            else:
                return MODEL_PROCESSING_SPEEDS["default-small"]
        elif provider == "google":
            return MODEL_PROCESSING_SPEEDS["default-medium"]
        elif provider == "ollama":
            # Ollama speeds depend on model size and hardware
            if "llama3" in model_name.lower() or "mistral" in model_name.lower():
                return MODEL_PROCESSING_SPEEDS["llama3:8b"]
            elif "mixtral" in model_name.lower():
                return MODEL_PROCESSING_SPEEDS["mixtral:8x7b"]
            elif "phi3" in model_name.lower():
                return MODEL_PROCESSING_SPEEDS["phi3:mini"]
            return MODEL_PROCESSING_SPEEDS["default-medium"]
        
        # Default fallback
        return MODEL_PROCESSING_SPEEDS["default-medium"]
    
    def _estimate_tokens_for_query(self, query: str) -> int:
        """Estimate the number of tokens in a query.
        
        Args:
            query: The query string.
            
        Returns:
            Estimated number of tokens.
        """
        if not query:
            return 0
        
        if TIKTOKEN_AVAILABLE:
            # Use tiktoken for more accurate token counting
            try:
                # cl100k_base is OpenAI's tokenizer (GPT-3.5/4 era), not Claude's —
                # Anthropic has never published one. Used here only as a cross-model
                # approximation, which this estimate already is regardless of provider.
                encoder = tiktoken.get_encoding("cl100k_base")
                return len(encoder.encode(query))
            except Exception:
                # Fallback to rough estimation if tiktoken fails
                pass
        
        # Rough estimation: ~1.33 tokens per word
        words = query.split()
        return math.ceil(len(words) * 1.33)
    
    def _estimate_prompt_tokens(self, params: Dict[str, Any]) -> int:
        """Estimate the number of tokens in a prompt.
        
        Args:
            params: Dictionary of command parameters.
            
        Returns:
            Estimated number of tokens.
        """
        query = params.get("query", "")
        
        # Use tiktoken if available
        if query and TIKTOKEN_AVAILABLE:
            query_tokens = self._estimate_tokens_for_query(query)
        else:
            # Rough estimation based on query length
            if not query:
                query_tokens = 0
            elif len(query) < 100:
                query_tokens = PROMPT_TOKEN_SIZES["short_query"]
            elif len(query) < 300:
                query_tokens = PROMPT_TOKEN_SIZES["medium_query"]
            else:
                query_tokens = PROMPT_TOKEN_SIZES["long_query"]
        
        # Add tokens for instruction template and domain context
        instruction_tokens = PROMPT_TOKEN_SIZES["instruction"]
        # _estimate_combinations() below already accepts EITHER params["domain"] (single)
        # OR params["domains"] (a list) as domain context. Checking only "domain" here
        # under-quoted every run that used the list form — the combination count grew
        # with the domains, but the per-prompt token estimate silently assumed there was
        # no domain context in the prompt at all.
        domain_tokens = PROMPT_TOKEN_SIZES["domain_context"] if (params.get("domain") or params.get("domains")) else 0
        system_tokens = PROMPT_TOKEN_SIZES["system_overhead"]
        
        return query_tokens + instruction_tokens + domain_tokens + system_tokens
    
    def _estimate_response_tokens(self, params: Dict[str, Any]) -> int:
        """Estimate the number of tokens in a response.
        
        Args:
            params: Dictionary of command parameters.
            
        Returns:
            Estimated number of tokens.
        """
        model_params = params.get("parameters", {})
        max_tokens = model_params.get("max_tokens", 1024)

        # `max_tokens` is a ceiling, not a forecast. Assuming 85% of it was defensible
        # while the ceiling was 4,096; at the current 16,000 it predicts 13,600 output
        # tokens per call and overstates a 66-call run as $1.66 where roughly $0.31 is
        # real — and an estimator that alarms is as useless as one that reassures.
        #
        # TYPICAL_RESPONSE_TOKENS is measured, not assumed: 23 real responses across the
        # configured portfolio on 2026-09-02 ran 4,075-15,565 characters, mean ≈8,760,
        # about 2,190 tokens. 2,500 is that rounded up.
        # ⚠️ One query, one day. The ceiling still applies, so a low max_tokens is
        # respected; re-measure before leaning on the constant harder than that.
        return int(min(max_tokens * 0.85, TYPICAL_RESPONSE_TOKENS))
    
    def _get_available_models_for_params(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get the list of available models that would be used based on parameters.
        
        Args:
            params: Dictionary of command parameters.
            
        Returns:
            List of model information dictionaries.
        """
        models_to_use = []

        # If the caller named the models, price THOSE. Nothing below this point knows
        # which models were actually selected: it takes the first N of a pool merged from
        # every *config*.json in the working directory, so a request selecting three
        # OpenRouter models was quoted for 'Claude Sonnet 4', 'GPT-4 Turbo' and
        # 'Gemini 2.5 Pro' — the first three entries of globant_enterprise_config.json,
        # a provider this installation cannot even reach.
        selected_ids = (params.get("selected_models") or params.get("selected_model_ids")
                        or params.get("models_selected"))
        if selected_ids:
            if isinstance(selected_ids, str):
                selected_ids = [s.strip() for s in selected_ids.split(",") if s.strip()]
            wanted = set(selected_ids)
            chosen = [
                info for mid, info in self.models_info.items()
                if mid in wanted
                or info.get("id") in wanted
                or info.get("parameters", {}).get("model") in wanted
            ]
            if chosen:
                return chosen
            logging.getLogger(__name__).warning(
                "None of the selected model ids %s were found in the loaded "
                "configurations; falling back to a portfolio-wide estimate.", sorted(wanted)
            )

        # Nothing was named, so this is a portfolio-wide estimate. Prefer the models whose
        # price we actually know — every *config*.json in the directory is merged into one
        # pool, so without this the estimate for an OpenRouter run could be built from
        # globant_enterprise_config.json entries, priced from a stale static table, for a
        # provider this installation has no credentials for.
        priced = [m for m in self.models_info.values() if isinstance(m.get("pricing"), dict)]
        if priced:
            models_count = params.get("models", 2)
            return priced[:max(1, int(models_count))]

        # Check how many models should be used
        models_count = params.get("models", 2)

        # Check if we should use Ollama models
        use_ollama = params.get("use_ollama", False)
        
        # Sort models by provider (cloud API vs Ollama)
        cloud_models = []
        ollama_models = []
        
        for model_id, model_info in self.models_info.items():
            provider = model_info.get("provider", "").lower()
            if provider == "ollama":
                ollama_models.append(model_info)
            else:
                cloud_models.append(model_info)
        
        # Select models based on params
        selected_models = []
        
        # Use a balanced approach if balanced_models is set
        if params.get("balanced_models", False):
            # Ensure diversity across providers
            providers_seen = set()
            
            # First, select one model from each provider
            for model in cloud_models + ollama_models:
                provider = model.get("provider", "").lower()
                
                # Only include Ollama models if use_ollama is True
                if provider == "ollama" and not use_ollama:
                    continue
                
                if provider not in providers_seen and len(selected_models) < models_count:
                    selected_models.append(model)
                    providers_seen.add(provider)
            
            # If we need more models, add additional ones
            remaining_slots = models_count - len(selected_models)
            if remaining_slots > 0:
                remaining_models = [m for m in cloud_models + ollama_models if m not in selected_models]
                
                # Only include Ollama models if use_ollama is True
                if not use_ollama:
                    remaining_models = [m for m in remaining_models if m.get("provider", "").lower() != "ollama"]
                
                # Add remaining models up to the requested count
                selected_models.extend(remaining_models[:remaining_slots])
        else:
            # Simple selection: use the first models up to the requested count
            all_models = cloud_models
            
            # Add Ollama models if requested
            if use_ollama:
                all_models.extend(ollama_models)
            
            selected_models = all_models[:models_count]
        
        return selected_models

    def _validate_numeric_params(self, params: Dict[str, Any]) -> List[str]:
        """Validate the numeric inputs the cost/time math depends on.

        Before this check, a negative `models`/`max_tokens` reached the arithmetic
        directly and came out the other end as a negative dollar figure that read like
        a discount, a non-integer `variations` (a string from an un-coerced web form
        field, say) raised a bare TypeError deep inside `_estimate_combinations`, and
        nothing here ever caught either. Validate once, at the boundary every caller
        goes through, and report every problem found rather than stopping at the first.

        Args:
            params: Dictionary of command parameters.

        Returns:
            List of human-readable error strings; empty if all checked values are valid.
        """
        errors: List[str] = []

        def check(name: str, value: Any, *, minimum: int, required: bool = True) -> None:
            if value is None:
                if required:
                    errors.append(f"'{name}' is required")
                return
            # bool is a subclass of int in Python — True/False must not silently pass
            # as 1/0 for a parameter that is supposed to be a combination count.
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f"'{name}' must be a whole number, got {value!r}")
                return
            if value < minimum:
                errors.append(f"'{name}' must be >= {minimum}, got {value}")

        check("models", params.get("models", 2), minimum=1)
        check("instructions", params.get("instructions", 3), minimum=1)
        check("variations", params.get("variations", 2), minimum=0)
        check("max_combinations", params.get("max_combinations"), minimum=1, required=False)
        check("max_workers", params.get("max_workers") or params.get("concurrency"),
              minimum=1, required=False)

        model_params = params.get("parameters", {}) or {}
        check("parameters.max_tokens", model_params.get("max_tokens", 1024), minimum=1)

        return errors

    def estimate_cost(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate the cost and execution time for a command.

        Args:
            params: Dictionary of command parameters.

        Returns:
            Dictionary with cost and time estimates and warnings.
        """
        # Reject bad numeric input before any of it reaches the cost/time arithmetic —
        # see _validate_numeric_params for the concrete failures this prevents. Checked
        # first, ahead of simulate/dry-run, because a caller passing e.g. models=-1
        # deserves the same clear rejection regardless of which mode it was headed for.
        parameter_errors = self._validate_numeric_params(params)
        if parameter_errors:
            return {
                "total_cost": None,
                "time_estimate_min": None,
                "time_estimate_max": None,
                "cost_warning_level": None,
                "time_warning_level": None,
                "cost_breakdown": {},
                "time_breakdown": {},
                "token_estimate": None,
                "combinations_estimate": None,
                "config_errors": list(self.config_errors),
                "parameter_errors": parameter_errors,
                "is_invalid": True
            }

        # If simulate is enabled, zero cost
        if params.get("simulate", False):
            return {
                "total_cost": 0.0,
                "time_estimate_min": 0.5,
                "time_estimate_max": 1.0,
                "cost_warning_level": None,
                "time_warning_level": None,
                "cost_breakdown": {},
                "time_breakdown": {},
                "token_estimate": 0,
                "combinations_estimate": 0,
                "config_errors": list(self.config_errors),
                "is_simulation": True
            }

        # If dry run is enabled, zero cost
        if params.get("dry_run", False):
            return {
                "total_cost": 0.0,
                "time_estimate_min": 0.1,
                "time_estimate_max": 0.2,
                "cost_warning_level": None,
                "time_warning_level": None,
                "cost_breakdown": {},
                "time_breakdown": {},
                "token_estimate": 0,
                "combinations_estimate": 0,
                "config_errors": list(self.config_errors),
                "is_dry_run": True
            }

        # Get the number of combinations
        combinations = self._estimate_combinations(params)
        
        # Get the available models
        selected_models = self._get_available_models_for_params(params)
        
        # Check if models were found
        if not selected_models:
            # No valid models found, use fallbacks
            selected_models = list(self._get_fallback_models_info().values())
        
        # Calculate token estimates per prompt
        prompt_tokens = self._estimate_prompt_tokens(params)
        response_tokens = self._estimate_response_tokens(params)
        
        # Calculate total tokens and costs per model
        total_cost = 0.0
        total_time_min = 0.0
        total_time_max = 0.0
        cost_breakdown = {}
        time_breakdown = {}
        total_tokens = 0
        
        # Split combinations evenly among models
        combinations_per_model = [combinations // len(selected_models)] * len(selected_models)
        for i in range(combinations % len(selected_models)):
            combinations_per_model[i] += 1
        
        # Calculate cost and time for each model
        for i, model_info in enumerate(selected_models):
            model_id = model_info.get("id", f"model_{i+1}")
            model_name = model_info.get("name", model_id)
            
            # Get cost rate for this model
            cost_rate = self._get_model_cost_rate(model_info)
            
            # Calculate tokens for this model's share of combinations
            model_combinations = combinations_per_model[i]
            
            model_prompt_tokens = prompt_tokens * model_combinations
            model_response_tokens = response_tokens * model_combinations
            model_total_tokens = model_prompt_tokens + model_response_tokens
            
            # Calculate cost in USD
            model_input_cost = (model_prompt_tokens / 1000000) * cost_rate["input"]
            model_output_cost = (model_response_tokens / 1000000) * cost_rate["output"]
            model_cost = model_input_cost + model_output_cost
            
            # Add to total cost
            total_cost += model_cost
            
            # Calculate estimated processing time
            processing_speed = self._get_model_processing_speed(model_info)
            
            # Calculate time for sequential processing (slower bound)
            sequential_time = (model_total_tokens / processing_speed)
            
            # Add overhead for API latency and system processing
            overhead_min = 0.1  # Minimum 6 seconds overhead per combination
            overhead_max = 0.2  # Maximum 12 seconds overhead per combination
            
            model_time_min = sequential_time + (overhead_min * model_combinations)
            model_time_max = sequential_time + (overhead_max * model_combinations)
            
            # Update total time estimates
            total_time_min += model_time_min
            total_time_max += model_time_max
            
            # Add to breakdowns
            cost_breakdown[model_name] = {
                "cost": model_cost,
                "prompt_tokens": model_prompt_tokens,
                "response_tokens": model_response_tokens,
                "total_tokens": model_total_tokens,
                "combinations": model_combinations
            }
            
            time_breakdown[model_name] = {
                "time_min": model_time_min,
                "time_max": model_time_max,
                "tokens_per_minute": processing_speed,
                "combinations": model_combinations
            }
            
            total_tokens += model_total_tokens
        
        # `total_time_min`/`total_time_max` above is the SERIAL total: every model's own
        # processing time, added together as if the models ran one after another. Real
        # execution runs all combinations through one shared worker pool (see
        # DEFAULT_CONCURRENCY), so that sum is not the wall-clock estimate — it is what
        # the run would take with a concurrency of exactly one. Approximate the actual
        # makespan as total work divided by the effective number of workers, capped at
        # the number of combinations (more workers than work does not speed it up
        # further). This is an approximation — it assumes work divides evenly across
        # workers — not a scheduler simulation.
        requested_concurrency = params.get("max_workers") or params.get("concurrency") or DEFAULT_CONCURRENCY
        effective_workers = max(1, min(int(requested_concurrency), max(combinations, 1)))
        makespan_min = total_time_min / effective_workers
        makespan_max = total_time_max / effective_workers

        # Determine warning levels
        cost_warning_level = None
        for level, threshold in sorted(COST_WARNING_THRESHOLDS.items(), key=lambda x: x[1]):
            if total_cost >= threshold:
                cost_warning_level = level

        # Use the max time for warning level determination — the makespan, since that is
        # what a user waiting on the run actually experiences.
        time_warning_level = None
        for level, threshold in sorted(TIME_WARNING_THRESHOLDS.items(), key=lambda x: x[1]):
            if makespan_max >= threshold:
                time_warning_level = level

        return {
            "total_cost": round(total_cost, 2),
            "time_estimate_min": round(makespan_min, 2),
            "time_estimate_max": round(makespan_max, 2),
            # Kept, but labelled separately and not used for warnings: the "if this ran
            # with a single worker" total, in case a caller wants it. Never present this
            # as the wall-clock estimate — that was finding 6 in the 2026-09-03 audit.
            "sequential_time_min": round(total_time_min, 2),
            "sequential_time_max": round(total_time_max, 2),
            "concurrency_assumed": effective_workers,
            "cost_warning_level": cost_warning_level,
            "time_warning_level": time_warning_level,
            "cost_breakdown": cost_breakdown,
            "time_breakdown": time_breakdown,
            "token_estimate": total_tokens,
            "combinations_estimate": combinations,
            "config_errors": list(self.config_errors)
        }
    
    def _estimate_combinations(self, params: Dict[str, Any]) -> int:
        """Estimate the number of combinations based on parameters.
        
        Args:
            params: Dictionary of command parameters.
            
        Returns:
            Estimated number of combinations.
        """
        # Extract key parameters
        models_count = params.get("models", 2)
        instructions_count = params.get("instructions", 3)
        variations_count = params.get("variations", 2)
        max_combinations = params.get("max_combinations")
        
        # Extract domains count - check for domains list first, then fallback
        domains_count = 1  # Default fallback
        if params.get("domains"):
            # Handle list of domain IDs
            domains_list = params.get("domains")
            if isinstance(domains_list, list):
                domains_count = len(domains_list)
            else:
                domains_count = 1
        elif params.get("domain"):
            # Handle single domain
            domains_count = 1
        
        # Calculate the total possible combinations
        # Formula matches main.py combination generation: templates × domains × queries × models
        # where queries = (1 + variations_count) to account for original + variations
        total_combinations = models_count * instructions_count * domains_count * (1 + variations_count)
        
        # If max_combinations is set, use that as the limit
        if max_combinations is not None and max_combinations > 0:
            return min(total_combinations, max_combinations)
        
        return total_combinations
    
    def get_warning_message(self, estimate: Dict[str, Any]) -> Optional[str]:
        """Get a warning message based on cost and time estimates.
        
        Args:
            estimate: Dictionary with cost and time estimates.
            
        Returns:
            Warning message or None if no warning is needed.
        """
        # Invalid input means nothing below was computed — say so instead of formatting
        # None values into a warning that looks like a real (if boring) estimate.
        if estimate.get("is_invalid"):
            errors = estimate.get("parameter_errors") or ["invalid parameters"]
            return "INVALID PARAMETERS — no estimate was computed:\n" + "\n".join(f"  - {e}" for e in errors)

        warnings = []
        config_errors = estimate.get("config_errors") or []
        if config_errors:
            # This is the visible half of finding 1 (2026-09-03 audit): a config that
            # could not be read must not produce a price quote that looks as trustworthy
            # as one built from the models that will actually run.
            warnings.append(
                "CONFIGURATION WARNING: the model configuration could not be read, so "
                "this estimate falls back to a hardcoded reference portfolio that may "
                "not match the models this run will actually use:")
            warnings.extend(f"  - {e}" for e in config_errors)

        # Simulation or dry run has no cost/time warnings, but a config problem is real
        # regardless of mode.
        if estimate.get("is_simulation") or estimate.get("is_dry_run"):
            return "\n".join(warnings) if warnings else None

        cost_warning = estimate.get("cost_warning_level")
        time_warning = estimate.get("time_warning_level")
        total_cost = estimate.get("total_cost", 0)
        time_max = estimate.get("time_estimate_max", 0)
        combinations = estimate.get("combinations_estimate", 0)

        # Cost warnings
        if cost_warning == "very_high":
            warnings.append(f"VERY HIGH COST: This operation will cost approximately ${total_cost:.2f} in API calls")
        elif cost_warning == "high":
            warnings.append(f"HIGH COST: This operation will cost approximately ${total_cost:.2f} in API calls")
        elif cost_warning == "warning":
            warnings.append(f"COST WARNING: This operation will cost approximately ${total_cost:.2f} in API calls")
        elif cost_warning == "notice":
            warnings.append(f"COST NOTICE: This operation will cost approximately ${total_cost:.2f} in API calls")
        
        # Time warnings
        if time_warning == "very_high":
            warnings.append(f"VERY LONG EXECUTION: This operation may take up to {math.ceil(time_max)} minutes to complete")
        elif time_warning == "high":
            warnings.append(f"LONG EXECUTION: This operation may take up to {math.ceil(time_max)} minutes to complete")
        elif time_warning == "warning":
            warnings.append(f"TIME WARNING: This operation may take up to {math.ceil(time_max)} minutes to complete")
        elif time_warning == "notice":
            warnings.append(f"TIME NOTICE: This operation may take several minutes to complete")
        
        # Suggestion for reducing cost/time if we have high warnings
        if cost_warning in ["high", "very_high"] or time_warning in ["high", "very_high"]:
            suggestions = []
            
            # If we have many combinations, suggest reducing them
            if combinations > 10:
                suggestions.append(f"Reducing combinations from {combinations} to {combinations // 2} would approximately halve the cost and time")
            
            # Suggest simulation mode for testing
            suggestions.append("Use --simulate flag for testing without incurring API costs")
            
            # Add suggestions to warning
            if suggestions:
                warnings.append("Suggestions:")
                warnings.extend([f"  - {s}" for s in suggestions])
        
        if warnings:
            return "\n".join(warnings)
        
        return None
    
    def get_cost_indicator(self, estimate: Dict[str, Any]) -> str:
        """Get a visual indicator of cost level.
        
        Args:
            estimate: Dictionary with cost and time estimates.
            
        Returns:
            String with a visual indicator of cost level.
        """
        if estimate.get("is_invalid"):
            # total_cost is None here — formatting it as currency would raise TypeError,
            # trading one invisible failure (silent bad estimate) for a crashing one.
            return "N/A (invalid parameters)"
        if estimate.get("is_simulation") or estimate.get("is_dry_run"):
            return "🔄 (No API cost - simulation mode)"

        cost_warning = estimate.get("cost_warning_level")
        total_cost = estimate.get("total_cost", 0)
        
        if cost_warning == "very_high":
            return f"💰💰💰💰 (${total_cost:.2f})"
        elif cost_warning == "high":
            return f"💰💰💰 (${total_cost:.2f})"
        elif cost_warning == "warning":
            return f"💰💰 (${total_cost:.2f})"
        elif cost_warning == "notice":
            return f"💰 (${total_cost:.2f})"
        else:
            return f"$ (${total_cost:.2f})"
    
    def get_time_indicator(self, estimate: Dict[str, Any]) -> str:
        """Get a visual indicator of time level.
        
        Args:
            estimate: Dictionary with cost and time estimates.
            
        Returns:
            String with a visual indicator of time level.
        """
        if estimate.get("is_invalid"):
            # time_estimate_min/max are None here — math.ceil(None) would raise.
            return "N/A (invalid parameters)"
        if estimate.get("is_simulation") or estimate.get("is_dry_run"):
            return "⏱️ (Quick - simulation mode)"

        time_warning = estimate.get("time_warning_level")
        time_min = estimate.get("time_estimate_min", 0)
        time_max = estimate.get("time_estimate_max", 0)
        
        # Format time range
        time_range = f"{math.ceil(time_min)}-{math.ceil(time_max)} min" if time_min != time_max else f"{math.ceil(time_max)} min"
        
        if time_warning == "very_high":
            return f"⏱️⏱️⏱️⏱️ ({time_range})"
        elif time_warning == "high":
            return f"⏱️⏱️⏱️ ({time_range})"
        elif time_warning == "warning":
            return f"⏱️⏱️ ({time_range})"
        elif time_warning == "notice":
            return f"⏱️ ({time_range})"
        else:
            return f"⏱️ (< 2 min)"
