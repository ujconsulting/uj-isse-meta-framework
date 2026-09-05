# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is ISEE?

The Idea Synthesis and Extraction Engine (ISEE) is a multi-perspective research
platform. A question is put to many models through many cognitive frameworks at once,
and the answers are scored and synthesised — the point being the perspectives that
appear between different ways of thinking, not any single reply.

**The numbers, measured 03.09.2026 against the configuration and the code:**

| | |
| --- | --- |
| Models configured | **14**, one per vendor house (anthropic, openai, google, x-ai, deepseek, qwen, z-ai, moonshotai, mistralai, nvidia, minimax, upstage, tencent, meta) |
| Offered in the interface | all 14, with 8 preselected (`ui_priority: strategic`) |
| Cognitive frameworks | **11** |
| A full run | 66 calls, roughly $0.31 |
| A test run | 11 calls, roughly $0.12 |

OpenRouter is the gateway, not a vendor: "300+ models" describes its catalogue, not
this project's portfolio.

## Development Commands

### Server Management
```bash
# Start development server (recommended)
./scripts/dev-server.sh start

# Check server status and recent logs
./scripts/dev-server.sh status

# View real-time logs
./scripts/dev-server.sh logs

# Restart server (after code changes)
./scripts/dev-server.sh restart

# Stop server
./scripts/dev-server.sh stop

# Alternative: Direct Python execution
python app.py
```

**Primary Interface**: http://localhost:5001/isee-ui (Web UI - recommended)

**Run archive**: http://localhost:5001/runs — every past run, what it produced, what
it cost, and what is missing. Reads `data/output` and computes nothing new; a number
no run recorded reads "not recorded", never "$0.00".

- Always remember to check the last few session summaries for context. They are in the `session-summaries` folder.

### Latest Features (August 2025)
- **🎯 GLOBANT ENTERPRISE AI INTEGRATION RESTORED**: Successfully restored functionality from 15% to 67% success rate (44/66 real responses)
- **🔍 API SYNTAX EVOLUTION RESOLVED**: Diagnosed and fixed parameter compatibility issues for most Globant models
- **🏢 12/15 MODEL OPERATIONAL STATUS**: Claude, Gemini, GPT-4, Cohere, DeepSeek, Llama, Grok models fully functional
- **⚙️ DUAL PROVIDER ARCHITECTURE**: Maintained OpenRouter (100%) + Globant (80%) provider system with seamless switching
- **🔄 STRATEGIC DEBUGGING APPROACH**: Implemented systematic revert + targeted fixes methodology for complex API issues
- **📊 ISOLATED REMAINING ISSUES**: OpenAI o-series models (o1, o3, o3-mini) require additional Globant authentication

### Previous Features (January 2025)
- **🔥 DUAL API PROVIDER SYSTEM**: Complete implementation enabling seamless switching between OpenRouter and Globant Enterprise AI with intelligent hybrid mode and automatic fallback
- **🏢 Enterprise AI Integration**: Full Globant Enterprise AI support with enhanced security, compliance features, and curated model portfolio
- **⚡ Hybrid Provider Mode**: Intelligent provider selection based on performance metrics, health monitoring, and cost optimization
- **💰 Cross-Provider Cost Analysis**: Real-time cost comparison and optimization recommendations across API providers
- **🔄 Automatic Failover**: Seamless provider switching on failures with health-based selection and performance tracking
- **🎛️ Professional Provider UI**: Clean three-card provider selection interface with real-time status indicators
- **📊 Provider Health Monitoring**: Live tracking of API performance, success rates, and response times
- **Query Enhancement System**: AI-powered query optimization with 15-25% score improvements using validated patterns
- **Auto-Apply Enhancement UX**: One-click enhancement selection with optional auto-apply for streamlined workflow
- **Prominent Enhancement UI**: Visually striking green gradient apply button with icons and animations
- **Enhancement Effectiveness Tracking**: SQLite-based analytics system tracks query improvement success rates
- **Parallel Processing Optimization**: 4-minute full analysis (66 calls) and 1-minute validation (11 calls)
- **Cost-Optimized Execution**: 90% cost reduction - $0.50 for full analysis, $0.07 for validation
- **Live API Calls Visualization**: Real-time display of individual combinations during execution
- **Enhanced Progress Monitoring**: Shows "LLM + Cognitive Framework + Knowledge Domain" per API call
- **Professional UI**: Card-based active calls grid with animations and status indicators
- ⛔ **The quality-gate apparatus below is NOT called by any run.** `main.py` scores
  with `ScoringFramework.score_text()`; `score_text_with_quality_gates()` has no
  caller in the run path. Measured 03.09.2026: on the path that runs, a response
  consisting only of placeholders scores 0.292 and a good one 0.298 — they are
  indistinguishable. Repairing the gates and then enabling them is planned in
  `docs/plans/2026-09-03-bewertung-reparieren.md`; until that lands, treat every
  claim in the next four lines as describing code that exists but does not execute.
  - *(dormant)* Template failure auto-disqualification — placeholder responses to 0.05
  - *(dormant)* Buzzword penalty engine, up to -0.60
  - *(dormant)* Quality gates, five tiers
  - *(dormant)* Actionability and specificity weighted for a technical audience
- **Rank-Based Raw Response Files**: Automatic renaming of raw response files with rank prefixes (01_, 02_, etc.) based on evaluation scores for easy identification and sharing of top-performing responses
- **Enhanced Visual Illumination System**: Fixed parallel execution visual display to accurately reflect true cognitive diversity with improved model/framework matching and duplicate prevention
- **Cognitive Diversity Explorer**: Revolutionary platform with pixel-perfect design alignment - seamlessly integrated UI for exploring all 66 raw responses with professional enterprise aesthetics and enhanced metadata filtering
- **Hybrid Smart Curation System**: Complete research annotation platform with stars, tags, notes, favorites, and reviewed tracking
- **Run-Specific Storage**: Isolated annotation storage per query run for clean research workflow
- **Advanced Export**: "Download My Analysis Notes" with comprehensive JSON export including run metadata
- **Remote Deployment Compatibility**: Enhanced error handling and robust subprocess execution for seamless remote deployment

### Common Development Tasks

**Testing Core ISEE Logic:**
```bash
# Quick CLI analysis (testing) - with provider selection
python main.py --query "Your test question" --models 3 --provider openrouter

# Full comprehensive analysis with Globant Enterprise AI
python main.py --query "Your research question" --models 14 --provider globant --generate-reports

# Intelligent hybrid mode with automatic provider selection
python main.py --query "Your research question" --models 14 --provider hybrid --generate-reports

# Legacy usage (still supported - defaults to OpenRouter)
python main.py --query "Your research question" --models 14 --config openrouter_config.json --generate-reports
```

**Dependency Management:**
```bash
pip install -r requirements.txt
```

**Environment Setup:**
```bash
cp .env.template .env
# Edit .env with OPENROUTER_API_KEY=your_key_here
```

**Port Debugging:**
```bash
# Check if port 5001 is occupied
./scripts/check-ports.sh

# Kill processes on port 5001
./scripts/kill-port.sh 5001

# Clean all dev ports
./scripts/kill-dev-ports.sh
```

## Architecture Overview

### Strategic Analysis & Planning Documents

**DSPy Integration Research:**
- `docs/dspy_integration_analysis.md` - Comprehensive analysis of DSPy framework integration potential for ISEE response synthesis optimization. Includes detailed evaluation of query optimization vs. response synthesis use cases, 5 implementation approaches with code examples, risk assessment, and phased implementation strategy.

### Core Application Files

**Primary Controllers:**
- `main.py` (2,304 lines) - Core ISEE execution engine and CLI orchestration
- `app.py` (2,304 lines) - Flask web interface with REST API endpoints

**AI Integration Layer:**
- `model_api_integration.py` (931 lines) - Unified gateway to 300+ AI models across 5 providers
- `openrouter_rankings_service.py` (413 lines) - Dynamic model ranking and caching system (legacy, no longer used, no longer needed)

**Cognitive Diversity Engine:**
- `cognitive_framework_visualizer.py` (373 lines) - Manages 11 cognitive frameworks (Analytical, Creative, Critical, Systems, etc.)
- `instruction_templates.py` - Template library for cognitive framework prompts
- `domain_manager.py` (410 lines) - Knowledge domain contextualization. Knowledge domains are dynamically generated based on the the user query provided for each run

**Intelligence & Analytics:**
- `reporting.py` (1,056 lines) - Result synthesis and comprehensive report generation
- `evaluation_scoring.py` (1,204 lines) - OVERHAULED scoring system with template failure detection, buzzword penalties, and technical audience optimization
- `cost_estimation.py` (747 lines) - Real-time cost/time estimation before execution
- `performance_tracker.py` (413 lines) - SQLite-based performance monitoring system

### Data Flow Architecture

```
Query Input → Cost Estimation → Framework Selection → Domain Context → 
Model Execution (60 calls) → Real-time Monitoring → Result Evaluation → 
Synthesis & Reporting → Performance Tracking → Analysis Reports
```

### Key Directories

**Configuration:**
- `openrouter_config.json` - Primary AI model configuration (300+ models via single API key)
- `.env` - Environment variables and API keys

**Data Storage:**
- ⚠️ **Two run layouts exist side by side, and this is not a leftover.** `app.py`
  creates `data/output/run_TIMESTAMP` before launching the subprocess, while
  `main.py`'s constructor computes `data/output/YYYY-MM/weekN/run_TIMESTAMP`. So a
  run started in the browser lands flat and a run started at the command line lands
  nested. Any reader of `data/output` must handle both — the run archive did not at
  first, and silently listed seven of nine runs (05.09.2026). Unifying them is a
  change to the run output layout and therefore needs a reviewed plan.
- `data/output/YYYY-MM/weekX/run_YYYYMMDD_HHMMSS/` - CLI runs
- `data/output/run_YYYYMMDD_HHMMSS/` - Web UI runs
- `data/output/latest.txt` - the last run, as a path relative to `data/output`
- `data/analysis_reports/` - Generated analysis reports with search capabilities  
- `data/performance_tracking.db` - SQLite database for performance analytics

**Development Tools:**
- `scripts/` - Development server management and utilities
- `tests/` - Test harnesses and validation scripts
- `archive/` - Legacy components and historical versions

**Web Interface:**
- `isee-ui.html` - Primary web interface
- `static/css/` - Styling and design tokens
- `static/js/` - Frontend JavaScript
- `templates/` - Additional HTML templates

## Key Technical Concepts

### Cognitive Diversity System
ISEE uses **11** distinct cognitive frameworks (counted in the configuration and offered by the interface on 03.09.2026 — this file said 10 and listed 10, omitting Disruption):
- **Analytical** (🔍) - Systematic problem breakdown
- **Creative** (💡) - Novel solution generation  
- **Critical** (⚖️) - Rigorous evaluation and challenges
- **Integrative** (🔗) - Cross-domain synthesis
- **Pragmatic** (🔧) - Implementation-focused analysis
- **First Principles** (🧱) - Fundamental assumptions examination
- **Systems** (🌐) - Holistic interconnection analysis
- **Contrarian** (🔄) - Alternative perspective generation
- **Historical** (📚) - Past patterns and lessons
- **Futurist** (🚀) - Forward-looking implications
- **Disruption** (⚡) - What would make the current approach obsolete

### Model Distribution Strategy
- **14 models, one per vendor house.** Diversity is counted by house, not by model:
  two Anthropic models are one perspective wearing two names. The houses are listed
  in the table at the top of this file.
- **Balanced distribution** so no single model dominates a run.
- ⚠️ **No silent fallback.** A failed call is recorded as a failure and excluded from
  scoring and synthesis; it is never replaced by a simulated answer. That behaviour
  was removed deliberately (`8137f49`) — if you find something that looks like a
  graceful fallback, it is a defect, not a feature.

### Quality Assurance System

**Multi-criteria scoring — the effective weights, read from the code
(`create_default_framework`) on 03.09.2026:**

| Criterion | Weight |
| --- | ---: |
| Impact | 20.83 % |
| Feasibility | 20.83 % |
| Specificity | 20.83 % |
| Actionability | 16.67 % |
| Novelty | 12.50 % |
| Comprehensiveness | 8.33 % |
| **Total** | **100.00 %** |

⚠️ This file previously carried **three** different answers to this question, none of
which matched the code or each other. Until `0f5497e` the weights summed to 1.2 while
`calculate_weighted_score` divided by that total, so a documented 25 % contributed
20.83 %. The literals were rescaled — every relative proportion and every computed
score is unchanged — so what is documented is now what applies. **One table. If you
change the weights, change them here in the same commit.**

## Development Workflow

### Making Changes
1. **Start development server**: `./scripts/dev-server.sh start`
2. **Make code changes** in relevant files
3. **Test via web interface**: http://localhost:5001/isee-ui
4. **Monitor logs**: `./scripts/dev-server.sh logs` 
5. **Restart if needed**: `./scripts/dev-server.sh restart`

### Testing ISEE Logic
1. **Quick test**: Use CLI with `--models 3` for faster testing
2. **Full analysis**: Use Web UI for complete 60-call comprehensive analysis
3. **Monitor execution**: Real-time progress indicators show framework/model activity
4. **Review results**: Check `data/output/` for generated reports

### Performance Analysis
The system includes built-in performance tracking and self-analysis capabilities:
- **SQLite database**: Tracks all runs, performance metrics, API costs
- **Analysis reports**: Generated automatically for performance optimization
- **Model rankings**: Dynamic ranking system for model selection optimization

## Output Structure

### Primary Result Files
- `isee_result.md` - Primary comprehensive analysis (main deliverable)
- `queries_detailed_YYYYMMDD_HHMMSS.csv` - Complete query transparency log
- `model_performance.csv` - Performance metrics by model
- `combinations.csv` - All executed combinations with timing data

### Results Access Methods
1. **Web UI Quick View**: "📄 View Analysis (Quick)" button
2. **Complete Package Download**: "📥 Download Complete Package" button  
3. **Direct File Access**: `data/output/run_YYYYMMDD_HHMMSS/` directory

## Configuration Notes

### OpenRouter Integration (Recommended)
- **Single API Key**: Access 300+ models from all major providers
- **Unified Billing**: One account for Claude, GPT-4, Gemini, Llama, etc.
- **Pre-configured Collections**: Carefully curated model portfolios for cognitive diversity

### Globant Enterprise AI Integration — INACCESSIBLE FROM THIS ACCOUNT

⛔ **Everything in this section is inherited from upstream and cannot be verified
here.** This account has no Globant credentials and no way to obtain them: Globant
Enterprise AI is sales-led, with no self-serve signup and no public price list. A run
with `--provider globant` or `--provider hybrid` therefore aborts with exit code 2
rather than pretending.

The model list, the "100 % accessibility" claim and the per-request costs below were
written by the original author against an account we do not have. They are kept for
whoever inherits this fork with access — not as anything this project has observed.

Consolidating on OpenRouter and deleting these paths is Route A step 2 in
`docs/todos/2026-09-02-offene-punkte.md`.

#### Original section, unverified
- **132 AI Models Available**: Enterprise-grade model portfolio with enhanced security
- **15 Strategic Models Configured**: Optimized selection providing superior cognitive diversity
- **8 Provider Path Architecture**: Multiple access routes for enhanced resilience
- **API Documentation Sources**:
  - **GitHub Repository**: https://github.com/genexuslabs/saia-ingest
  - **Official Wiki**: https://wiki.genexus.com/enterprise-ai/wiki?20
  - **Supported Models**: https://wiki.genexus.com/enterprise-ai/wiki?200,Supported+Chat+Models
- **API Configuration**:
  - Base URL: `https://api.saia.ai`
  - Endpoint: `/chat/completions` (not `/v1/chat/completions`)
  - Authentication: Bearer token with API key
  - Model Format: `provider/model` (e.g., `anthropic/claude-3-5-haiku-20241022`)

#### ✅ **VERIFIED INTEGRATION DETAILS** (August 2025)

**Working Model Formats** (confirmed via testing and documentation):
- ✅ `anthropic/claude-3-5-haiku-20241022` - Standard Anthropic format
- ✅ `vertex_ai/claude-3-5-haiku-20241022` - Google Vertex AI format
- ✅ `openai/gpt-3.5-turbo` - OpenAI format
- ✅ `openai/gpt-4o-mini` - OpenAI format
- ✅ `google/gemini-2.5-pro` - Google direct format
- ❌ `claude-3-5-haiku-20241022` - Bare model names return 400 error

**Critical Requirements** (discovered through debugging):
1. **Model Format Mandatory**: API strictly requires `{provider}/{modelName}` format
   - Error if missing: "Invalid 'model' name. Must follow pattern {provider}/{modelName}"
2. **Endpoint URL**: Use `/chat/completions` (not `/api/v1/chat/completions`)
3. **Headers Required**: 
   - `Authorization: Bearer {api_key}`
   - `X-Organization-ID: {org_id}`
   - `Content-Type: application/json`

**Integration Status**: ✅ FULLY OPERATIONAL - EXPANDED 15-MODEL CONFIGURATION (August 22, 2025)
- Real API calls working with proper authentication across all 15 models
- Costs being charged normally (~$0.00007-0.000138 per request)
- 100% model accessibility rate (15/15 models responding successfully)
- Enhanced cognitive diversity with 8 different provider paths
- No billing setup required - API active immediately
- Superior capabilities vs original 12-model OpenRouter configuration

#### ✅ **EXPANDED 15-MODEL CONFIGURATION DETAILS** (August 22, 2025)

**Strategic Model Portfolio**:
1. **Claude Sonnet 4** (`anthropic/claude-sonnet-4-20250514`) - Frontier reasoning
2. **GPT-4 Turbo** (`azure/gpt-4.1`) - Reliable performance  
3. **Gemini 2.5 Pro** (`vertex_ai/gemini-2.5-pro`) - Verification master
4. **Grok 3 Mini** (`azure_ai_foundry/grok-3-mini`) - Contrarian thinking
5. **GPT-4o Mini** (`openai/gpt-4o-mini`) - Efficiency champion
6. **Claude 3.5 Haiku** (`awsbedrock/anthropic.claude-3.5-haiku`) - Speed demon
7. **OpenAI o3-mini** (`openai/o3-mini`) - Analytical excellence
8. **DeepSeek Chat V3** (`awsbedrock/us.deepseek.r1-v1:0`) - Mathematical reasoning
9. **Llama 3.3 70B** (`awsbedrock/meta.llama3-2-11b`) - Open source wisdom
10. **Cohere Command-A 2025** (`cohere/command-a-03-2025`) - Ensemble reasoning
11. **OpenAI o1** (`openai/o1`) - Advanced multi-step reasoning
12. **Llama 3.1 405B** (`awsbedrock/meta.llama3-1-405b`) - Massive parameter reasoning
13. **OpenAI o3** (`openai/o3`) - Research synthesis
14. **Grok 4** (`xai/grok-4`) - Advanced contrarian perspectives
15. **Amazon Nova Pro** (`awsbedrock/amazon.nova-pro-v1:0`) - AWS proprietary reasoning

**Provider Path Diversity** (8 unique architectures):
- `anthropic/` - Direct Anthropic access
- `openai/` - Direct OpenAI including o-series (4 models)
- `azure/` - Microsoft Azure hosting
- `vertex_ai/` - Google Cloud platform
- `awsbedrock/` - AWS enterprise hosting (4 models)
- `azure_ai_foundry/` - Microsoft experimental platform
- `xai/` - X.AI direct access
- `cohere/` - Enterprise AI direct

**Cognitive Coverage**: 100% gap elimination vs original OpenRouter configuration
**Success Rate**: 100% accessibility validation (15/15 models working)
**Usage**: `python main.py --provider globant --models 15` for full cognitive diversity

**Troubleshooting Notes**:
- Previous "simulation mode" was caused by model format validation errors
- Error handling system was masking 400 responses as "provider unavailable"
- Server restart required after configuration changes

### Environment Variables
```bash
OPENROUTER_API_KEY=your_openrouter_key_here

# Globant Enterprise AI (alternative provider)
GLOBANT_API_KEY=your_globant_api_key_here
GLOBANT_ORG_ID=your_organization_id
GLOBANT_BASE_URL=https://api.saia.ai

# Optional individual provider keys:
# ANTHROPIC_API_KEY=your_anthropic_key
# OPENAI_API_KEY=your_openai_key  
# GOOGLE_API_KEY=your_google_key

# How many analyses may be started, and how close together. Every start spends
# real money, and the web interface has no authentication, so this is the only
# thing bounding what a caller can run up. Defaults: 3 and 10.
# ISEE_MAX_CONCURRENT_RUNS=3
# ISEE_MAX_RUNS_PER_HOUR=10

# /api/suggest-domains asks Claude 3 Haiku for knowledge domains and is billed
# for it — cheap per call, but paid, and on the same unauthenticated interface.
# The UI makes one per analysis. Default: 60.
# ISEE_MAX_HELPER_CALLS_PER_HOUR=60
```

### Execution Settings
- **Standard Analysis**: 66 calls (~4 minutes, ~$0.50)
- **Quick Testing**: 11 calls (~1 minute, ~$0.07)
- **Comprehensive Research**: 60+ calls with custom parameters

## Troubleshooting

### Common Issues
- **Port 5001 occupied**: Use `./scripts/kill-port.sh 5001` or `./scripts/check-ports.sh`
- **API key errors**: Verify OpenRouter key at https://openrouter.ai/keys
- **Memory issues**: 60-call analysis requires adequate system resources
- **Slow first execution**: Model caching improves subsequent performance

### Debugging Tools
- **Real-time logs**: `./scripts/dev-server.sh logs`
- **Server status**: `./scripts/dev-server.sh status`
- **Error detection**: Built-in `api_error_detector.py` system
- **Performance tracking**: Check `data/performance_tracking.db`

## Key Design Principles

### Cognitive Diversity Over Consensus
ISEE is designed to reveal contradictory and complementary perspectives rather than seeking agreement. The goal is intellectual insurance against single-perspective limitations.

### High-Performance Parallel Execution
Advanced AsyncIO-based parallel execution system delivers 10x performance improvements. 66-call comprehensive analyses complete in 3-5 minutes vs 30+ minutes with intelligent rate limiting across all major AI providers.

### Economic Intelligence
Transparent cost management with real-time estimation before execution. Users know exactly what each analysis will cost before running.

### Academic Rigor
Professional interface optimized for research contexts with scholarly aesthetics and comprehensive documentation.

### Systematic Exploration
Every analysis runs the same comprehensive 60-call framework to ensure reliable cognitive diversity and prevent cherry-picking results.

## Development Dependencies

Core dependencies from `requirements.txt`:
```
requests>=2.28.0          # HTTP client
anthropic>=0.5.0          # Claude API
openai>=1.0.0            # OpenAI API  
flask>=2.3.0             # Web framework
rich>=13.0.0             # CLI formatting
pandas>=1.5.0            # Data analysis
matplotlib>=3.6.0        # Visualization
aiohttp>=3.8.0           # Async HTTP
tiktoken>=0.5.0          # Token counting
psutil>=5.9.0            # System monitoring
```

## File Organization

The codebase follows a modular architecture with clear separation of concerns:
- **Core Logic**: `main.py` orchestrates the entire ISEE process
- **Web Interface**: `app.py` provides Flask-based web demo  
- **AI Integration**: `model_api_integration.py` handles all AI model communications
- **Analysis Tools**: Separate modules for scoring, reporting, and performance tracking
- **Historical Data**: Comprehensive archiving in `data/output/` with organized folder structure

Total Core Codebase: ~11,000 lines across 9 key modules, designed for both accessibility and sophisticated multi-perspective research capabilities.

## 🧠 Cognitive Diversity Explorer - ✅ FULLY INTEGRATED & DESIGN ALIGNED

**Revolutionary platform that transforms ISEE from "smart synthesis tool" to "cognitive diversity exploration platform" - NOW SEAMLESSLY INTEGRATED INTO MAIN WEB UI WITH PIXEL-PERFECT DESIGN CONSISTENCY**

### 🎨 Enterprise Design System Alignment (August 2025)
- **Sophisticated Color Palette**: Migrated from bright purple/blue to professional amber/slate enterprise scheme
- **Typography Excellence**: Enhanced with SF Pro Display font stack and improved hierarchy
- **Premium Card Design**: Glass morphism effects with backdrop filters and sophisticated shadow systems
- **Consistent Spacing**: Professional padding/margin scale matching main ISEE UI exactly
- **Interactive Polish**: Enhanced hover states, focus treatments, and accessibility features
- **Visual Cohesion**: Both interfaces now provide identical professional appearance

### What is the Cognitive Diversity Explorer?

The Cognitive Diversity Explorer provides transparent access to all 66 unique AI thinking approaches from any ISEE analysis run. Instead of only seeing the final synthesis, users can explore, filter, compare, and discover insights across all raw responses with rich metadata and interactive tools.

### 🚀 **INTEGRATED ACCESS - NEW PRIMARY METHOD**

**The Cognitive Diversity Explorer is now seamlessly integrated into the main ISEE web interface!**

```bash
# 1. Run ISEE analysis through main web UI
http://localhost:5001/isee-ui

# 2. After analysis completion, click the third result option:
#    📄 View Analysis (Quick) | 📥 Download Package | 🧠 Explore Cognitive Diversity

# 3. Explorer opens automatically with all 66 responses loaded and ready to explore!
```

### 🛠️ **Alternative Launch Methods (for direct access)**

```bash
# Direct launch for any existing run
python launch_cognitive_explorer.py data/output/run_YYYYMMDD_HHMMSS

# CLI exploration and analysis
python cognitive_diversity_browser.py data/output/run_YYYYMMDD_HHMMSS/cognitive_diversity_index.json
```

### Core Components

**Files Created:**
- `cognitive_diversity_metadata_schema.json` - Complete 40+ field metadata specification
- `cognitive_diversity_extractor.py` - Metadata extraction and indexing system
- `cognitive_diversity_browser.py` - Interactive CLI exploration tool
- `cognitive_diversity_web.html` - Rich web interface template
- `launch_cognitive_explorer.py` - Web server and data integration
- `COGNITIVE_DIVERSITY_README.md` - Complete documentation and usage guide

### Enhanced Metadata Schema (40+ Fields)

**Core Metadata:**
- Performance scores (overall, feasibility, impact, novelty, etc.)
- Cognitive framework and thinking style analysis
- Model provider specializations and execution metrics

**Cognitive Analysis:**
- Framework specialization (what each approach does uniquely well)
- Thinking style (analytical, creative, contrarian, systematic, etc.)
- Innovation approach (incremental, disruptive, paradigm_shift, synthesis)
- Contrarian elements (ways responses challenge conventional thinking)

**Content Analysis:**
- Key concepts (extracted technologies, methodologies, frameworks)
- Approach categories (implementation, strategy, research, comparison)
- Success metrics (specific measurable criteria mentioned)
- Tone characteristics (formal, practical, innovative, ambitious)

**Discoverability:**
- Search keywords for enhanced discoverability
- Cognitive clusters (groupings of similar thinking approaches)
- Similarity relationships (related, contrasting, complementary responses)

### Key Use Cases

**🔍 Research & Discovery:**
- Study cognitive diversity patterns in AI responses
- Find alternative approaches to implementation challenges
- Discover breakthrough ideas that scored lower initially

**🎭 Framework Deep Dive:**
- Compare how different cognitive frameworks approach the same problem
- Identify framework specializations and optimal use cases
- Discover framework combinations that complement each other

**🤖 Model Specialization Analysis:**
- Explore how different AI models excel at different cognitive approaches
- Find model-framework combinations that produce exceptional results
- Identify model biases and blind spots

**🔄 Contrarian Perspective Discovery:**
- Find responses that challenge conventional wisdom
- Explore minority viewpoints that didn't make the synthesis
- Identify alternative approaches dismissed by mainstream thinking

### Web Interface Features

**Multi-Dimensional Filtering:**
- Score-based: Filter by performance tiers or score ranges
- Cognitive: Filter by frameworks, thinking styles, innovation approaches
- Technical: Filter by model providers, domains, complexity levels
- Content: Search by concepts, technologies, keywords

**Interactive Response Cards:**
- Performance metrics visualization
- Cognitive framework and model badges  
- Key concepts and approach categories
- Content preview and expandable details
- Similarity and relationship indicators

**Discovery Modes:**
- Cognitive Diversity Mapping (visual clustering of thinking approaches)
- Performance Analysis (score vs innovation plotting)
- Framework Effectiveness (systematic framework comparison)
- Contrarian Exploration (alternative viewpoint discovery)

### Integration with Main ISEE Workflow

The Cognitive Diversity Explorer seamlessly integrates with the main ISEE workflow:

1. **Run ISEE Analysis**: Generate 66 responses with standard ISEE process
2. **Extract Metadata**: `python cognitive_diversity_extractor.py <run_directory>`
3. **Explore Diversity**: Launch web or CLI tools to explore all perspectives
4. **Discover Insights**: Find hidden gems and alternative approaches
5. **Inform Decisions**: Use cognitive diversity insights for better research outcomes

### Competitive Advantage

This transforms ISEE into something **unprecedented in the AI space**:
- **No other AI system** offers transparent access to 66 different thinking approaches
- **Unique value proposition**: From "smart AI answers" to "cognitive diversity exploration"
- **Defensible differentiation**: Complex to replicate, high switching costs
- **Research platform**: Valuable for academic and enterprise research applications

### Development Status

**Current Status:** working since 05.09.2026 — before that, it could not open a
single run on this machine, while this section said "fully operational and
battle-tested".

What was wrong is worth remembering, because none of it looked like this feature
failing. The extractor printed a checkmark emoji; run by hand its output is a
terminal, which copes, but `app.py` runs it through a pipe, where Windows falls
back to cp1252 and the emoji raised `UnicodeEncodeError`. That print sits *before*
`save_index`, so no index was ever written — no run directory under `data/output`
had one. What surfaced was "extraction failed" plus a traceback about a checkmark,
which reads like a cosmetic complaint. Two more layers of the same fault sat behind
it: `launch_cognitive_explorer.py` opened files without naming an encoding, and
`app.py` read the pipe with bare `text=True`, killing the reader thread that was
supposed to report the error.

- ✅ Metadata extraction — runs, and is now triggered by the explorer route itself
      when a run has no index yet. It used to require one particular button after
      one particular analysis, so every other way in (the run archive, a bookmark,
      a second visit) hit "Please extract metadata first".
- ✅ Interactive web interface with real-time data serving
- ✅ CLI tools for programmatic analysis
- ⚠️ **Only for runs in the flat layout.** The route and the two APIs its page
      calls take a run id that cannot contain a slash, so a nested CLI run cannot be
      addressed at all. See the two-layout warning under Data Storage.
- ✅ Integration with existing ISEE workflow

**Next Development Phase:**
- Semantic search and similarity clustering
- Advanced visualization with D3.js cognitive mapping
- User contribution systems for community-driven insights
- Direct integration with main ISEE UI for seamless workflow

## Git Branch Management & Development Workflow

### Current Repository Structure (verified 2026-09-02)

This repository is a **fork** of
[joseph-fajen/ISEE_Meta_Framework](https://github.com/joseph-fajen/ISEE_Meta_Framework),
published as `ujconsulting/uj-isse-meta-framework` (renamed 2026-09-02 to match the
working directory). See README → "About This Fork" for the attribution and license notice.

**`main`**
- Identical to upstream `main` up to `a35f081` (2025-08-30); the only commits of our own
  are the license-compliance fix and the claudex-loop wiring.
- Remote: `origin` = our fork. `upstream` = joseph-fajen's repository (read-only).

**`upstream-refactor-codebase-plan`**
- Upstream's active refactoring line, fetched into this fork on 2026-09-02.
  15 commits, Dec 3–6 2025, +6,156/−5,016 lines.
- **What it does**: removes the `app.py` → `main.py` subprocess pattern (direct
  `isee_engine.py` imports), drops OpenRouter entirely in favour of Globant, flattens the
  output layout to `data/output/run_TIMESTAMP`, and fixes three model mislabels.
- **Why we did NOT adopt it**: it consolidates on Globant Enterprise AI, for which this
  account has no access — Globant is sales-led with no self-serve signup and no public
  price list. Phase 6 is also unfinished. Its *architectural* gains are
  provider-independent and can be cherry-picked later.
- **Measured, contrary to its own plan document**: the plan claims "−48%, ~2,500 lines
  removed"; the core is actually **104 lines larger** (12,465 → 12,569). OpenRouter was
  archived rather than deleted, and Phase 6 added more UI than Phases 1–5 removed.

⚠️ **Corrected 2026-09-02**: this section previously described two branches,
`feature/raw-response-analysis-to-csv-pipeline` ("87 files, 11,823+ insertions") and
`archive-remote-main`. **Neither exists** — not locally, not in this fork, not upstream.
The documented `git checkout` for them fails. Either the work was never pushed or it was
lost; do not plan around it.

### Branch Management Best Practices

**For Main ISEE Development:**
```bash
# Ensure you're on main and up-to-date
git checkout main
git status  # Should show "working tree clean"

# Start new feature development
git checkout -b feature/your-new-feature
# ... make changes ...
git commit -m "your changes"
```

**For inspecting upstream's refactoring line:**
```bash
# Read-only look at what upstream rebuilt (do not merge without deciding on Globant)
git checkout upstream-refactor-codebase-plan
cat docs/refactoring-plan.md

# Pull newer upstream work into the fork
git fetch upstream
git log --oneline main..upstream/main
```

**For Session Handoffs:**
- Main branch always clean and GitHub-synchronized
- Experimental work preserved in feature branches
- Comprehensive commit messages with session context
- CLAUDE.md updated to reflect current development state
- always remember to check the last few session summaries for context. They are in the `session-summaries` folder.
## Plan-Härtung mit claudex-loop (Cross-Model-Review)

Vor Umbauten, bei denen ein Denkfehler *im Plan* später teuer wird, läuft der Plan durch
`/claudex-loop:plan-review` — Claude schreibt, OpenAI Codex greift ihn read-only an.

**Einsetzen bei:** Provider-/Modell-Änderungen (OpenRouter ↔ Globant), Scoring-Umbauten,
Änderungen am Run-Ausgabelayout, neuen Flask-Routen, allem am Übergang Web-UI → CLI-
Subprozess, Deployment. **Nicht bei:** Einzeilern, reiner Doku, allem unter ~30 Minuten.

**Tabu-Scope in einem Satz:** Codex schreibt nicht, aber alles Gelesene geht an OpenAI —
also nie `.env`, `data/output/`, `data/analysis_reports/`, `data/*.db`, `archive/`
öffnen; Quellcode, Doku, Tests und `.env.template` sind freigegeben. Den Scope im
Review-Prompt wiederholen, nicht darauf vertrauen, dass Codex von selbst wegschaut.

**Ablage:** Plan *und* Review-Log nach `docs/plans/JJJJ-MM-TT-<thema>[-review-log].md`,
beides committen.

**Modell-Pin:** `gpt-5.6-terra` / `model_reasoning_effort=high` (Wrapper-Vorgabe);
⛔ nicht `sol` — reißt an echten Plänen das 10-Minuten-Ceiling. Aufruf **immer** über
`python tools/codex_ro.py`, nie direkt `codex exec`, und das Bash-Timeout auf 600000 ms
setzen.

**Prüfkatalog, Tabu-Scope im Detail und die Abnahme-Maßstäbe stehen in `AGENTS.md`** —
nicht hier duplizieren, zwei Quellen driften.
