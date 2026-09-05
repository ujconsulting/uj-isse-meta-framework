#!/usr/bin/env python3
"""
ISEE Meta Framework - Web Demo Application
Minimalist web UI for investor demonstrations showcasing the ISEE configuration capabilities.
"""

import os
import sys
import json
import re
import secrets
import subprocess
import threading
import time
import logging

# Force UTF-8 on this process's own streams before anything logs or prints.
#
# dev-server.sh redirects stdout to a file, so Windows picks cp1252 and any emoji
# in a log line raises UnicodeEncodeError. It happened to work only because
# `from main import ...` further down runs main.py's reconfigure as a side effect
# of import — an accident that would end the moment that import moved or went away.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import markdown

# Import existing ISEE components
from cost_estimation import CostEstimator
from cognitive_framework_visualizer import CognitiveFrameworkVisualizer
from openrouter_model_collections import OpenRouterModelCollections
# Legacy imports removed - these components have been archived
from main import ISEEGuardrails
from domain_manager import DomainManager, create_default_domains
from openrouter_rankings_service import OpenRouterRankingsService
# Removed: HTML report generation - using markdown display only

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.urandom(24)

# Configure logging for debugging.
#
# encoding="utf-8" on the file handler is not cosmetic. This module logs the child
# process's output verbatim, and that output contains emoji; without it the handler
# encodes with the Windows locale codec, every such line raises UnicodeEncodeError inside
# logging, and the record is replaced by a "--- Logging error ---" block. 24 of them
# appeared in a single three-minute session. Losing log lines is precisely how the
# preceding defects stayed invisible for so long.
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('isee-ui.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ISEEWebDemo:
    """Web demo controller that leverages existing ISEE backend logic"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ISEEWebDemo")
        self.cost_estimator = CostEstimator()
        self.framework_visualizer = CognitiveFrameworkVisualizer()
        self.model_collections = OpenRouterModelCollections()
        # Legacy components removed - dashboard and parameter_context archived
        self.guardrails = ISEEGuardrails()
        self.execution_status = {}
        # Removed: HTML report generator - using markdown display only
        
        # Initialize rankings service
        self.rankings_service = OpenRouterRankingsService()
        
        # Initialize domain manager with real domains
        self.domain_manager = DomainManager()
        self._load_actual_domains()
        
        # Initialize LLM collections
        self.llm_collections = {}
        self._load_llm_collections()
        
        self.logger.info("ISEEWebDemo initialized successfully")
        
    def get_cognitive_frameworks(self, complexity_level: str = "all") -> List[Dict[str, Any]]:
        """Get cognitive frameworks with icons and descriptions"""
        # Handle "all" complexity level by getting all frameworks
        if complexity_level == "all":
            all_frameworks = []
            for level in ["basic", "advanced", "expert"]:
                all_frameworks.extend(self.framework_visualizer.get_frameworks_for_complexity(level))
            frameworks = all_frameworks
        else:
            frameworks = self.framework_visualizer.get_frameworks_for_complexity(complexity_level)
        framework_data = []
        
        framework_icons = {
            "ins_analytical": "🔍",
            "ins_creative": "💡", 
            "ins_critical": "⚖️",
            "ins_integrative": "🔗",
            "ins_pragmatic": "🔧",
            "ins_first_principles": "🧱",
            "ins_systems": "🌐",
            "ins_contrarian": "🔄",
            "ins_historical": "📚",
            "ins_futurist": "🚀",
            "ins_disruption": "⚡"
        }
        
        framework_descriptions = {
            "ins_analytical": "Analytical - Break down problems systematically",
            "ins_creative": "Creative - Generate novel solutions and ideas",
            "ins_critical": "Critical - Evaluate assumptions and evidence",
            "ins_integrative": "Integrative - Synthesize multiple perspectives",
            "ins_pragmatic": "Pragmatic - Focus on practical implementations",
            "ins_first_principles": "First Principles - Reason from fundamental truths",
            "ins_systems": "Systems - Consider holistic relationships",
            "ins_contrarian": "Contrarian - Challenge conventional wisdom",
            "ins_historical": "Historical - Learn from past patterns",
            "ins_futurist": "Futurist - Explore future possibilities",
            "ins_disruption": "Disruption - Challenge all existing assumptions"
        }
        
        for framework_id, _ in frameworks:
            framework_data.append({
                "id": framework_id,
                "icon": framework_icons.get(framework_id, "🔍"),
                "name": framework_descriptions.get(framework_id, framework_id),
                "description": framework_descriptions.get(framework_id, framework_id)
            })
        
        return framework_data
    
    def get_individual_models(self, use_cached: bool = True, strategic_only: bool = False) -> List[Dict[str, Any]]:
        """Get individual LLM models for manual selection.
        
        Args:
            use_cached: Whether to use cached rankings (True) or force update (False)
            strategic_only: Whether to return only strategically curated models (True) or all models (False)
        """
        try:
            # ⛔ The CONFIGURATION decides which models exist. Not the rankings cache.
            #
            # This used to consult OpenRouterRankingsService first and fall back to the
            # configuration only when its cache was stale. That inverted the authority:
            # one call to /api/models-fresh repopulated the cache from the live
            # OpenRouter leaderboard, and the picker then offered 20 models of which 19
            # were not configured — while `strategic_only` collapsed to a single card,
            # because ui_priority exists only on configured entries. The framework can
            # only call what openrouter_config.json defines; offering anything else
            # produces a run that fails at call time for a reason the user cannot see.
            #
            # Rankings are still welcome as METADATA — position and top-performer flags
            # are merged onto configured models below — but never as a source of models.
            # (CLAUDE.md has described this service as "legacy, no longer used" for some
            # time; it was in fact the primary source.)
            models = self._get_fallback_models()

            if use_cached and models:
                try:
                    cache_status = self.rankings_service.get_cache_status()
                    if cache_status["cache_exists"] and not cache_status["needs_update"]:
                        cache_data = self.rankings_service._load_cache()
                        ranked = {}
                        for i, rm in enumerate(cache_data.models if cache_data else []):
                            key = rm.get("model_param") or rm.get("id")
                            if key:
                                ranked[key] = i + 1
                        merged = 0
                        for m in models:
                            pos = ranked.get(m.get("model_param")) or ranked.get(m.get("id"))
                            if pos:
                                m["ranking_position"] = pos
                                m["is_top_performer"] = pos <= 10
                                merged += 1
                        self.logger.info(
                            "Merged ranking metadata onto %d of %d configured models",
                            merged, len(models))
                except Exception as e:
                    # Ranking metadata is a nicety; its absence must not affect which
                    # models are offered.
                    self.logger.warning("Could not merge ranking metadata: %s", e)

            if strategic_only:
                models = self._filter_strategic_models(models)
                self.logger.info(f"Filtered to {len(models)} strategic models")

            return models

            # Fallback to config-based models + hardcoded fallback
            self.logger.info("Using fallback model loading approach")
            fallback_models = self._get_fallback_models()
            
            # Apply strategic filtering if requested
            if strategic_only:
                fallback_models = self._filter_strategic_models(fallback_models)
                self.logger.info(f"Filtered fallback to {len(fallback_models)} strategic models")
            
            return fallback_models
            
        except Exception as e:
            self.logger.error(f"Error in get_individual_models: {e}")
            fallback_models = self._get_fallback_models()
            
            # Apply strategic filtering if requested
            if strategic_only:
                fallback_models = self._filter_strategic_models(fallback_models)
                self.logger.info(f"Filtered error fallback to {len(fallback_models)} strategic models")
            
            return fallback_models
    
    def _filter_strategic_models(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter models to return only strategically curated ones based on openrouter_config.json metadata."""
        try:
            # Load openrouter_config.json to get strategic model metadata
            with open('openrouter_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Create lookup of strategic models by ID and model_param
            strategic_ids = set()
            strategic_params = set()
            
            for model in config.get('models', {}).get('api_models', []):
                # Skip disabled models
                if model.get('disabled', False):
                    continue
                    
                if model.get('ui_priority') == 'strategic':
                    strategic_ids.add(model.get('id'))
                    model_param = model.get('parameters', {}).get('model', '')
                    if model_param:
                        strategic_params.add(model_param)
            
            # Filter input models to only strategic ones and remove duplicates
            strategic_models = []
            seen_model_params = set()  # Track model_params to prevent duplicates
            
            for model in models:
                model_id = model.get('id', '')
                model_param = model.get('model_param', '')
                
                # Check if this model is marked as strategic
                if ((model_id in strategic_ids or model_param in strategic_params) 
                    and model_param not in seen_model_params):
                    strategic_models.append(model)
                    seen_model_params.add(model_param)
                elif model_param in seen_model_params:
                    self.logger.debug(f"Skipping duplicate strategic model: {model.get('name', '')} ({model_param})")
            
            self.logger.debug(f"Strategic filtering: {len(strategic_models)} out of {len(models)} models (duplicates removed)")
            return strategic_models
            
        except Exception as e:
            self.logger.error(f"Error filtering strategic models: {e}")
            # Return first 12 models as fallback
            return models[:12]
    
    def _get_fallback_models(self) -> List[Dict[str, Any]]:
        """Get models from config file and hardcoded fallback list."""
        try:
            with open('openrouter_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            models = []
            for model in config.get('models', {}).get('api_models', []):
                # Extract provider from model parameter
                model_param = model.get('parameters', {}).get('model', '')
                provider = model_param.split('/')[0] if '/' in model_param else 'unknown'
                
                # Determine cost tier from features
                cost_tier = model.get('cost_tier', 'medium')
                if cost_tier == 'premium_plus':
                    cost_tier = 'premium'
                
                models.append({
                    "id": model.get('id'),
                    "name": model.get('name'),
                    "provider": provider.title(),
                    "model_param": model_param,
                    "cost_tier": cost_tier,
                    "features": model.get('features', []),
                    "description": f"{provider.title()} model",
                    "ui_priority": model.get('ui_priority'),
                    "curation_tags": model.get('curation_tags', []),
                    "willison_tier": model.get('willison_tier')
                })
            
            # ⛔ No padding with hardcoded model ids.
            #
            # This used to top the list up to 20 entries from a literal list of "top
            # performers" (google/gemini-2.0-flash, anthropic/claude-3.7-sonnet and
            # others). Those ids age independently of openrouter_config.json, so the UI
            # kept offering models the framework could no longer call — and a deliberate
            # 14-model portfolio silently became a 20-model one, six of them stale.
            # The configuration is the single source of truth for what is on offer.
            
            # Add dynamic Ollama models if available
            try:
                api_status = self._detect_apis()
                ollama_models = api_status.get("ollama_models", [])
                if ollama_models:
                    existing_ids = {m["id"] for m in models}
                    for ollama_model in ollama_models:
                        # Use the model name directly as the ID (this matches what users select)
                        model_id = ollama_model
                        if model_id not in existing_ids:
                            models.append({
                                "id": model_id,
                                "name": f"Ollama {model_id}",
                                "provider": "Ollama",
                                "model_param": model_id,
                                "cost_tier": "free",
                                "features": ["local", "free", "dynamic"],
                                "description": f"Local Ollama model: {model_id}"
                            })
                            self.logger.debug(f"Added dynamic Ollama model to list: {model_id}")
            except Exception as e:
                self.logger.error(f"Error adding Ollama models: {e}")
            
            # Don't sort - preserve the order from config file which follows top performers list
            # Add fallback ranking metadata for consistency with rankings service
            for i, model in enumerate(models):
                model["ranking_position"] = None  # Config models don't have rankings
                model["is_top_performer"] = i < 10  # First 10 from config get highlighting
            
            return models
            
        except Exception as e:
            print(f"Error loading models: {e}")
            # ⛔ No stale hardcoded fallback list here either.
            #
            # This returned twenty obsolete model ids whenever the configuration failed
            # to load, so a broken openrouter_config.json presented as a working model
            # picker whose every choice fails at call time. An empty list makes the real
            # problem visible where it happens.
            self.logger.error(
                "Could not load models from openrouter_config.json (%s). Returning an "
                "empty model list: the configuration is the only source of truth for "
                "what this framework can call.", e,
            )
            return []
    
    def _domain_flags(self, selected_domains: Optional[List[str]],
                      single_domain: Optional[str] = None) -> List[str]:
        """Turn the run's domains into command-line flags.

        `--domain` is validated by the engine and aborts the run if the name is
        unknown; `--dynamic-domain` takes any name and uses it as context. So a
        domain goes on the validated flag only when the engine can actually
        resolve it, and everything else — in particular whatever
        `/api/suggest-domains` generated for this query — goes on the dynamic one.
        """
        flags: List[str] = []
        for candidate in (selected_domains or ([single_domain] if single_domain else [])):
            if not candidate:
                continue
            explicit_dynamic = candidate.startswith('dynamic:')
            name = candidate[len('dynamic:'):] if explicit_dynamic else candidate
            if not name:
                continue
            if not explicit_dynamic and self._is_known_domain(name):
                flags.extend(["--domain", name])
            else:
                flags.extend(["--dynamic-domain", name])
        return flags

    @staticmethod
    def resolve_inside(base: "Path", *parts: str) -> "Path":
        """Resolve a path under `base`, or raise ValueError if it escapes.

        Containment is decided AFTER resolution and on path components, never on
        the string. Two ways the previous checks were got around, both confirmed
        against the running app on 05.09.2026:

        * `/api/raw-response` rejected ".." and a leading "/". On Windows an
          absolute drive path (a drive letter, a colon, then the path) contains
          neither, and `os.path.join` DISCARDS everything before an absolute
          second argument — so the run directory disappeared and the file was
          read and returned with HTTP 200.
        * `/api/download-file` resolved correctly and then compared with
          `str(path).startswith(str(base))`, so `data/output_backup/...` passes
          because its name begins with `data/output`.

        `Path.relative_to` compares components, so neither trick survives it.
        """
        from pathlib import Path as _Path

        base = _Path(base).resolve()
        candidate = _Path(base, *parts).resolve()
        try:
            candidate.relative_to(base)
        except ValueError:
            raise ValueError(f"path escapes {base}")
        return candidate

    def _is_known_domain(self, identifier: str) -> bool:
        """Can the engine resolve this domain by id or by exact name?

        Mirrors the lookup in `main.py`: an id match, or a case-insensitive match
        on the display name. Both sides build their domain manager from
        `create_default_domains()`, so the two lists agree. When in doubt the
        answer must be False — an unknown name passed as `--domain` aborts the
        run, whereas a known one passed as `--dynamic-domain` merely loses the
        stored description.
        """
        wanted = (identifier or "").strip().lower()
        if not wanted:
            return False
        for domain in self.domain_manager.list_domains():
            if domain.id.lower() == wanted or domain.name.lower() == wanted:
                return True
        return False

    def _load_actual_domains(self):
        """Load domains from actual ISEE domain system"""
        # Load default domains (now includes all 15 domains: Core, Technical Writing, and Learning Design)
        for domain in create_default_domains():
            self.domain_manager.add_domain(domain)
    
    def _get_real_domains(self) -> Dict[str, List[Dict[str, str]]]:
        """Get actual domains organized by category with IDs and names"""
        # Convert DomainManager domains to web UI format with IDs
        domains_by_category = {
            "Core Domains": [],
            "Technical Writing": [],
            "Learning Design": [],
        }
        
        # domains is a dictionary, so iterate over values
        for domain in self.domain_manager.domains.values():
            domain_info = {
                "id": domain.id,
                "name": domain.name,
                "description": domain.description
            }
            
            # Categorize domains based on their IDs and source files
            if domain.id in ["domain_technical_writing", "domain_knowledge_management", "domain_content_strategy", "domain_ai_writing", "domain_developer_docs"]:
                domains_by_category["Technical Writing"].append(domain_info)
            elif domain.id in ["domain_instructional_design", "domain_elearning", "domain_learning_experience", "domain_corporate_training", "domain_assessment_design"]:
                domains_by_category["Learning Design"].append(domain_info)
            else:
                # Default domains and others go to Core Domains
                domains_by_category["Core Domains"].append(domain_info)
        
        # Remove empty categories
        return {k: v for k, v in domains_by_category.items() if v}
    
    def get_knowledge_domains(self) -> Dict[str, List[Dict[str, str]]]:
        """Get knowledge domains organized by category with IDs and names"""
        return self._get_real_domains()
    
    def _load_llm_collections(self):
        """Load LLM collections from JSON configuration"""
        try:
            collections_file = Path("llm_collections.json")
            if collections_file.exists():
                with open(collections_file, 'r', encoding='utf-8') as f:
                    collections_data = json.load(f)
                self.llm_collections = collections_data.get("collections", {})
                self.logger.info(f"Loaded {len(self.llm_collections)} LLM collections")
            else:
                self.logger.warning("llm_collections.json not found, using empty collections")
                self.llm_collections = {}
        except Exception as e:
            self.logger.error(f"Error loading LLM collections: {e}")
            self.llm_collections = {}
    
    def get_llm_collections(self) -> Dict[str, Any]:
        """Get LLM collections for the web UI"""
        return self.llm_collections
    
    def resolve_collection_models(self, collection_id: str) -> List[str]:
        """Resolve a collection ID to a list of model IDs"""
        if collection_id not in self.llm_collections:
            self.logger.error(f"Collection '{collection_id}' not found")
            return []
        
        collection = self.llm_collections[collection_id]
        model_ids = []
        
        # Extract model IDs from collection - use model_param for OpenRouter models
        for model in collection.get("models", []):
            # Use model_param (actual OpenRouter ID) for models with "rankings" source
            # Use id (internal config ID) for models with "config" source
            if model.get("source") == "rankings":
                model_ids.append(model["model_param"])
            else:
                model_ids.append(model["id"])
        
        self.logger.info(f"Resolved collection '{collection_id}' to {len(model_ids)} models: {model_ids}")
        return model_ids
    
    def estimate_execution_cost(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate cost and resource requirements for given parameters"""
        try:
            # Create a simple parameter object for cost estimation
            class SimpleParams:
                def __init__(self, params_dict):
                    self._params = params_dict
                    for key, value in params_dict.items():
                        setattr(self, key, value)
                
                def get(self, key, default=None):
                    """Dictionary-like get method for compatibility with cost estimator"""
                    return self._params.get(key, default)
            
            # Convert web parameters to format expected by cost estimator
            converted_params = self._convert_web_params_to_isee(parameters)
            param_obj = SimpleParams(converted_params)
            
            # Get cost estimate using existing logic
            estimate = self.cost_estimator.estimate_cost(param_obj)
            
            # Add resource guardrails check
            limits_check = self.guardrails.validate_command_limits(param_obj)
            
            return {
                **estimate,
                "guardrails": limits_check,
                "resource_warnings": limits_check.get("warnings", []),
                "within_limits": limits_check.get("within_limits", True)
            }
        except Exception as e:
            # Log the actual error for debugging
            self.logger.error(f"Cost estimation failed, falling back to simplified calculation: {str(e)}")
            self.logger.debug(f"Parameters that caused error: {parameters}")
            
            # Fallback calculation for demo
            combinations = parameters.get("max_combinations", 30)
            cost_per_combination = 0.08
            return {
                "total_cost": combinations * cost_per_combination,
                "time_estimate_min": combinations * 0.5,
                "time_estimate_max": combinations * 1.2,
                "combinations_estimate": combinations,
                "cost_warning_level": "notice" if combinations <= 50 else "warning",
                "resource_warnings": ["Demo mode: Using simplified cost calculation"],
                "within_limits": combinations <= 100
            }
    
    def generate_command_preview(self, parameters: Dict[str, Any]) -> str:
        """Generate the terminal command that would be executed"""
        import shlex
        
        cmd_parts = ["python", "main.py"]
        
        # Add query (properly escaped)
        if parameters.get("query"):
            cmd_parts.extend(["--query", parameters["query"]])
        
        # Add selected domains (properly escaped)
        selected_domains = parameters.get("selected_domains", [])
        if selected_domains:
            # Add multiple --domain flags for accurate command preview
            for domain in selected_domains:
                cmd_parts.extend(["--domain", domain])
        
        # Add cognitive frameworks
        frameworks = parameters.get("cognitive_frameworks", [])
        if frameworks:
            framework_list = ",".join(frameworks)
            cmd_parts.extend(["--instruction-templates", framework_list])
        
        # Add model configuration - handle both collections and individual selection
        selected_models = parameters.get("selected_models", [])
        
        # Check for collection selection first (same logic as execution)
        if parameters.get("selected_collection"):
            collection_id = parameters["selected_collection"]
            collection_models = self.resolve_collection_models(collection_id)
            if collection_models:
                selected_models = collection_models
                self.logger.debug(f"Preview: Using collection '{collection_id}' with {len(collection_models)} models")
            else:
                self.logger.warning(f"Preview: Collection '{collection_id}' resolution failed")
        
        if selected_models:
            # Process model parameters (same as execution)
            processed_models = self._process_model_params(selected_models)
            
            # Determine config based on model types (same logic as execution)
            api_status = self._detect_apis()
            ollama_models = api_status.get("ollama_models", [])
            # Use consolidated OpenRouter config for all model combinations (per June 2025 config consolidation)
            cmd_parts.extend(["--config", "openrouter_config.json"])
            
            cmd_parts.extend(["--models", str(len(processed_models))])
            # Add processed models to preview
            cmd_parts.extend(["--selected-models", ",".join(processed_models)])
        
        # Add execution settings
        if parameters.get("variations"):
            cmd_parts.extend(["--variations", str(parameters["variations"])])
        
        if parameters.get("max_combinations"):
            cmd_parts.extend(["--max-combinations", str(parameters["max_combinations"])])
        
        # Sampling method removed - now uses optimal default (exhaustive + balanced-models)
        
        # Add output format (see the note at the execution site below)
        cmd_parts.extend(["--output-format",
                          parameters.get("output_format") or "markdown"])
        
        # Note: No dry-run flag added - show the actual command that will be executed
        
        # Properly escape the command for shell display
        return " ".join(shlex.quote(part) for part in cmd_parts)
    
    def execute_isee_command(self, parameters: Dict[str, Any], execution_id: str, session_api_key: str = None) -> Dict[str, Any]:
        """Execute ISEE command and track progress"""
        self.logger.info(f"Starting execution {execution_id} with parameters: {parameters}")
        
        # Store execution parameters for performance tracking
        if not hasattr(self, 'execution_parameters'):
            self.execution_parameters = {}
        stored_params = parameters.copy()
        stored_params['session_api_key'] = session_api_key
        # Default to generating reports for ISEE-UI executions if not specified
        if 'generate_report' not in stored_params:
            stored_params['generate_report'] = True  # Enable by default for ISEE-UI
        self.execution_parameters[execution_id] = stored_params
        
        try:
            # Validate parameters before execution
            validation_errors = self._validate_parameters(parameters)
            if validation_errors:
                error_message = "Parameter validation failed: " + "; ".join(validation_errors)
                self.logger.error(f"Validation failed for execution {execution_id}: {validation_errors}")
                self.execution_status[execution_id] = {
                    "status": "error",
                    "progress": 0,
                    "message": error_message,
                    "start_time": datetime.now().isoformat(),
                    "results_file": None,
                    "validation_errors": validation_errors
                }
                return self.execution_status[execution_id]
            
            # Update status
            self.execution_status[execution_id] = {
                "status": "starting",
                "progress": 0,
                "message": "Preparing execution...",
                "start_time": datetime.now().isoformat(),
                "results_file": None
            }
            
            # Convert Web UI parameters to format expected by ISEE backend
            converted_params = self._convert_web_params_to_isee(parameters)
            self.logger.debug(f"Converted parameters: {converted_params}")
            
            # Build command properly for subprocess using converted parameters
            cmd = ["python", "main.py"]
            self.logger.debug(f"Building command for execution {execution_id}")
            
            # Add query (properly handled)
            if converted_params.get("query"):
                cmd.extend(["--query", converted_params["query"]])
                self.logger.debug(f"Added query: {converted_params['query'][:100]}...")
            
            # Add selected domains (support both static and dynamic domains)
            #
            # Whether a domain has to pass validation depends on the domain, not on
            # which models are in play. This used to be decided by `strategic_models`:
            # once the UI began sending an explicit model selection that flag went
            # false, every AI-suggested domain went out as a validated `--domain`, and
            # the engine rejected the first one — killing the run before a single call
            # was made, while the interface still reported it as completed.
            #
            # `--domain` is only correct for a domain the engine actually knows;
            # anything else is contextual guidance and belongs on `--dynamic-domain`,
            # which is exactly what `/api/suggest-domains` produces.
            domain_flags = self._domain_flags(
                converted_params.get("domains", []),
                converted_params.get("domain"),
            )
            cmd.extend(domain_flags)
            if domain_flags:
                self.logger.debug(f"Domain flags: {' '.join(domain_flags)}")
            
            # Add cognitive frameworks - use converted framework IDs instead of Web UI names
            if converted_params.get("instruction_templates"):
                cmd.extend(["--instruction-templates", converted_params["instruction_templates"]])
                self.logger.debug(f"Added framework templates: {converted_params['instruction_templates']}")
            
            # Add provider selection and model configuration
            provider_mode = converted_params.get("provider", "openrouter")
            cmd.extend(["--provider", provider_mode])
            self.logger.debug(f"Using provider: {provider_mode}")
            
            selected_models = converted_params.get("selected_models", [])
            if selected_models:
                self.logger.debug(f"Selected models: {selected_models}")
                
                # Process model parameters 
                processed_models = self._process_model_params(selected_models)
                self.logger.debug(f"Processed models: {processed_models}")
                
                # Use appropriate config file based on provider
                if provider_mode == "globant":
                    config_file = "globant_enterprise_config.json"
                else:
                    config_file = "openrouter_config.json"
                cmd.extend(["--config", config_file])
                self.logger.debug(f"Using config file: {config_file}")
                
                # Pass specific model selections to CLI using processed model params
                cmd.extend(["--selected-models", ",".join(processed_models)])
                cmd.extend(["--models", str(len(processed_models))])
                self.logger.debug(f"Added {len(processed_models)} specific models to command")
            
            # Add execution settings using converted parameters
            # `is not None`, not truthiness. A requested 0 is a request, not an
            # absence: `if params.get('variations')` dropped the flag for 0 exactly
            # as it does for a missing key, so argparse fell back to its own default
            # of 2. Asking for no variations produced two of them — three queries
            # instead of one, and the paid calls that go with them. The opposite of
            # what was asked, and invisible.
            if converted_params.get("variations") is not None:
                cmd.extend(["--variations", str(converted_params["variations"])])
            
            if converted_params.get("max_combinations") is not None:
                cmd.extend(["--max-combinations", str(converted_params["max_combinations"])])
            
            # Sampling method removed - now uses optimal default (exhaustive + balanced-models)
            
            # Always pass the format explicitly and default to markdown, matching
            # main.py (--output-format default="markdown").
            #
            # These two sides disagreed: app.py assumed "json" and SKIPPED the flag
            # for that value, so main.py fell back to its own default and wrote
            # Markdown — into a file app.py had already named isee_result.json. The
            # result was Markdown behind a .json extension: /api/markdown returned
            # 404 because the name did not end in .md, and anything parsing it as
            # JSON failed. Assuming a default instead of stating it is what let the
            # two drift apart.
            cmd.extend(["--output-format",
                        converted_params.get("output_format") or "markdown"])
            
            # Always generate comprehensive result package for Web UI
            cmd.append("--generate-reports")
            cmd.append("--export-csv") 
            cmd.append("--analyze-results")
            cmd.append("--json-progress")  # Enable structured progress output
            cmd.append("--parallel")  # Enable parallel execution by default for Web UI
            
            # Add report format if specified
            if converted_params.get("report_format") and converted_params["report_format"] != "markdown":
                cmd.extend(["--report-format", converted_params["report_format"]])
                
            # Only add no-visualizations if explicitly requested
            if converted_params.get("no_visualizations"):
                cmd.append("--no-visualizations")
            
            # Check if we should use real execution or simulation
            # Use real execution if we have API keys available
            current_api_status = self._detect_apis_with_session_key(session_api_key)
            if not current_api_status.get("any_api", False):
                cmd.append("--simulate")  # Use simulation if no API keys
            
            # Create timestamped run directory (matching CLI behavior)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_dir = Path("data/output") / f"run_{timestamp}"
            run_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine file extension based on output format (following main.py logic)
            output_format = converted_params.get("output_format") or "markdown"
            if output_format == "markdown":
                extension = "md"
            else:
                extension = "json"
            
            # Use standard filename in run directory
            output_file = run_dir / f"isee_result.{extension}"
            cmd.extend(["--output-file", str(output_file)])
            
            # Force CLI to use the same output directory for all reports
            cmd.extend(["--output-directory", str(run_dir)])
            
            # Add enhancement information if available
            enhancement_info = converted_params.get("enhancement_info")
            if enhancement_info:
                # Store the enhancement info as environment variables for the subprocess
                env_enhancement_info = {
                    "ISEE_ORIGINAL_QUERY": enhancement_info.get("originalQuery", ""),
                    "ISEE_ENHANCEMENT_TYPE": enhancement_info.get("enhancementType", ""),
                    "ISEE_ENHANCEMENT_RATIONALE": enhancement_info.get("enhancementRationale", "")
                }
                
                # We'll pass this to the subprocess environment later
                if not hasattr(self, 'pending_enhancement_info'):
                    self.pending_enhancement_info = {}
                self.pending_enhancement_info[execution_id] = env_enhancement_info
                self.logger.info(f"ENHANCEMENT_DEBUG: Stored enhancement info for execution {execution_id}: {env_enhancement_info}")
            else:
                self.logger.info(f"ENHANCEMENT_DEBUG: No enhancement info found in converted_params: {converted_params}")
            
            # Store run directory for generating additional reports
            self.execution_status[execution_id]["run_directory"] = str(run_dir)
            
            # Update status
            self.execution_status[execution_id].update({
                "status": "running",
                "progress": 10,
                "message": "Executing ISEE framework...",
                "command": " ".join(cmd)
            })
            
            # Prepare environment with session API keys
            env = os.environ.copy()
            
            # Add session-stored OpenRouter API key if available
            if session_api_key:
                env['OPENROUTER_API_KEY'] = session_api_key
                self.logger.debug("Added OpenRouter API key from session to environment")
            
            # Add enhancement information to environment if available
            if hasattr(self, 'pending_enhancement_info') and execution_id in self.pending_enhancement_info:
                env.update(self.pending_enhancement_info[execution_id])
                self.logger.debug("Added enhancement info to subprocess environment")
                # Clean up after adding to env
                del self.pending_enhancement_info[execution_id]
            
            # Force Python to be unbuffered for real-time progress monitoring
            env['PYTHONUNBUFFERED'] = '1'
            
            # Log command execution details
            self.logger.info(f"Executing command: {' '.join(cmd)}")
            self.logger.debug(f"Working directory: {Path(__file__).parent}")
            self.logger.debug(f"Environment variables set: {[k for k in env.keys() if 'API_KEY' in k]}")
            
            # Execute command with unbuffered output for real-time monitoring
            # The child writes UTF-8 (main.py reconfigures its streams). Without saying so
            # here, the PARENT decodes with locale.getpreferredencoding(), which is cp1252
            # on Windows — and the consequence is worse than a mangled character.
            #
            # TextIOWrapper decodes in 8 KB chunks, so one undefined byte discards the
            # WHOLE CHUNK, not just its line. main.py prints "🏁 Parallel execution
            # completed" 149 bytes after the `parallel_execution_complete` PROGRESS_JSON
            # line — same chunk — so the run tally was silently lost and
            # succeeded_combinations stayed 0 after three successful calls. The error was
            # swallowed by a broad `except` further down and appeared only as a DEBUG line.
            #
            # errors="replace" is the second half: a decode problem must degrade one
            # character, never a block of progress events. Emoji sit right next to the
            # ❌ failure prints, which is exactly where losing a chunk would matter most.
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,  # Line buffered
                cwd=Path(__file__).parent,
                env=env
            )
            
            self.logger.info(f"Started subprocess with PID {process.pid} for execution {execution_id}")
            
            # Monitor progress and wait for completion
            stdout, stderr = self._monitor_subprocess_progress(process, execution_id)
            
            # main.py's exit code now carries the analysis outcome, not just "the process
            # reached the end":
            #   0 — every combination succeeded
            #   1 — some failed, an analysis was still produced
            #   2 — all failed, nothing was produced
            # Anything else is a crash and belongs in the error branch below. Treating 1
            # and 2 as crashes would throw away the partial results and the distinction
            # this whole path exists to make.
            if process.returncode in (0, 1, 2):
                self.logger.info(f"Execution {execution_id} completed successfully")
                
                # Auto-ingest performance data into database
                run_directory = self.execution_status[execution_id].get("run_directory", "")
                if run_directory:
                    try:
                        from performance_tracker import PerformanceTracker
                        tracker = PerformanceTracker()
                        
                        # Get collection name from parameters
                        collection_name = "Unknown Collection"
                        if hasattr(self, 'execution_parameters') and execution_id in self.execution_parameters:
                            params = self.execution_parameters[execution_id]
                            if params.get("selected_collection"):
                                collection_id = params["selected_collection"]
                                collection_names = {
                                    "premium": "Premium Diversity",
                                    "reliable": "Reliable Exploration", 
                                    "experimental": "Experimental Innovation",
                                    "free": "Free Cognitive Diversity"
                                }
                                collection_name = collection_names.get(collection_id, collection_id.title())
                        
                        # Ingest performance data
                        success = tracker.ingest_test_run(run_directory, collection_name)
                        if success:
                            self.logger.info(f"Performance data automatically captured for {collection_name}")
                        else:
                            self.logger.warning(f"Failed to capture performance data for {execution_id}")
                            
                    except Exception as e:
                        self.logger.error(f"Error auto-ingesting performance data: {e}")
                
                # HTML report generation removed - using markdown display only
                
                # Enhanced completion message with file location details
                completion_message = "Execution completed successfully! Results saved to timestamped directory:"
                if run_directory:
                    completion_message += f"\n📁 Directory: {run_directory}"
                    completion_message += f"\n📄 Main Results: {os.path.basename(str(output_file))}"
                    completion_message += f"\n📊 Additional Files: run_summary.md, analysis.md, CSV exports, visualizations"
                    completion_message += f"\n🗄️ Performance data automatically captured in database"
                    
                    # Markdown display available via View Results button
                
                # Exit code 0 means the process ran to completion, not that the analysis
                # succeeded. Individual model calls fail independently and are persisted
                # as failures; reporting that as an unqualified success is how a run in
                # which nothing worked came to be presented as a finished analysis.
                st = self.execution_status[execution_id]
                failed = st.get("failed_combinations", 0)
                succeeded = st.get("succeeded_combinations", 0)
                total = st.get("total_combinations", 0)

                if not total and not failed and not succeeded:
                    # The engine never announced a run, so it died before the first
                    # call — a bad argument, a missing config, an import error. Exit
                    # code 1 covers both that and "some calls failed", so the code
                    # alone cannot tell them apart; the absence of any run is what
                    # distinguishes them. Without this the interface reported a
                    # crash as a finished analysis, at 100%.
                    run_status = "failed"
                    detail = (stderr or "").strip().splitlines()
                    reason = detail[-1] if detail else "no error output was captured"
                    completion_message = (
                        "❌ The analysis engine stopped before it ran a single model "
                        f"call (exit code {process.returncode}). Nothing was produced.\n"
                        f"Reason: {reason}"
                    )
                elif failed and succeeded == 0:
                    run_status = "failed"
                    completion_message = (
                        f"❌ Every one of the {failed} model call(s) failed. "
                        "No analysis was produced. See failed_responses/ in the run "
                        "directory for the per-call errors."
                    )
                elif failed:
                    run_status = "completed_with_failures"
                    completion_message = (
                        f"⚠️ Completed with {failed} of {total or failed + succeeded} "
                        f"model call(s) failed — the analysis rests on {succeeded} "
                        f"response(s). See failed_responses/ for the errors.\n\n"
                        + completion_message
                    )
                else:
                    run_status = "completed"

                self.execution_status[execution_id].update({
                    "status": run_status,
                    "progress": 100,
                    "message": completion_message,
                    "failed_combinations": failed,
                    "succeeded_combinations": succeeded,
                    "results_file": str(output_file),
                    # HTML report generation removed - using markdown display only
                    "run_directory": run_directory,
                    "end_time": datetime.now().isoformat(),
                    "stdout": stdout,
                    "stderr": stderr
                })
            else:
                # Use enhanced error analysis
                error_message = self._analyze_execution_error(stderr, process.returncode, execution_id)
                self.logger.error(f"Execution {execution_id} failed with return code {process.returncode}")
                self.execution_status[execution_id].update({
                    "status": "error",
                    "progress": 0,
                    "message": error_message,
                    "end_time": datetime.now().isoformat(),
                    "error": stderr,
                    "return_code": process.returncode
                })
        
        except Exception as e:
            self.logger.exception(f"Unexpected error during execution {execution_id}: {e}")
            self.execution_status[execution_id].update({
                "status": "error",
                "progress": 0,
                "message": f"Unexpected execution error: {str(e)}",
                "end_time": datetime.now().isoformat(),
                "error": str(e),
                "exception": str(e)
            })
        
        return self.execution_status[execution_id]
    
    def _validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """Validate web UI parameters before execution"""
        errors = []
        
        # Validate required parameters
        if not parameters.get("query") or not parameters.get("query").strip():
            errors.append("Query is required and cannot be empty")
            
        # Validate model selections - accept strategic models, individual models, or collections
        selected_models = parameters.get("selected_models", [])
        selected_collection = parameters.get("selected_collection")
        use_strategic_models = parameters.get("use_strategic_models", False)
        
        if not selected_models and not selected_collection and not use_strategic_models:
            errors.append("At least one model, collection, or strategic models must be selected")
        elif selected_collection and selected_collection not in self.llm_collections:
            errors.append(f"Invalid collection '{selected_collection}' - must be one of: {list(self.llm_collections.keys())}")
        elif selected_models and len(selected_models) > 20:
            errors.append("Maximum 20 models can be selected at once")
            
        # Validate variations
        variations = parameters.get("variations")
        if variations is not None:
            try:
                variations_int = int(variations)
                if variations_int < 0 or variations_int > 5:
                    errors.append("Variations must be between 0 and 5")
            except (ValueError, TypeError):
                errors.append("Variations must be a valid number")
                
        # Validate max combinations
        max_combinations = parameters.get("max_combinations")
        if max_combinations is not None:
            try:
                max_combinations_int = int(max_combinations)
                if max_combinations_int < 1 or max_combinations_int > 1000:
                    errors.append("Max combinations must be between 1 and 1000")
            except (ValueError, TypeError):
                errors.append("Max combinations must be a valid number")
                
        # Sampling method validation removed - now uses optimal default configuration
            
        # Validate output format
        output_format = parameters.get("output_format")
        valid_output_formats = ["markdown", "json"]
        if output_format and output_format not in valid_output_formats:
            errors.append(f"Output format must be one of: {', '.join(valid_output_formats)}")
            
        # Validate report format
        report_format = parameters.get("report_format")
        valid_report_formats = ["markdown", "json"]
        if report_format and report_format not in valid_report_formats:
            errors.append(f"Report format must be one of: {', '.join(valid_report_formats)}")
            
        # Validate cognitive frameworks
        frameworks = parameters.get("cognitive_frameworks", [])
        if frameworks and len(frameworks) > 11:
            errors.append("Maximum 11 cognitive frameworks can be selected")
            
        return errors

    def _convert_web_params_to_isee(self, web_params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert web UI parameters to format expected by ISEE backend"""
        converted = {}
        
        # Core parameter mapping
        param_mapping = {
            "query": "query",
            "variations": "variations", 
            "max_combinations": "max_combinations",
            # "sampling_method": removed - simplified to optimal default
            "output_format": "output_format",
            "generate_reports": "generate_reports",
            "report_format": "report_format", 
            "export_csv": "export_csv",
            "analyze_results": "analyze_results",
            "no_visualizations": "no_visualizations",
            "enhancement_info": "enhancement_info",
            "provider": "provider"
        }
        
        for web_key, isee_key in param_mapping.items():
            if web_key in web_params and web_params[web_key] is not None:
                converted[isee_key] = web_params[web_key]
        
        # Handle domain selection - support dynamic domains and traditional mapping
        domain_ids = []
        if web_params.get("selected_domains"):
            # Process selected domains from Web UI
            for domain_identifier in web_params["selected_domains"]:
                # Resolve first, pass through only when nothing resolves.
                #
                # This used to read:
                #
                #     if identifier.startswith('dynamic_domain_') or not
                #        identifier.startswith('domain_'):
                #         use it as-is
                #     else:
                #         <the whole ID / exact-name / fuzzy resolution ladder>
                #
                # "or not startswith('domain_')" means anything that is not already
                # an id is used unchanged, so the ladder below the else was only ever
                # reachable for identifiers that were already ids. Name resolution
                # could not run. A domain picked by its display name -- which is what
                # the interface sends -- reached main.py as "Education", and
                # domain_manager.get_domain raised KeyError: No domain with ID
                # 'Education' exists, surfaced as a 500 by /api/preview-queries.
                # Reproduced 03.09.2026.
                if domain_identifier in self.domain_manager.domains:
                    domain_ids.append(domain_identifier)
                    self.logger.debug(f"Direct ID mapping for '{domain_identifier}'")
                    continue

                exact = [d for d in self.domain_manager.list_domains()
                         if d.name.lower() == domain_identifier.lower()]
                if exact:
                    domain_ids.append(exact[0].id)
                    self.logger.debug(
                        f"Resolved display name '{domain_identifier}' to {exact[0].id}")
                    continue

                # Anything else is a domain this run generated for its own query.
                # It is passed through untouched and travels on --dynamic-domain,
                # which takes any name as context (see _domain_flags).
                #
                # Deliberately NOT fuzzy-matched onto a static domain: a generated
                # domain that gets silently redirected to a similarly named stored
                # one changes what the run actually asks, and nothing downstream
                # would say so. _find_best_domain_match stays available for a caller
                # that wants it explicitly.
                domain_ids.append(domain_identifier)
                self.logger.debug(f"Generated domain, passed through: '{domain_identifier}'")
            
            if domain_ids:
                # Remove duplicates while preserving order
                unique_domain_ids = list(dict.fromkeys(domain_ids))
                converted["domains"] = unique_domain_ids
                converted["domain"] = unique_domain_ids[0]  # Keep single domain for backward compatibility
        elif web_params.get("domain"):
            # Handle single domain selection
            domain_name = web_params["domain"]
            matching_domains = self.domain_manager.search_domains(domain_name)
            if matching_domains:
                domain_ids = [matching_domains[0].id]
                converted["domain"] = domain_ids[0]
                self.logger.debug(f"Resolved single domain '{domain_name}' to ID: {domain_ids[0]}")
            else:
                self.logger.warning(f"No matching domain found for '{domain_name}', using as-is")
                converted["domain"] = domain_name
        
        # No domain resolved: pass none, and let the engine select domains the way it does
        # for a CLI run without --domain.
        #
        # This used to invent the placeholder "Technology", which is not a domain — the
        # configuration has `domain_technology` / "Technology Innovation". main.py then
        # returned early from run_complete_pipeline without an error, the caller
        # concatenated None onto a string, and the run died with
        # `TypeError: can only concatenate str (not "NoneType") to str` and an empty run
        # directory. Every web run that reached this fallback failed that way.
        if not domain_ids and not web_params.get("domain"):
            self.logger.debug(
                "No domains specified; leaving domain unset so the engine selects them.")
        
        # Handle cognitive frameworks
        if web_params.get("cognitive_frameworks"):
            converted["instructions"] = len(web_params["cognitive_frameworks"])
            # Convert Web UI framework names to backend template IDs
            framework_mapping = {
                "Analytical": "ins_analytical",
                "Creative": "ins_creative", 
                "Critical": "ins_critical",
                "Integrative": "ins_integrative",
                "Pragmatic": "ins_pragmatic",
                "First Principles": "ins_first_principles",
                "Systems": "ins_systems",
                "Contrarian": "ins_contrarian",
                "Historical": "ins_historical",
                "Futurist": "ins_futurist",
                "Disruption": "ins_disruption",
                # Legacy support for full names
                "Analytical Framework": "ins_analytical",
                "Creative Framework": "ins_creative", 
                "Critical Framework": "ins_critical",
                "Integrative Framework": "ins_integrative",
                "Pragmatic Framework": "ins_pragmatic",
                "First Principles Framework": "ins_first_principles",
                "Systems Thinking Framework": "ins_systems",
                "Contrarian Framework": "ins_contrarian",
                "Historical Framework": "ins_historical",
                "Future-Oriented Framework": "ins_futurist",
                "Disruption Framework": "ins_disruption"
            }
            
            # Map Web UI framework names to backend IDs
            mapped_frameworks = []
            for framework in web_params["cognitive_frameworks"]:
                if framework in framework_mapping:
                    mapped_frameworks.append(framework_mapping[framework])
                else:
                    self.logger.warning(f"Unknown framework: {framework}")
                    # Keep original name as fallback
                    mapped_frameworks.append(framework)
            
            # Convert list to comma-separated string as expected by guardrails
            converted["instruction_templates"] = ",".join(mapped_frameworks)
        else:
            # Default to 3 instructions if not specified
            converted["instructions"] = 3
            converted["instruction_templates"] = None
        
        # Handle models - support strategic models, collections, or individual selection
        if web_params.get("use_strategic_models"):
            # Smart Auto-Pilot: Use strategic models
            strategic_models = self.get_individual_models(strategic_only=True)
            strategic_model_ids = [model['model_param'] for model in strategic_models]
            converted["models"] = len(strategic_model_ids)
            converted["selected_models"] = strategic_model_ids
            converted["strategic_models"] = True
            self.logger.info(f"Using strategic models: {len(strategic_model_ids)} models")
        elif web_params.get("selected_collection"):
            # Collection-based model selection
            collection_id = web_params["selected_collection"]
            collection_models = self.resolve_collection_models(collection_id)
            if collection_models:
                converted["models"] = len(collection_models)
                converted["selected_models"] = collection_models
                converted["collection_id"] = collection_id
                self.logger.info(f"Using collection '{collection_id}' with {len(collection_models)} models")
            else:
                # Fallback to default if collection resolution fails
                self.logger.warning(f"Collection '{collection_id}' resolution failed, using default")
                converted["models"] = 3
        elif web_params.get("selected_models"):
            # Individual model selection (legacy support)
            converted["models"] = len(web_params["selected_models"])
            converted["selected_models"] = web_params["selected_models"]
            self.logger.info(f"Using individual model selection: {len(web_params['selected_models'])} models")
        else:
            # Default to 3 models if not specified
            converted["models"] = 3
            self.logger.debug("No models or collection specified, defaulting to 3 models")
        
        # Add defaults for other required parameters
        if "variations" not in converted:
            # Default to 0 variations to preserve only the original user query
            # Users can explicitly set higher values if they want query exploration
            converted["variations"] = 0
        if "max_combinations" not in converted:
            converted["max_combinations"] = 30
        
        # Add defaults for cost estimator parameters
        converted.setdefault("simulate", False)
        converted.setdefault("dry_run", False)
        converted.setdefault("use_ollama", False)
        converted.setdefault("balanced_models", False)
        
        return converted

    # ------------------------------------------------------------------
    # Progress events
    # ------------------------------------------------------------------
    # A run reports itself as a stream of PROGRESS_JSON events. Folding one event
    # into the run's status is kept apart from reading the pipe on purpose: it is
    # the half worth testing, and it is the half that stays if the engine is ever
    # imported directly instead of spawned. Only the producer would change then,
    # not this.

    #: How many calls the status carries for display. Bookkeeping keeps all of
    #: them regardless — see `new_progress_context`.
    DISPLAY_CALLS = 20

    #: What the engine prefixes a progress event with on stdout.
    PROGRESS_MARKER = "PROGRESS_JSON:"

    def extract_progress_events(self, line: str) -> List[Dict[str, Any]]:
        """Pull every progress event out of one line of engine output.

        The engine prints these from a thread pool, and concurrent `print()` calls
        interleave: a marker regularly lands mid-line, glued behind another
        thread's output — "…using provider: openrouterPROGRESS_JSON:{…}". The
        reader used to require the line to *begin* with the marker, so anything
        that landed behind other text was dropped silently. Measured on
        03.09.2026 during a live run: 6 of 18 events, a third of the run's
        progress, lost that way.

        Parsed with `raw_decode`, which stops at the end of the JSON value, so a
        line carrying two events — or an event followed by more output — yields
        all of them. The interleaving itself cannot be fixed on this side; it is
        a property of shipping structured events down a shared text stream.
        """
        events: List[Dict[str, Any]] = []
        decoder = json.JSONDecoder()
        index = line.find(self.PROGRESS_MARKER)

        while index != -1:
            start = index + len(self.PROGRESS_MARKER)
            try:
                event, end = decoder.raw_decode(line, start)
            except ValueError as e:
                # A marker whose JSON is cut off — the line ended mid-event.
                self.logger.warning(f"Unparsable progress event at offset {start}: {e}")
                break
            if isinstance(event, dict):
                events.append(event)
            index = line.find(self.PROGRESS_MARKER, max(end, start + 1))

        return events

    @staticmethod
    def new_progress_context() -> Dict[str, Any]:
        """Per-run bookkeeping for the progress stream.

        `calls` is the complete register of every combination the run announced,
        keyed by combination_id, and is deliberately never truncated. A completion
        event names a call that may have started dozens of events earlier, and it
        can only be matched while that call is still on record. The previous code
        kept just the last eight, so under parallel execution most completions
        found nothing to update and were dropped without a trace.
        """
        return {"total": 0, "completed": 0, "calls": {}, "unmatched": 0}

    @staticmethod
    def _format_minutes(minutes: float) -> str:
        """Render a duration the way the progress line reads it."""
        if minutes < 1:
            return f"{int(minutes * 60)}s"
        if minutes < 60:
            return f"{int(minutes)}m"
        return f"{int(minutes // 60)}h {int(minutes % 60)}m"

    def _publish_calls(self, status: Dict[str, Any], ctx: Dict[str, Any]) -> None:
        """Copy the register into the status the browser polls.

        `active_parallel_calls` is derived from the register every time rather
        than accumulated, so a call that is still running cannot silently drop out
        of the list it belongs to.
        """
        calls = list(ctx["calls"].values())
        status["active_parallel_calls"] = [c for c in calls if c["status"] == "processing"]
        status["current_calls"] = calls[-self.DISPLAY_CALLS:]

    def _apply_progress_event(self, execution_id: str, event: Dict[str, Any],
                              ctx: Dict[str, Any]) -> None:
        """Fold one PROGRESS_JSON event into the run's status."""
        status = self.execution_status.get(execution_id)
        if status is None:
            return

        etype = event.get("type")
        if not etype:
            self.logger.warning(f"Progress event without a type, ignored: {event!r}")
            return

        # `main.py` announces the run as `execution_start` on the sequential path
        # and as `parallel_execution_start` on the parallel one. The web UI always
        # takes the parallel path, so listening for only the first left the total
        # at zero for every single web run — and a zero total then divided.
        if etype in ("execution_start", "parallel_execution_start"):
            ctx["total"] = event.get("total_combinations") or 0
            ctx["completed"] = 0
            ctx["calls"].clear()
            ctx["unmatched"] = 0
            status.update({
                "progress": 10,
                "message": f"Starting execution of {ctx['total']} LLM calls...",
                "total_combinations": ctx["total"],
                "completed_combinations": 0,
                "failed_combinations": 0,
                "succeeded_combinations": 0,
                "current_calls": [],
                "active_parallel_calls": [],
            })
            return

        if etype in ("combination_start", "combination_start_parallel"):
            self._on_combination_start(status, event, ctx)
            return

        if etype in ("combination_complete", "combination_complete_parallel",
                     "combination_failed_parallel"):
            self._on_combination_end(status, event, ctx)
            return

        if etype == "parallel_execution_complete":
            # The run's own tally, and the authoritative one. Without it the only
            # completion signal is the exit code, which is 0 for a run in which
            # every call failed — the UI then reported "completed successfully"
            # over an entirely fabricated report.
            status.update({
                "failed_combinations": event.get("failed", 0),
                "succeeded_combinations": event.get("completed", 0),
            })
            return

        self.logger.debug(f"Unhandled progress event type {etype!r}")

    def _on_combination_start(self, status: Dict[str, Any], event: Dict[str, Any],
                              ctx: Dict[str, Any]) -> None:
        combo_id = event.get("combination_id") or f"combo_{len(ctx['calls'])}"
        started = datetime.now()

        ctx["calls"][combo_id] = {
            "combination_id": combo_id,
            "model": event.get("model", "Unknown"),
            # The display name is what a person reads; the id is what the browser
            # matches an indicator on. Sending both spares the front end a ladder
            # of substring guesses against the visible label.
            "model_id": event.get("model_id"),
            "framework": event.get("framework", "Unknown"),
            "framework_id": event.get("framework_id"),
            "domain": event.get("domain", "Unknown"),
            "provider": event.get("provider", "Unknown"),
            "status": "processing",
            "start_time": started.isoformat(),
            "is_parallel": event.get("type") == "combination_start_parallel",
        }

        total = ctx["total"]
        done = ctx["completed"]
        if "combination_index" in event:
            index = event["combination_index"]
            percent = int(index / total * 100) if total else 0
            position = f"({index}/{total or '?'} - {percent}%)"
        else:
            percent = event.get("progress_percent")
            if percent is None:
                percent = int(done / total * 100) if total else 0
            position = f"({done + 1}/{total or '?'} - {percent}%)"

        elapsed = self._elapsed_minutes(status, started)
        if done > 0 and total:
            velocity = done / max(elapsed, 0.1)
            remaining = (total - done) / max(velocity, 0.01)
            eta = "< 1 min" if remaining < 1 else self._format_minutes(remaining)
        else:
            eta = "calculating..."

        status["message"] = (f"Processing {event.get('model', 'model')} with "
                             f"{event.get('framework', 'framework')} {position} • ETA: {eta}")
        status["progress"] = 10 + (int(done / total * 80) if total else 0)
        self._publish_calls(status, ctx)

    def _on_combination_end(self, status: Dict[str, Any], event: Dict[str, Any],
                            ctx: Dict[str, Any]) -> None:
        # `combination_failed_parallel` is emitted once all three attempts are
        # spent. It used to have no handler at all, so an exhausted call stayed
        # "processing" in the UI for the rest of the run and was never counted.
        failed_outright = event.get("type") == "combination_failed_parallel"
        success = False if failed_outright else event.get("success", True)

        combo_id = event.get("combination_id")
        call = ctx["calls"].get(combo_id) if combo_id else None
        if call is None:
            # Sequential runs may omit the id; there is exactly one call in flight
            # then, so it is unambiguous. Guessing "the most recently started"
            # under parallel execution, as the old code did, named the wrong call
            # almost every time.
            in_flight = [c for c in ctx["calls"].values() if c["status"] == "processing"]
            if len(in_flight) == 1:
                call = in_flight[0]
            else:
                ctx["unmatched"] += 1
                self.logger.warning(
                    f"Completion for unknown combination {combo_id!r} "
                    f"({len(in_flight)} calls in flight); counted, not attributed"
                )

        ctx["completed"] += 1
        if call is not None:
            call["status"] = "completed" if success else "error"
            call["end_time"] = datetime.now().isoformat()
            if not success:
                call["error"] = event.get("error", "Unknown error")
            if "response_length" in event:
                call["response_length"] = event["response_length"]
            if "attempts" in event:
                call["attempts"] = event["attempts"]

        if not success:
            status["failed_combinations"] = status.get("failed_combinations", 0) + 1

        total = ctx["total"]
        done = ctx["completed"]
        percent = int(done / total * 100) if total else 0
        elapsed = self._format_minutes(self._elapsed_minutes(status, datetime.now()))

        message = f"Completed {done}/{total or '?'} LLM calls ({percent}%) • Elapsed: {elapsed}"
        if not success:
            message += f" (Call failed: {event.get('error', 'Unknown error')})"

        status.update({
            "progress": 10 + (int(done / total * 80) if total else 0),
            "message": message,
            "completed_combinations": done,
        })
        self._publish_calls(status, ctx)

    @staticmethod
    def _elapsed_minutes(status: Dict[str, Any], now: datetime) -> float:
        """Minutes since the run started, 0.0 if the start time is unusable."""
        try:
            started = datetime.fromisoformat(status["start_time"])
        except (KeyError, TypeError, ValueError):
            return 0.0
        return (now - started).total_seconds() / 60

    def _monitor_subprocess_progress(self, process, execution_id: str):
        """Real-time progress monitoring from CLI JSON output and wait for completion"""
        self.logger.debug(f"Starting JSON progress monitoring for execution {execution_id}")
        
        # Initialize progress tracking
        progress_ctx = self.new_progress_context()
        stdout_lines = []
        stderr_lines = []
        
        # Enhanced error recovery tracking
        last_progress_time = datetime.now()
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        try:
            # Read output line by line in real-time with error recovery
            while True:
                # Check if process has finished
                if process.poll() is not None:
                    break
                
                # Check for stalled progress (no updates for too long)
                current_time = datetime.now()
                time_since_progress = (current_time - last_progress_time).total_seconds()
                
                if time_since_progress > 60:  # No progress for 60 seconds
                    self.logger.warning(f"Execution {execution_id}: No progress updates for {int(time_since_progress)} seconds")
                    if execution_id in self.execution_status:
                        current_msg = self.execution_status[execution_id].get("message", "Processing...")
                        self.execution_status[execution_id].update({
                            "message": f"{current_msg} (Working on complex task...)",
                            "last_activity": current_time.isoformat()
                        })
                    last_progress_time = current_time  # Reset timer
                    
                try:
                    # Use a simpler approach - try to read a line with a short timeout
                    try:
                        line = process.stdout.readline()
                        if line:
                            line = line.strip()
                            stdout_lines.append(line)
                            self.logger.debug(f"CLI output: {line}")
                            
                            # Check for JSON progress messages
                            for progress_data in self.extract_progress_events(line):
                                self._apply_progress_event(
                                    execution_id, progress_data, progress_ctx
                                )
                        else:
                            # No output available, short sleep
                            time.sleep(0.1)
                    except Exception as read_error:
                        self.logger.debug(f"Read timeout or error: {read_error}")
                        consecutive_errors += 1
                        time.sleep(0.1)
                        
                except Exception as e:
                    self.logger.debug(f"Non-critical error reading output: {e}")
                    consecutive_errors += 1
                    time.sleep(0.1)  # Small delay to prevent busy waiting
                
                # Check for too many consecutive errors
                if consecutive_errors > max_consecutive_errors:
                    self.logger.warning(f"Execution {execution_id}: {consecutive_errors} consecutive errors, attempting recovery")
                    if execution_id in self.execution_status:
                        current_msg = self.execution_status[execution_id].get("message", "Processing...")
                        self.execution_status[execution_id].update({
                            "message": f"{current_msg} (Recovering from communication issues...)",
                            "recovery_attempts": self.execution_status[execution_id].get("recovery_attempts", 0) + 1
                        })
                    consecutive_errors = 0  # Reset counter
                    time.sleep(1)  # Longer delay for recovery
                elif consecutive_errors == 0:
                    # Reset progress timer on successful reads
                    last_progress_time = datetime.now()
            
            # Read any remaining output
            remaining_stdout, remaining_stderr = process.communicate()
            if remaining_stdout:
                stdout_lines.extend(remaining_stdout.strip().split('\n'))
            if remaining_stderr:
                stderr_lines.extend(remaining_stderr.strip().split('\n'))
                
            # When process completes, update to synthesis phase
            if execution_id in self.execution_status and self.execution_status[execution_id]["status"] == "running":
                self.execution_status[execution_id].update({
                    "progress": 90,
                    "message": "Generating reports and analysis..."
                })
                    
        except Exception as e:
            self.logger.error(f"Error monitoring progress for {execution_id}: {e}")
            # Fallback to communicate() if monitoring fails
            remaining_stdout, remaining_stderr = process.communicate()
            if remaining_stdout:
                stdout_lines.append(remaining_stdout)
            if remaining_stderr:
                stderr_lines.append(remaining_stderr)
        
        # Return combined output
        return '\n'.join(stdout_lines), '\n'.join(stderr_lines)
    
    def _analyze_execution_error(self, stderr: str, returncode: int, execution_id: str) -> str:
        """Analyze subprocess errors and provide specific guidance"""
        self.logger.error(f"Analyzing execution error for {execution_id}: return code {returncode}")
        self.logger.error(f"STDERR content: {stderr}")
        
        # Analyze common error patterns
        if "No module named" in stderr:
            missing_module = stderr.split("No module named '")[1].split("'")[0] if "No module named '" in stderr else "unknown"
            self.logger.error(f"Missing Python module: {missing_module}")
            return f"Missing Python dependencies ({missing_module}). Run: pip install -r requirements.txt"
            
        elif "API key" in stderr.lower() or "authentication" in stderr.lower():
            self.logger.error("API key or authentication issue detected")
            return "API key issue. Check your OpenRouter or other API key configuration in the session."
            
        elif "FileNotFoundError" in stderr:
            if "config" in stderr.lower():
                self.logger.error("Configuration file not found")
                return "Configuration file missing. Verify the selected config file exists."
            else:
                self.logger.error("General file not found error")
                return "Required file missing. Check file paths and permissions."
                
        elif "Permission denied" in stderr:
            self.logger.error("Permission denied error")
            return "Permission denied. Check file permissions and disk space."
            
        elif "Connection" in stderr and ("refused" in stderr or "timeout" in stderr):
            self.logger.error("Network connection issue")
            return "Network connection issue. Check internet connectivity and API endpoints."
            
        elif returncode == 1 and "Usage:" in stderr:
            self.logger.error("Command line argument error")
            return "Invalid command line arguments. Check parameter formatting."
            
        elif returncode == 130:  # Ctrl+C
            self.logger.warning("Process interrupted by user")
            return "Process was interrupted. This may be normal if you stopped the execution."
            
        else:
            self.logger.error(f"Unhandled error pattern: {stderr[:200]}...")
            return f"Execution failed with code {returncode}: {stderr[:200]}{'...' if len(stderr) > 200 else ''}"
    
    def _process_model_params(self, selected_models):
        """Process model parameters to ensure they work with the ISEE backend"""
        processed_models = []
        
        # Load config to check existing models
        try:
            with open('openrouter_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                config_models = {model.get('id'): model for model in config.get('models', {}).get('api_models', [])}
                # Also create a reverse lookup by model parameter
                param_to_config = {model.get('parameters', {}).get('model', ''): model.get('id') 
                                 for model in config.get('models', {}).get('api_models', [])
                                 if model.get('parameters', {}).get('model')}
        except Exception as e:
            self.logger.warning(f"Could not load config for model processing: {e}")
            config_models = {}
            param_to_config = {}
        
        for model_param in selected_models:
            # Check if this is already a model parameter (e.g., "anthropic/claude-3-5-sonnet")
            if '/' in model_param:
                # This looks like an OpenRouter model parameter
                if model_param in param_to_config:
                    # Use the existing config ID
                    config_id = param_to_config[model_param]
                    processed_models.append(config_id)
                    self.logger.info(f"Found existing config for {model_param} -> {config_id}")
                else:
                    # Generate a dynamic config ID for this model parameter
                    dynamic_id = f"openrouter_{model_param.replace('/', '_').replace('-', '_')}"
                    processed_models.append(model_param)  # Pass the model param directly
                    self.logger.info(f"Using dynamic model parameter: {model_param}")
            else:
                # This might be a legacy ID, check if it exists in config
                if model_param in config_models:
                    processed_models.append(model_param)
                    self.logger.debug(f"Using existing config ID: {model_param}")
                else:
                    # Treat as a model parameter and pass through
                    processed_models.append(model_param)
                    self.logger.warning(f"Unknown model identifier, passing through: {model_param}")
        
        return processed_models
    
    def _detect_apis(self) -> Dict[str, Any]:
        """Detect available API providers and Ollama models (adapted from command wizard)"""
        # Get session API key if available (only within request context)
        session_api_key = None
        try:
            if 'openrouter_api_key' in session:
                session_api_key = session['openrouter_api_key']
        except RuntimeError:
            # Outside request context - no session access
            pass
        
        return self._detect_apis_with_session_key(session_api_key)
    
    def _detect_apis_with_session_key(self, session_api_key: str = None) -> Dict[str, Any]:
        """Detect available API providers and Ollama models with optional session key"""
        api_status = {
            "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "openai": bool(os.environ.get("OPENAI_API_KEY")),
            "google": bool(os.environ.get("GOOGLE_API_KEY")),
            "openrouter": bool(os.environ.get("OPENROUTER_API_KEY")),
            "globant": bool(os.environ.get("GLOBANT_API_KEY")),
            "ollama": False,
            "ollama_models": [],
            "any_api": False
        }
        
        # Check session-stored keys
        if session_api_key:
            api_status["openrouter"] = True
        
        # Check Ollama availability
        try:
            from model_api_integration import ModelAPIFactory
            ollama_client = ModelAPIFactory.create_client("ollama")
            ollama_models = ollama_client.get_available_models()
            if ollama_models:
                api_status["ollama"] = True
                api_status["ollama_models"] = ollama_models
        except Exception:
            # Silently fail if Ollama check fails
            pass
            
        api_status["any_api"] = any([
            api_status["anthropic"],
            api_status["openai"], 
            api_status["google"],
            api_status["openrouter"],
            api_status["globant"],
            api_status["ollama"]
        ])
        
        return api_status
    
    def validate_openrouter_api_key(self, api_key: str) -> bool:
        """Validate an OpenRouter API key by making a test request"""
        try:
            from model_api_integration import OpenRouterClient
            
            # Create a temporary client with the provided key
            temp_client = OpenRouterClient(api_key=api_key)
            
            # Try to get the models list as a validation
            models = temp_client.get_available_models()
            
            # If we get here without exception, the key works
            return len(models) > 0
            
        except Exception as e:
            print(f"API key validation failed: {str(e)}")
            return False
    
    def setup_openrouter_api_key(self, api_key: str, storage_method: str = "session") -> Dict[str, Any]:
        """Set up OpenRouter API key with specified storage method"""
        result = {
            "success": False,
            "message": "",
            "api_status": {}
        }
        
        # Validate API key format
        if not api_key.startswith("sk-or-"):
            result["message"] = "OpenRouter API keys should start with 'sk-or-'"
            return result
        
        # Optional validation
        if not self.validate_openrouter_api_key(api_key):
            result["message"] = "API key validation failed. Please check your key."
            return result
        
        # Store the key based on storage method
        if storage_method == "session":
            session['openrouter_api_key'] = api_key
            result["message"] = "OpenRouter API key set for this session!"
        elif storage_method == "environment":
            os.environ["OPENROUTER_API_KEY"] = api_key
            result["message"] = "OpenRouter API key set for this application session!"
        
        # Update API status
        updated_api_status = self._detect_apis()
        result["success"] = True
        result["api_status"] = updated_api_status
        
        return result
    
    def _generate_dynamic_domains(self, query: str) -> List[Dict[str, str]]:
        """Generate domain areas dynamically based on query using lightweight LLM"""
        try:
            # Import OpenRouter client
            import requests
            
            # Use a fast, cost-effective model for domain analysis
            api_key = session.get('openrouter_api_key') or os.environ.get('OPENROUTER_API_KEY')
            if not api_key:
                self.logger.warning("No OpenRouter API key available for domain suggestion")
                return self._get_fallback_domains()
            
            # Construct domain analysis prompt
            prompt = f"""Analyze this query and suggest 2-3 relevant domain areas that would provide the most valuable perspectives:

Query: "{query}"

Respond with ONLY a JSON array of 2-3 domain objects, each with:
- "name": A concise domain name (2-4 words)
- "description": Brief explanation of why this domain is relevant (1 sentence)

Example format:
[
  {{"name": "Behavioral Psychology", "description": "Understanding human decision-making patterns and cognitive biases relevant to the query."}},
  {{"name": "Technology Innovation", "description": "Exploring technological solutions and digital transformation opportunities."}}
]

Return only the JSON array, no other text."""

            # Make API call to lightweight model
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "anthropic/claude-3-haiku",  # Fast, cost-effective
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 300,
                    "temperature": 0.1
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # Parse JSON response
                import json
                domains = json.loads(content)
                
                # Validate and format domains
                formatted_domains = []
                for i, domain in enumerate(domains[:3]):  # Max 3 domains
                    if isinstance(domain, dict) and "name" in domain and "description" in domain:
                        formatted_domains.append({
                            "id": f"dynamic_domain_{i+1}",
                            "name": domain["name"],
                            "description": domain["description"]
                        })
                
                if formatted_domains:
                    self.logger.info(f"Generated {len(formatted_domains)} dynamic domains for query: {query[:50]}...")
                    return formatted_domains
                    
            self.logger.warning("Failed to parse domain suggestions, using fallback")
            return self._get_fallback_domains()
            
        except Exception as e:
            self.logger.error(f"Dynamic domain generation failed: {str(e)}")
            return self._get_fallback_domains()
    
    def _get_fallback_domains(self) -> List[Dict[str, str]]:
        """Provide fallback domains when dynamic generation fails"""
        return [
            {
                "id": "fallback_domain_1",
                "name": "Cross-Disciplinary Analysis", 
                "description": "Integrating insights from multiple fields to provide comprehensive understanding."
            },
            {
                "id": "fallback_domain_2",
                "name": "Practical Implementation",
                "description": "Focusing on actionable solutions and real-world application strategies."
            },
            {
                "id": "fallback_domain_3", 
                "name": "Strategic Planning",
                "description": "Examining long-term implications and systematic approaches to the challenge."
            }
        ]
    
    def _find_best_domain_match(self, domain_name: str) -> Optional[str]:
        """Find the best matching domain ID for a dynamic domain name"""
        # Define mapping of common dynamic domain terms to existing domains
        domain_mappings = {
            # Technical documentation related
            "technical communication": "domain_technical_writing",
            "technical documentation": "domain_technical_writing", 
            "documentation": "domain_technical_writing",
            "content management": "domain_content_strategy",
            "content strategy": "domain_content_strategy",
            
            # UX/Design related
            "user experience": "domain_technology",
            "ux design": "domain_technology",
            "user experience design": "domain_technology",
            "interface design": "domain_technology",
            
            # Technology related
            "technology": "domain_technology",
            "innovation": "domain_technology",
            "digital": "domain_technology",
            "ai": "domain_ai_writing",
            "artificial intelligence": "domain_ai_writing",
            
            # Education related
            "education": "domain_education",
            "learning": "domain_education", 
            "teaching": "domain_education",
            "instructional": "domain_instructional_design",
            
            # Development related
            "development": "domain_developer_docs",
            "programming": "domain_developer_docs",
            "software": "domain_developer_docs",
            
            # Management related
            "knowledge management": "domain_knowledge_management",
            "information": "domain_knowledge_management",
            
            # General fallbacks
            "communication": "domain_technical_writing",
            "systems": "domain_technology",
            "management": "domain_knowledge_management"
        }
        
        domain_lower = domain_name.lower().strip()
        
        # Direct mapping first
        if domain_lower in domain_mappings:
            return domain_mappings[domain_lower]
        
        # Partial matching - check if any mapping key is contained in the domain name
        for key, domain_id in domain_mappings.items():
            if key in domain_lower or domain_lower in key:
                return domain_id
        
        # No match found
        return None

# Initialize demo controller
demo = ISEEWebDemo()

@app.route('/')
def index():
    """Main demo page"""
    # Generate session ID for user behavior analytics if not exists
    if 'session_id' not in session:
        import uuid
        session['session_id'] = str(uuid.uuid4())[:8]  # Short session ID
        
        # Track new session start
        demo.logger.info(f"USER_ANALYTICS: event_type=session_started user_session={session['session_id']} "
                        f"timestamp={datetime.now().isoformat()}")
    
    return render_template('demo.html')

@app.route('/isee-ui')
def isee_ui():
    """Serve the hybrid UI interface with dynamic model loading"""
    return send_file('isee-ui.html')

@app.route('/favicon.ico')
def favicon():
    """Browsers request /favicon.ico by default regardless of any <link rel="icon">
    tag, and isee-ui.html (the primary interface) has none. Without this route that
    request 404s and is the only console error the web interface produces. Reuse the
    existing academic-gradient mark instead of shipping a second icon asset."""
    return send_file(
        os.path.join(app.static_folder, 'favicon.svg'),
        mimetype='image/svg+xml'
    )

@app.route('/api/frameworks')
def api_frameworks():
    """Get cognitive frameworks data"""
    complexity = request.args.get('complexity', 'all')
    frameworks = demo.get_cognitive_frameworks(complexity)
    return jsonify(frameworks)

@app.route('/api/models')
def api_models():
    """Get individual model data with optional strategic filtering"""
    strategic_only = request.args.get('strategic_only', 'false').lower() == 'true'
    models = demo.get_individual_models(strategic_only=strategic_only)
    return jsonify(models)

@app.route('/api/domains')
def api_domains():
    """Get knowledge domains data"""
    domains = demo.get_knowledge_domains()
    return jsonify(domains)

@app.route('/api/collections')
def api_collections():
    """Get LLM collections data"""
    # User Behavior Analytics - Track collections viewing
    user_session = session.get('session_id', 'anonymous')
    demo.logger.info(f"USER_ANALYTICS: event_type=collections_viewed user_session={user_session} "
                    f"timestamp={datetime.now().isoformat()}")
    
    collections = demo.get_llm_collections()
    return jsonify(collections)

@app.route('/api/estimate', methods=['POST'])
def api_estimate():
    """Get cost and resource estimates"""
    parameters = request.json
    
    # User Behavior Analytics - Track cost estimation usage
    user_session = session.get('session_id', 'anonymous')
    collection_name = parameters.get('collection_name', 'individual_models')
    estimated_models = len(parameters.get('selected_models', []))
    
    demo.logger.info(f"USER_ANALYTICS: event_type=cost_estimated user_session={user_session} "
                    f"collection_name={collection_name} estimated_models={estimated_models} "
                    f"timestamp={datetime.now().isoformat()}")
    
    estimate = demo.estimate_execution_cost(parameters)
    
    # Track the estimated cost value
    estimated_cost = estimate.get('estimated_cost', 0)
    demo.logger.info(f"USER_ANALYTICS: event_type=cost_calculated user_session={user_session} "
                    f"estimated_cost_usd={estimated_cost} collection_name={collection_name} "
                    f"timestamp={datetime.now().isoformat()}")
    
    return jsonify(estimate)

@app.route('/api/preview', methods=['POST'])
def api_preview():
    """Generate command preview"""
    parameters = request.json
    
    # User Behavior Analytics - Track command preview usage
    user_session = session.get('session_id', 'anonymous')
    collection_name = parameters.get('collection_name', 'individual_models')
    demo.logger.info(f"USER_ANALYTICS: event_type=command_previewed user_session={user_session} "
                    f"collection_name={collection_name} timestamp={datetime.now().isoformat()}")
    
    command = demo.generate_command_preview(parameters)
    return jsonify({"command": command})

@app.route('/api/preview-queries', methods=['POST'])
def api_preview_queries():
    """Preview the assembled queries that would be sent to LLMs"""
    try:
        parameters = request.json
        
        if not parameters:
            return jsonify({"error": "No parameters provided"}), 400
        
        # Validate required parameters
        if not parameters.get('query'):
            return jsonify({"error": "Query text is required"}), 400
        
        # Convert web parameters to ISEE format
        converted_params = demo._convert_web_params_to_isee(parameters)
        
        # Create ISEE instance for preview
        from main import ISEEApplication, Query
        isee = ISEEApplication()
        
        # Load configuration
        config_file = converted_params.get('config', 'openrouter_config.json')
        if not os.path.exists(config_file):
            return jsonify({"error": f"Configuration file {config_file} not found"}), 400
        
        isee.load_config(config_file)
        
        # Generate combinations for preview
        query_text = converted_params['query']
        
        # Use domain IDs that were already resolved in parameter conversion
        domain_ids = []
        if converted_params.get('domains'):
            # Use already-resolved domain IDs from parameter conversion
            domain_ids = converted_params['domains']
        elif converted_params.get('domain'):
            # Use single resolved domain ID
            domain_ids = [converted_params['domain']]
        
        # Final fallback if no domains found
        if not domain_ids:
            domain_ids = ['general problem-solving']
        model_count = converted_params.get('models', 3)
        instruction_count = converted_params.get('instructions', 3)
        query_variations = converted_params.get('variations', 0)
        max_combinations = converted_params.get('max_combinations', 100)  # No limit for preview - enables full analysis
        selected_models = converted_params.get('selected_models', [])
        # Create query and generate combinations
        from uuid import uuid4
        query_id = f"query_{str(uuid4())[:8]}"
        query = Query(id=query_id, text=query_text)
        isee.query_generator.add_base_query(query)
        
        # Set specific framework templates if provided by Web UI
        if converted_params.get('instruction_templates'):
            framework_ids = converted_params['instruction_templates'].split(',')
            isee.specific_template_ids = [fid.strip() for fid in framework_ids if fid.strip()]
        
        # Generate combinations
        combinations = isee.generate_combinations(
            query_id=query_id,
            domain_ids=domain_ids,
            model_count=model_count,
            instruction_count=instruction_count,
            query_variations=query_variations,
            max_combinations=max_combinations,
            selected_models=selected_models
        )
        
        if not combinations:
            return jsonify({"error": "No valid combinations generated"}), 400
        
        # Build preview data
        preview_data = []
        for combo in combinations:
            try:
                # Get components
                template = isee.template_library.get_template(combo["template"])
                query_obj = isee.query_generator.get_query_by_id(combo["query"])
                domain = isee.domain_manager.get_domain(combo["domain"])
                
                # Format the instruction template
                formatted_instruction = template.format({
                    "domain": domain.description,
                    **query_obj.variables
                })
                
                # Create complete prompt
                complete_prompt = f"{formatted_instruction}\n\n{query_obj.text}"
                
                preview_data.append({
                    "combination_id": combo["id"],
                    "model": combo["model"],
                    "template_name": template.name,
                    "template_id": template.id,
                    "cognitive_style": template.metadata.get('cognitive_style', 'default'),
                    "domain_name": domain.name,
                    "query_text": query_obj.text,
                    "formatted_instruction": formatted_instruction,
                    "complete_prompt": complete_prompt,
                    "character_count": len(complete_prompt),
                    "word_count": len(complete_prompt.split())
                })
                
            except Exception as e:
                # Skip invalid combinations
                continue
        
        return jsonify({
            "success": True,
            "total_combinations": len(combinations),
            "preview_count": len(preview_data),
            "queries": preview_data
        })
        
    except Exception as e:
        return jsonify({"error": f"Preview generation failed: {str(e)}"}), 500

# How many analyses may be started, and how close together. Every start spends the
# owner's money -- roughly $0.31 for a full run -- and nothing stopped a caller from
# sending a hundred POSTs in a second. The interface has no authentication by
# design, so the money is protected here or nowhere.
#
# The defaults are set so that ordinary use never meets them: three runs at once,
# ten starts an hour, about $3 an hour at the worst. Raise them with
# ISEE_MAX_CONCURRENT_RUNS and ISEE_MAX_RUNS_PER_HOUR when a real workload needs
# more; the point is a ceiling, not this particular ceiling.
MAX_CONCURRENT_RUNS = int(os.environ.get("ISEE_MAX_CONCURRENT_RUNS", "3"))
MAX_RUNS_PER_HOUR = int(os.environ.get("ISEE_MAX_RUNS_PER_HOUR", "10"))

_run_starts: List[float] = []
_run_starts_lock = threading.Lock()


def _claim_a_run_slot() -> Optional[str]:
    """Reserve permission to start one analysis, or say why it is refused.

    Returns None when the run may proceed, otherwise a sentence for the caller.
    Both limits are checked under one lock, so two simultaneous requests cannot
    both see the last free slot.
    """
    now = time.time()
    with _run_starts_lock:
        del _run_starts[:max(0, len(_run_starts) - 1000)]  # bound the list
        recent = [t for t in _run_starts if now - t < 3600]
        _run_starts[:] = recent

        running = sum(
            1 for status in demo.execution_status.values()
            if status.get("status") == "running")
        if running >= MAX_CONCURRENT_RUNS:
            return (f"{running} analyses are already running, which is the limit. "
                    f"Wait for one to finish, or raise ISEE_MAX_CONCURRENT_RUNS.")

        if len(recent) >= MAX_RUNS_PER_HOUR:
            oldest = min(recent)
            minutes = int((3600 - (now - oldest)) / 60) + 1
            return (f"{len(recent)} analyses have been started in the last hour, "
                    f"which is the limit. The next slot frees in about {minutes} "
                    f"minutes, or raise ISEE_MAX_RUNS_PER_HOUR.")

        _run_starts.append(now)
        return None


@app.route('/api/execute', methods=['POST'])
def api_execute():
    """Execute ISEE command"""
    parameters = request.get_json(silent=True)
    if not isinstance(parameters, dict):
        # request.json raises on a malformed body but returns None for a literal
        # `null`, and every line below assumes a dict.
        return jsonify({"error": "Request body must be a JSON object"}), 400

    refusal = _claim_a_run_slot()
    if refusal:
        demo.logger.warning(f"Refused an analysis: {refusal}")
        return jsonify({"error": refusal}), 429

    # A timestamp alone collides whenever two runs start in the same second -- the
    # second one would overwrite the first's status entry, and each would report the
    # other's progress. The random half also stops a caller guessing the id of a run
    # they did not start, since knowing one is enough to read its results.
    execution_id = f"exec_{int(time.time())}_{secrets.token_hex(4)}"
    
    # User Behavior Analytics - Track execution start
    user_session = session.get('session_id', 'anonymous')
    collection_name = parameters.get('collection_name', 'individual_models')
    query_length = len(parameters.get('query', ''))
    frameworks_count = len(parameters.get('selected_frameworks', []))
    domains_count = len(parameters.get('selected_domains', []))
    
    demo.logger.info(f"USER_ANALYTICS: event_type=execution_started user_session={user_session} "
                    f"execution_id={execution_id} collection_name={collection_name} "
                    f"query_length={query_length} frameworks_count={frameworks_count} "
                    f"domains_count={domains_count} timestamp={datetime.now().isoformat()}")
    
    # Get session API key if available
    session_api_key = session.get('openrouter_api_key', None)
    
    # Start execution in background thread
    thread = threading.Thread(
        target=demo.execute_isee_command,
        args=(parameters, execution_id, session_api_key)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({"execution_id": execution_id})

@app.route('/api/analyze-test', methods=['POST'])
def api_analyze_test():
    """Execute ISEE test analysis with reduced parameters for testing report generation"""
    parameters = request.get_json(silent=True)
    if not isinstance(parameters, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    # This route runs a smaller analysis, but it is the same subprocess against the
    # same paid API. It counts against the same ceiling.
    refusal = _claim_a_run_slot()
    if refusal:
        demo.logger.warning(f"Refused a test analysis: {refusal}")
        return jsonify({"error": refusal}), 429

    execution_id = f"test_{int(time.time())}_{secrets.token_hex(4)}"
    
    # Log test execution
    user_session = session.get('session_id', 'anonymous')
    demo.logger.info(f"USER_ANALYTICS: event_type=test_execution_started user_session={user_session} "
                    f"execution_id={execution_id} max_combinations={parameters.get('max_combinations', 10)} "
                    f"timestamp={datetime.now().isoformat()}")
    
    # Get session API key if available
    session_api_key = session.get('openrouter_api_key', None)
    
    # Start execution in background thread
    thread = threading.Thread(
        target=demo.execute_isee_command,
        args=(parameters, execution_id, session_api_key)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({"execution_id": execution_id})

@app.route('/api/status/<execution_id>')
def api_status(execution_id):
    """Get execution status"""
    status = demo.execution_status.get(execution_id, {"status": "not_found"})
    return jsonify(status)

@app.route('/api/download/<execution_id>')
def api_download(execution_id):
    """Download results file with proper content type and filename"""
    status = demo.execution_status.get(execution_id, {})
    results_file = status.get("results_file")
    
    # User Behavior Analytics - Track result download
    user_session = session.get('session_id', 'anonymous')
    execution_duration = None
    if status.get("start_time") and status.get("status") in ("completed", "completed_with_failures"):
        start_time = datetime.fromisoformat(status["start_time"].replace('Z', '+00:00'))
        execution_duration = (datetime.now() - start_time).total_seconds()
    
    demo.logger.info(f"USER_ANALYTICS: event_type=result_downloaded user_session={user_session} "
                    f"execution_id={execution_id} file_available={bool(results_file and Path(results_file).exists())} "
                    f"execution_duration_seconds={execution_duration} timestamp={datetime.now().isoformat()}")
    
    if results_file and Path(results_file).exists():
        file_path = Path(results_file)
        
        # Determine content type and download filename based on file extension
        if file_path.suffix == '.md':
            mimetype = 'text/markdown'
            download_name = f"isee_results_{execution_id}.md"
        elif file_path.suffix == '.json':
            mimetype = 'application/json'
            download_name = f"isee_results_{execution_id}.json"
        else:
            # Fallback for other formats
            mimetype = 'application/octet-stream'
            download_name = f"isee_results_{execution_id}{file_path.suffix}"
        
        return send_file(
            results_file, 
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype
        )
    else:
        return jsonify({"error": "Results file not found"}), 404

@app.route('/api/download-zip/<execution_id>')
def api_download_zip(execution_id):
    """Download entire run directory as ZIP archive"""
    import zipfile
    import tempfile
    import os
    
    status = demo.execution_status.get(execution_id, {})
    results_file = status.get("results_file")
    
    # User Behavior Analytics - Track ZIP download
    user_session = session.get('session_id', 'anonymous')
    execution_duration = None
    if status.get("start_time") and status.get("status") in ("completed", "completed_with_failures"):
        start_time = datetime.fromisoformat(status["start_time"].replace('Z', '+00:00'))
        execution_duration = (datetime.now() - start_time).total_seconds()
    
    demo.logger.info(f"USER_ANALYTICS: event_type=zip_downloaded user_session={user_session} "
                    f"execution_id={execution_id} timestamp={datetime.now().isoformat()}")
    
    # Find the run directory
    run_directory = None
    
    if results_file and Path(results_file).exists():
        # If we have the results file, use its parent directory
        run_directory = Path(results_file).parent
    else:
        # No fallback to "the newest run that has files in it".
        #
        # This used to walk data/output and return the most recent non-empty run
        # whenever the id could not be resolved. Confirmed on 05.09.2026: an invented
        # id returned 160,854 bytes of a real run's ZIP with HTTP 200.
        #
        # The security reading is the smaller one. On a single-user machine it means
        # "download my results" can hand back a DIFFERENT run's results, silently,
        # and a researcher comparing two runs cannot tell. The case it was written
        # for is real -- run status lives in a per-process dict and a server restart
        # loses it -- but the answer to an unresolvable id is to say so.
        run_directory = None
    
    if not run_directory or not run_directory.exists():
        return jsonify({"error": "Run directory not found"}), 404
    
    # Create temporary ZIP file
    try:
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from the run directory
            for file_path in run_directory.rglob('*'):
                if file_path.is_file():
                    # Create archive path relative to run directory
                    arcname = file_path.relative_to(run_directory)
                    zipf.write(file_path, arcname)
        
        # Determine download filename
        timestamp = run_directory.name.replace('run_', '')
        download_name = f"isee_results_{timestamp}_{execution_id}.zip"
        
        def remove_temp_file():
            try:
                os.unlink(temp_zip.name)
            except:
                pass
        
        # Schedule cleanup after response
        from flask import after_this_request
        @after_this_request
        def cleanup(response):
            remove_temp_file()
            return response
        
        return send_file(
            temp_zip.name,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/zip'
        )
        
    except Exception as e:
        demo.logger.error(f"Error creating ZIP for execution {execution_id}: {e}")
        # Cleanup temp file if it exists
        try:
            os.unlink(temp_zip.name)
        except:
            pass
        return jsonify({"error": f"Error creating ZIP archive: {str(e)}"}), 500

# HTML report endpoint removed - using markdown display only

@app.route('/api/markdown/<execution_id>')
def api_view_markdown(execution_id):
    """Serve the raw markdown content for client-side rendering"""
    status = demo.execution_status.get(execution_id, {})
    results_file = status.get("results_file")
    
    # If not in execution status, try to find the file directly
    if not results_file:
        # First try the direct execution_id path (for backward compatibility)
        potential_path = Path(f"data/output/{execution_id}/isee_result.md")
        if potential_path.exists():
            results_file = str(potential_path)
        else:
            # Same reasoning as /api/download-zip above: an unresolvable id is
            # answered as unresolvable, never with whichever run happens to be
            # newest. Confirmed returning 19,400 bytes of an unrelated run.
            results_file = None
    
    # User Behavior Analytics - Track markdown viewing
    user_session = session.get('session_id', 'anonymous')
    demo.logger.info(f"USER_ANALYTICS: event_type=markdown_viewed user_session={user_session} "
                    f"execution_id={execution_id} results_available={bool(results_file and Path(results_file).exists())} "
                    f"timestamp={datetime.now().isoformat()}")
    
    if results_file and Path(results_file).exists() and str(results_file).endswith('.md'):
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            return jsonify({
                "success": True,
                "markdown": markdown_content,
                "filename": Path(results_file).name,
                "execution_id": execution_id
            })
        except Exception as e:
            demo.logger.error(f"Error reading markdown file {results_file}: {e}")
            return jsonify({"error": f"Error reading results file: {str(e)}"}), 500
    else:
        return jsonify({"error": "Markdown results file not available"}), 404

@app.route('/api/query-details/<execution_id>')
def api_query_details(execution_id):
    """Serve query details CSV for a specific execution"""
    try:
        # Find the output directory for this execution
        output_dir = Path(f"data/output")
        
        # Look for query details CSV files in the execution directory or output directory
        # Only patterns that actually contain the execution id.
        #
        # Two of the four did not: `data/output/run_*/queries_detailed_*.csv` matches
        # every run, and `data/output/queries_detailed_*.csv` matches every file. With
        # `max(..., key=mtime)` on top, an unknown id returned the newest query CSV of
        # whatever run happened to be latest. Confirmed on 05.09.2026: an invented id
        # returned 13,156 bytes belonging to a different run, HTTP 200.
        #
        # The two that remain both name the id: callers pass a run id as the
        # execution id, and some layouts put the CSV beside the run directory.
        possible_patterns = [
            f"data/output/{execution_id}/queries_detailed_*.csv",
            f"data/output/queries_detailed_*{execution_id}*.csv",
        ]
        
        csv_file = None
        for pattern in possible_patterns:
            matches = list(Path().glob(pattern))
            if matches:
                # Get the most recent file
                csv_file = max(matches, key=lambda p: p.stat().st_mtime)
                break
        
        if not csv_file or not csv_file.exists():
            return jsonify({"error": "Query details not available for this execution"}), 404
        
        # Read CSV content
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        return jsonify({
            "success": True,
            "csv_content": csv_content,
            "csv_path": str(csv_file),
            "filename": csv_file.name,
            "execution_id": execution_id
        })
        
    except Exception as e:
        demo.logger.error(f"Error serving query details for {execution_id}: {e}")
        return jsonify({"error": f"Error loading query details: {str(e)}"}), 500

@app.route('/api/download-file')
def api_download_file():
    """Download a file by path (security restricted to output directory)"""
    file_path = request.args.get('path')
    
    if not file_path:
        return jsonify({"error": "File path is required"}), 400
    
    # Security: Ensure file is within the output directory
    try:
        # Component-wise containment. The string comparison this replaces let a
        # sibling through whenever its name merely began with the allowed one --
        # 'data/output_backup' beside 'data/output'.
        try:
            file_path = ISEEWebDemo.resolve_inside(Path('data/output'), file_path)
        except ValueError:
            return jsonify({"error": "Access denied: File outside allowed directory"}), 403

        if not file_path.is_file():
            return jsonify({"error": "File not found"}), 404
        
        return send_file(file_path, as_attachment=True, download_name=file_path.name)
        
    except Exception as e:
        demo.logger.error(f"Error downloading file {file_path}: {e}")
        return jsonify({"error": f"Error downloading file: {str(e)}"}), 500

@app.route('/api/api-status')
def api_api_status():
    """Get current API provider status"""
    api_status = demo._detect_apis()  # Get current status
    return jsonify(api_status)

@app.route('/api/setup-openrouter', methods=['POST'])
def api_setup_openrouter():
    """Set up OpenRouter API key"""
    data = request.get_json()
    api_key = data.get('api_key', '').strip()
    storage_method = data.get('storage_method', 'session')
    
    if not api_key:
        return jsonify({"success": False, "message": "API key is required"}), 400
    
    result = demo.setup_openrouter_api_key(api_key, storage_method)
    return jsonify(result)

@app.route('/api/validate-openrouter', methods=['POST'])
def api_validate_openrouter():
    """Validate OpenRouter API key without storing it"""
    data = request.get_json()
    api_key = data.get('api_key', '').strip()
    
    if not api_key:
        return jsonify({"valid": False, "message": "API key is required"}), 400
    
    if not api_key.startswith("sk-or-"):
        return jsonify({"valid": False, "message": "OpenRouter API keys should start with 'sk-or-'"})
    
    is_valid = demo.validate_openrouter_api_key(api_key)
    return jsonify({
        "valid": is_valid,
        "message": "API key is valid!" if is_valid else "API key validation failed"
    })

@app.route('/api/ollama-models')
def api_ollama_models():
    """Get available Ollama models"""
    api_status = demo._detect_apis()
    return jsonify({
        "available": api_status.get("ollama", False),
        "models": api_status.get("ollama_models", []),
        "count": len(api_status.get("ollama_models", []))
    })

@app.route('/api/rankings-status')
def api_rankings_status():
    """Get current rankings cache status"""
    try:
        status = demo.rankings_service.get_cache_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            "error": str(e),
            "cache_exists": False,
            "needs_update": True,
            "recommendation": "error"
        }), 500

@app.route('/api/update-rankings', methods=['POST'])
def api_update_rankings():
    """Update model rankings from OpenRouter API"""
    try:
        # Run the async update in a thread
        def run_update():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(demo.rankings_service._update_rankings())
                return success
            finally:
                loop.close()
        
        # Execute in background thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_update)
            success = future.result(timeout=30)  # 30 second timeout
        
        # Get updated status
        status = demo.rankings_service.get_cache_status()
        
        return jsonify({
            "success": success,
            "status": status,
            "message": "Rankings updated successfully" if success else "Update failed, using fallback data"
        })
        
    except concurrent.futures.TimeoutError:
        return jsonify({
            "success": False,
            "error": "Update timeout after 30 seconds",
            "message": "Rankings update timed out"
        }), 408
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": f"Update failed: {str(e)}"
        }), 500

@app.route('/api/enhance-query', methods=['POST'])
def api_enhance_query():
    """Generate enhanced versions of user query using validated patterns"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Import enhancement system
        from query_enhancement import get_enhancement_service
        from enhancement_tracking import get_enhancement_tracker
        
        # Generate enhancements
        enhancement_service = get_enhancement_service()
        result = enhancement_service.enhance_query(query)
        
        # Track enhancement generation
        tracker = get_enhancement_tracker()
        enhancement_ids = tracker.track_enhancement_generation(result)
        
        # Convert to JSON-serializable format
        response_data = {
            "original": result.original,
            "enhanced_versions": [
                {
                    "type": enhancement.type.value,
                    "query": enhancement.query,
                    "rationale": enhancement.rationale,
                    "expected_quality_improvement": enhancement.expected_quality_improvement,
                    "confidence_score": enhancement.confidence_score,
                    "enhancement_id": enhancement_ids[i] if i < len(enhancement_ids) else None
                }
                for i, enhancement in enumerate(result.enhanced_versions)
            ],
            "enhancement_analysis": result.enhancement_analysis,
            "processing_time_ms": result.processing_time_ms,
            "analytics": enhancement_service.get_analytics(),
            "tracking_enabled": True
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        demo.logger.error(f"Query enhancement failed: {str(e)}")
        return jsonify({
            "error": "Failed to enhance query",
            "original": data.get('query', '') if data else ''
        }), 500

@app.route('/api/track-enhancement-selection', methods=['POST'])
def api_track_enhancement_selection():
    """Track when user selects an enhancement"""
    try:
        data = request.get_json()
        enhancement_id = data.get('enhancement_id')
        selected = data.get('selected', True)
        
        if not enhancement_id:
            return jsonify({"error": "Enhancement ID is required"}), 400
        
        from enhancement_tracking import get_enhancement_tracker
        tracker = get_enhancement_tracker()
        tracker.track_enhancement_selection(enhancement_id, selected)
        
        return jsonify({
            "success": True,
            "enhancement_id": enhancement_id,
            "selected": selected
        })
        
    except Exception as e:
        demo.logger.error(f"Enhancement tracking failed: {str(e)}")
        return jsonify({
            "error": "Failed to track enhancement selection",
            "enhancement_id": data.get('enhancement_id', '') if data else ''
        }), 500

@app.route('/api/enhancement-analytics')
def api_enhancement_analytics():
    """Get enhancement effectiveness analytics"""
    try:
        from enhancement_tracking import get_enhancement_tracker
        tracker = get_enhancement_tracker()
        
        # Get effectiveness metrics
        effectiveness = tracker.get_enhancement_effectiveness()
        validation_report = tracker.get_validation_report()
        
        return jsonify({
            "effectiveness": effectiveness,
            "validation_report": validation_report,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        demo.logger.error(f"Enhancement analytics failed: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve enhancement analytics"
        }), 500

@app.route('/api/suggest-domains', methods=['POST'])
def api_suggest_domains():
    """Generate relevant domains based on user query using lightweight LLM"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Use a lightweight model to analyze query and suggest domains
        suggested_domains = demo._generate_dynamic_domains(query)
        
        return jsonify({
            "query": query,
            "suggested_domains": suggested_domains,
            "domain_count": len(suggested_domains)
        })
        
    except Exception as e:
        demo.logger.error(f"Domain suggestion failed: {str(e)}")
        return jsonify({
            "error": "Failed to generate domain suggestions",
            "fallback_domains": demo._get_fallback_domains()
        }), 500

@app.route('/api/models-fresh')
def api_models_fresh():
    """Get fresh model data (bypassing cache)"""
    try:
        # Run async model fetch in thread
        def run_fetch():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                models = loop.run_until_complete(demo.rankings_service.get_top_models(force_update=True))
                return models
            finally:
                loop.close()
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_fetch)
            models = future.result(timeout=30)
        
        return jsonify(models)
        
    except concurrent.futures.TimeoutError:
        return jsonify({"error": "Request timeout"}), 408
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/docs')
@app.route('/docs/')
@app.route('/docs/<path:doc_path>')
def documentation(doc_path=''):
    """Documentation pages with hierarchical navigation"""
    try:
        # Build documentation structure from docs/ directory
        docs_structure = _build_docs_structure()
        
        # Handle root docs page - show index/overview
        if not doc_path:
            doc_path = 'index'
        
        # If requesting a category (getting-started, advanced, etc.), show category index
        if doc_path in ['getting-started', 'configuration', 'advanced', 'development', 'specs']:
            content, breadcrumbs = _load_category_index(doc_path, docs_structure)
        else:
            # Load specific document
            content, breadcrumbs = _load_documentation_file(doc_path, docs_structure)
        
        return render_template('documentation.html', 
                             content=content, 
                             docs_structure=docs_structure,
                             breadcrumbs=breadcrumbs,
                             current_path=doc_path,
                             is_markdown=isinstance(content, dict))
    except Exception as e:
        logger.error(f"Error loading documentation: {e}")
        return render_template('documentation.html', 
                             content="<p>Error loading documentation.</p>",
                             docs_structure={},
                             breadcrumbs=[],
                             current_path=doc_path)

def _build_docs_structure():
    """Build hierarchical structure of all documentation files"""
    docs_base = Path('docs')
    structure = {
        'getting-started': {
            'title': 'Getting Started',
            'description': 'Quick start guides and introduction to ISEE',
            'files': []
        },
        'configuration': {
            'title': 'Configuration',
            'description': 'Setup and configuration guides',
            'files': []
        },
        'advanced': {
            'title': 'Advanced Features',
            'description': 'In-depth features and capabilities',
            'files': []
        },
        'development': {
            'title': 'Development',
            'description': 'Technical architecture and development guides',
            'files': []
        }
    }
    
    # Add specs if it exists
    specs_path = Path('specs')
    if specs_path.exists():
        structure['specs'] = {
            'title': 'Specifications',
            'description': 'Technical specifications and implementation details',
            'files': []
        }
    
    # Scan docs directory
    if docs_base.exists():
        for category in structure.keys():
            category_path = docs_base / category
            if category_path.exists():
                for md_file in category_path.glob('*.md'):
                    if md_file.name != 'README.md':  # Skip READMEs for now
                        file_info = {
                            'name': md_file.stem,
                            'title': _get_title_from_file(md_file),
                            'path': f"{category}/{md_file.stem}",
                            'file_path': md_file
                        }
                        structure[category]['files'].append(file_info)
    
    # Add specs files
    if specs_path.exists():
        for md_file in specs_path.glob('*.md'):
            file_info = {
                'name': md_file.stem,
                'title': _get_title_from_file(md_file),
                'path': f"specs/{md_file.stem}",
                'file_path': md_file
            }
            structure['specs']['files'].append(file_info)
    
    return structure

def _get_title_from_file(file_path):
    """Extract title from markdown file (first # heading or filename)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# '):
                    return line[2:].strip()
                elif line.startswith('## '):
                    return line[3:].strip()
        # Fallback to filename with formatting
        return file_path.stem.replace('_', ' ').replace('-', ' ').title()
    except:
        return file_path.stem.replace('_', ' ').replace('-', ' ').title()

def _load_category_index(category, docs_structure):
    """Generate index page for a documentation category"""
    if category not in docs_structure:
        return "<p>Category not found.</p>", [("Documentation", "/docs")]
    
    cat_info = docs_structure[category]
    content = f"<h1>{cat_info['title']}</h1>\n"
    content += f"<p class='category-description'>{cat_info['description']}</p>\n\n"
    
    if cat_info['files']:
        content += "<div class='file-list'>\n"
        for file_info in cat_info['files']:
            content += f"<div class='file-item'>\n"
            content += f"  <h3><a href='/docs/{file_info['path']}'>{file_info['title']}</a></h3>\n"
            content += f"</div>\n"
        content += "</div>\n"
    else:
        content += "<p>No documentation files found in this category.</p>"
    
    breadcrumbs = [
        ("Documentation", "/docs"),
        (cat_info['title'], f"/docs/{category}")
    ]
    
    return content, breadcrumbs

def _load_documentation_file(doc_path, docs_structure):
    """Load specific documentation file"""
    # Handle special case for index
    if doc_path == 'index':
        return _load_docs_index(docs_structure), [("Documentation", "/docs")]
    
    # Find the file in structure
    file_path = None
    category = None
    title = "Documentation"
    
    # Check if it's a category/file pattern
    if '/' in doc_path:
        cat, filename = doc_path.split('/', 1)
        if cat in docs_structure:
            for file_info in docs_structure[cat]['files']:
                if file_info['name'] == filename:
                    file_path = file_info['file_path']
                    category = cat
                    title = file_info['title']
                    break
    
    if not file_path:
        return "<p>Documentation file not found.</p>", [("Documentation", "/docs")]
    
    # Load raw markdown for client-side rendering
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Build breadcrumbs
        breadcrumbs = [("Documentation", "/docs")]
        if category:
            breadcrumbs.append((docs_structure[category]['title'], f"/docs/{category}"))
        breadcrumbs.append((title, f"/docs/{doc_path}"))
        
        # Return raw markdown with metadata for client-side rendering
        return {
            'markdown': markdown_content,
            'title': title,
            'type': 'markdown'
        }, breadcrumbs
    except Exception as e:
        logger.error(f"Error reading documentation file {file_path}: {e}")
        return "<p>Error loading documentation file.</p>", [("Documentation", "/docs")]

def _load_docs_index(docs_structure):
    """Generate main documentation index page"""
    content = "<h1>ISEE Meta Framework Documentation</h1>\n"
    content += "<p class='docs-intro'>Comprehensive guides and documentation for the ISEE Meta Framework system.</p>\n\n"
    
    for category, cat_info in docs_structure.items():
        if cat_info['files']:  # Only show categories with files
            content += f"<div class='category-section'>\n"
            content += f"  <h2><a href='/docs/{category}'>{cat_info['title']}</a></h2>\n"
            content += f"  <p class='category-description'>{cat_info['description']}</p>\n"
            content += f"  <div class='file-preview'>\n"
            
            # Show first few files as preview
            for file_info in cat_info['files'][:3]:
                content += f"    <div class='file-preview-item'>\n"
                content += f"      <a href='/docs/{file_info['path']}'>{file_info['title']}</a>\n"
                content += f"    </div>\n"
            
            if len(cat_info['files']) > 3:
                content += f"    <div class='file-preview-more'>\n"
                content += f"      <a href='/docs/{category}'>View all {len(cat_info['files'])} files →</a>\n"
                content += f"    </div>\n"
            
            content += f"  </div>\n"
            content += f"</div>\n\n"
    
    return content

@app.route('/api/extract_cognitive_diversity', methods=['POST'])
def extract_cognitive_diversity():
    """Extract cognitive diversity metadata for a given execution"""
    try:
        data = request.json
        execution_id = data.get('execution_id')
        
        if not execution_id:
            return jsonify({'success': False, 'error': 'No execution ID provided'}), 400
        
        # Get run directory from execution status (handles exec_* -> run_* mapping)
        execution_status = demo.execution_status.get(execution_id, {})
        run_directory = execution_status.get('run_directory')
        
        if not run_directory:
            # Fallback: try direct execution_id if it's already in run_* format
            if execution_id.startswith('run_'):
                # Resolved under data/output, not interpolated into it: this id comes
                # straight from the request body.
                try:
                    run_directory = str(ISEEWebDemo.resolve_inside(
                        Path("data/output"), execution_id))
                except ValueError:
                    return jsonify({'success': False, 'error': 'Invalid run id'}), 400
            else:
                return jsonify({'success': False, 'error': f'Run directory not found for execution: {execution_id}'}), 404
        
        if not os.path.exists(run_directory):
            # No fallback to "a run with a nearby timestamp".
            #
            # This searched data/output for a run whose HHMMSS was numerically
            # within 300 of the requested one and used that instead. Two things
            # wrong with it. It answered an unresolvable id with a DIFFERENT run --
            # the fourth place on this branch doing that -- and here the substituted
            # run is then WRITTEN to, because extraction produces files inside it.
            # A caller asking about one run could rewrite the index of another.
            #
            # And the arithmetic never meant what it says: HHMMSS is not a
            # quantity, so `abs(dir_time - target_time) <= 300` is not "within five
            # minutes". 195900 and 200000 differ by 100 and are one minute apart;
            # 195959 and 200000 differ by 41 and are one second apart.
            # The id, not the absolute path. The path answered with the machine's
            # directory layout ("D:\Dokumente\Projekte\...") to anyone who asked
            # about a run that does not exist, which is a free map of the filesystem.
            return jsonify({'success': False,
                            'error': f'No run named {execution_id}'}), 404

        # Extract run_id from directory path for the response
        run_id = os.path.basename(run_directory)
        
        # Extract cognitive diversity metadata
        # Use absolute paths and explicit Python to handle remote deployment
        import sys
        script_path = os.path.join(os.getcwd(), 'cognitive_diversity_extractor.py')
        
        # Enhanced subprocess call with better error handling
        try:
            # encoding and errors, not bare text=True. text=True decodes the pipe
            # with the platform default -- cp1252 here -- and the extractor's output
            # is full of emoji, so subprocess's reader thread died with
            # UnicodeDecodeError. The call still returned 0 and looked fine, but
            # result.stdout and result.stderr were then unusable: had the extraction
            # actually failed, the branch below would have had nothing to report.
            # A diagnostic path that breaks exactly when it is needed.
            #
            # This mirrors what the main run's subprocess already does in
            # execute_isee_command.
            result = subprocess.run(
                [sys.executable, script_path, run_directory],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=os.getcwd(), timeout=300)
            
            if result.returncode == 0:
                return jsonify({'success': True, 'run_id': run_id})
            else:
                # Log detailed error for debugging
                detailed_error = f'Extraction failed. Return code: {result.returncode}'
                if result.stderr:
                    detailed_error += f', STDERR: {result.stderr}'
                if result.stdout:
                    detailed_error += f', STDOUT: {result.stdout}'
                demo.logger.error(f"Cognitive diversity extraction failed: {detailed_error}")
                
                # A short reason for the caller; the traceback stays in the log.
                #
                # The last branch used to append 200 characters of raw stderr, which
                # is how a Python traceback -- absolute paths, module layout, local
                # variables in the message -- reached anyone who could provoke a
                # failure. The log above keeps all of it for whoever is debugging.
                user_error = 'Cognitive diversity extraction failed'
                stderr = str(result.stderr)
                if 'FileNotFoundError' in stderr:
                    user_error += ': required files not found'
                elif 'ModuleNotFoundError' in stderr:
                    user_error += ': missing Python dependencies'
                elif 'PermissionError' in stderr:
                    user_error += ': file permission denied'
                else:
                    user_error += '. The server log has the details.'

                return jsonify({'success': False, 'error': user_error}), 500
                
        except subprocess.TimeoutExpired:
            error_msg = 'Extraction timed out after 5 minutes'
            demo.logger.error(error_msg)
            return jsonify({'success': False, 'error': error_msg}), 504
        except FileNotFoundError as e:
            # The script path is a server path; the caller gets the fact, the log
            # gets the location.
            demo.logger.error(f'Extractor not found at {script_path}: {e}')
            return jsonify({'success': False,
                            'error': 'The extractor is missing on the server'}), 500
        except Exception as e:
            demo.logger.exception(f'Subprocess error during extraction: {e}')
            return jsonify({'success': False,
                            'error': 'Extraction could not be started'}), 500

    except Exception as e:
        demo.logger.exception(f"Error extracting cognitive diversity: {e}")
        return jsonify({'success': False,
                        'error': 'Extraction failed. The server log has the details.'}), 500

@app.route('/cognitive_diversity_explorer/<run_id>')
def cognitive_diversity_explorer(run_id):
    """Serve the cognitive diversity explorer for a specific run"""
    # The id was interpolated into a path unchecked. Flask's default converter will
    # not let it contain a slash, so this was never the traversal that /api/raw-
    # response had -- but "not exploitable today" is a property of the converter,
    # not of this code, and the sibling route was fixed hours ago. Same helper.
    try:
        run_directory = str(ISEEWebDemo.resolve_inside(Path("data/output"), run_id))
    except ValueError:
        return "Invalid run id", 400
    index_file = f"{run_directory}/cognitive_diversity_index.json"

    if not os.path.exists(index_file):
        # Build it, rather than telling the visitor to run a script.
        #
        # This answered 404 with "Please extract metadata first." for every run,
        # because nothing in either interface ran the extractor unless the user
        # pressed one particular button after one particular analysis. Any link that
        # arrived another way -- the run archive, a bookmark, a second visit --
        # landed on that message, and the feature looked broken because it was.
        #
        # The route already builds its HTML on demand, so building the index it
        # needs is the same bargain. Idempotent, bounded by the extractor's own
        # timeout, and only for a run that actually has responses to index.
        if not os.path.isdir(os.path.join(run_directory, "raw_responses")):
            return "This run has no raw responses to explore.", 404

        demo.logger.info(f"Extracting cognitive diversity metadata for {run_id}")
        try:
            extraction = subprocess.run(
                [sys.executable,
                 os.path.join(os.getcwd(), 'cognitive_diversity_extractor.py'),
                 run_directory],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=os.getcwd(), timeout=300)
        except (subprocess.TimeoutExpired, OSError) as e:
            demo.logger.error(f"Extraction for {run_id} could not run: {e}")
            return "Could not prepare this run for exploration.", 500

        if extraction.returncode != 0 or not os.path.exists(index_file):
            demo.logger.error(
                f"Extraction for {run_id} failed ({extraction.returncode}): "
                f"{extraction.stderr[-2000:]}")
            return "Could not prepare this run for exploration.", 500
    
    # Serve the cognitive diversity explorer HTML
    explorer_html = f"{run_directory}/cognitive_diversity_explorer.html"
    
    if not os.path.exists(explorer_html):
        # Create the explorer HTML if it doesn't exist
        try:
            from launch_cognitive_explorer import create_enhanced_web_interface
            create_enhanced_web_interface(index_file, explorer_html)
        except Exception as e:
            demo.logger.error(f"Error creating cognitive diversity explorer: {e}")
            return f"Error creating explorer interface: {str(e)}", 500
    
    # Update the HTML to use the correct API endpoint with run_id
    try:
        with open(explorer_html, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Replace the generic API endpoint with the run-specific one
        updated_html = html_content.replace(
            "const response = await fetch('/api/cognitive_diversity_data');",
            f"const response = await fetch('/api/cognitive_diversity_data/{run_id}');"
        )
        
        # Also update the raw response file API endpoint
        updated_html = updated_html.replace(
            "const response = await fetch(`/api/raw-response?file=${encodeURIComponent(file_path)}`);",
            f"const response = await fetch(`/api/raw-response/{run_id}?file=${{encodeURIComponent(file_path)}}`);"
        )
        
        # Alternative pattern that might be used
        updated_html = updated_html.replace(
            "/api/raw-response?file=",
            f"/api/raw-response/{run_id}?file="
        )
        
        # Write the updated HTML back
        with open(explorer_html, 'w', encoding='utf-8') as f:
            f.write(updated_html)
            
    except Exception as e:
        demo.logger.error(f"Error updating explorer HTML: {e}")
        # Continue serving the original file
    
    return send_file(explorer_html)

@app.route('/api/cognitive_diversity_data/<run_id>')
def cognitive_diversity_data(run_id):
    """Serve cognitive diversity data as JSON API"""
    try:
        index_file = str(ISEEWebDemo.resolve_inside(
            Path("data/output"), run_id, "cognitive_diversity_index.json"))
    except ValueError:
        return jsonify({'error': 'Invalid run id'}), 400
    
    if not os.path.exists(index_file):
        return jsonify({'error': 'Cognitive diversity data not found'}), 404
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data)
    except Exception as e:
        demo.logger.error(f"Error loading cognitive diversity data: {e}")
        return jsonify({'error': f'Error loading data: {str(e)}'}), 500

@app.route('/api/raw-response/<run_id>')
def serve_raw_response(run_id):
    """Serve raw response files for cognitive diversity explorer"""
    try:
        # Get the file parameter from query string
        file_path = request.args.get('file')
        
        if not file_path:
            return jsonify({'error': 'Missing file parameter'}), 400
        
        # Resolve under the run directory and refuse anything that escapes it.
        #
        # The previous check tested for '..' and a leading '/'. An absolute Windows
        # path satisfies neither, and os.path.join DISCARDS everything before an
        # absolute second argument -- so the run directory vanished and the file was
        # read and returned. Confirmed against the running app on 05.09.2026: a bait
        # file outside data/output came back HTTP 200 with its contents.
        #
        # The run id is validated too. It was interpolated into the path unchecked
        # while only the file parameter was examined.
        if not re.fullmatch(r'run_[0-9]{8}_[0-9]{6}(?:_[A-Za-z0-9]{1,8})?', run_id or ''):
            return jsonify({'error': 'Invalid run id'}), 400

        try:
            full_file_path = ISEEWebDemo.resolve_inside(
                Path('data/output'), run_id, file_path)
        except ValueError:
            return jsonify({'error': 'Invalid file path'}), 403

        if not os.path.exists(full_file_path):
            return jsonify({'error': f'File not found: {file_path}'}), 404
        
        # Read and serve the file content
        with open(full_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        demo.logger.error(f"Error serving raw response file: {e}")
        return jsonify({'error': f'Error reading file: {str(e)}'}), 500

@app.route('/about')
def about():
    """About page with editable content from markdown file"""
    try:
        content_path = Path('content/about.md')
        if content_path.exists():
            with open(content_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            html_content = markdown.markdown(
            markdown_content,
            extensions=['codehilite', 'fenced_code', 'tables', 'toc'],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': False  # We'll use Prism.js instead
                }
            }
        )
            return render_template('about.html', content=html_content)
        else:
            return render_template('about.html', content="<p>About content not found.</p>")
    except Exception as e:
        logger.error(f"Error loading about page: {e}")
        return render_template('about.html', content="<p>Error loading about content.</p>")

@app.route('/runs')
def runs_archive():
    """Overview of past runs and what each one produced - the owner asked for this
    on 02.09.2026 (docs/todos/2026-09-02-offene-punkte.md, section 1.1); the data
    was already on disk, only the page was missing.

    Its own page rather than folding into the Cognitive Diversity Explorer, per
    that todo's design decision: the Explorer is already a second, separately
    styled interface, and a third would be worse than one small page that links
    into both. This route only renders the shell; /api/runs supplies the data,
    which is what keeps the route a one-liner and the summarising logic in
    run_archive.py testable without a server (see tests/test_run_archive.py).
    """
    return render_template('run_archive.html')

@app.route('/api/runs')
def api_runs():
    """JSON summaries of every past run, newest first.

    All reading and summarising happens in run_archive.py's pure functions -
    this route exists only to call list_run_summaries and return the result, so
    that logic has exactly one caller-independent implementation instead of one
    copy here and a second, inevitably-drifting one under test.
    """
    from run_archive import list_run_summaries
    return jsonify(list_run_summaries(Path('data/output')))

if __name__ == '__main__':
    import os
    
    # Ensure output directory exists
    Path("data/output").mkdir(parents=True, exist_ok=True)
    
    # Get port from environment (Railway sets PORT) or default to 5001
    port = int(os.environ.get('PORT', 5001))
    
    # Run development server on specified port
    print("🚀 Starting ISEE Meta Framework...")
    print(f"📱 Open your browser to: http://localhost:{port}/isee-ui")
    print("💡 For full screen mode, press F11")
    
    # ⛔ The auto-reloader must stay off, and that is not a preference.
    #
    # `execution_status` lives in this process's memory, and analyses run for minutes as
    # child processes. When the reloader restarts the server — which it does on any file
    # touched while a run is in flight — the child is orphaned with an empty run
    # directory, and every later poll of /api/status/<id> answers "not_found" forever
    # because the dictionary that held it is gone. Observed exactly that way on
    # 2026-09-02: an edit during a run cost the run, silently.
    #
    # This used to be `debug = PORT is None`, i.e. on for the documented
    # `./scripts/dev-server.sh start` path and off only on Railway — so the mode that
    # destroys work was the default for local use. Opt in deliberately instead.
    debug_mode = os.environ.get('ISEE_FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
    if debug_mode:
        print("⚠️  Flask debug mode is ON. The auto-reloader will kill any analysis that "
              "is running when a file changes, and in-flight run status is lost with it.")
    app.run(debug=debug_mode, host='0.0.0.0', port=port)