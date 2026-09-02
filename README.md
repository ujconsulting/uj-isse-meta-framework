# ISEE Meta Framework

**The Idea Synthesis and Extraction Engine • Systematic Multi-Perspective Research Platform**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

---

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/ujconsulting/uj-isse-meta-framework.git
cd uj-isse-meta-framework
pip install -r requirements.txt

# 2. Configure API access
cp .env.template .env
# Edit .env with your OpenRouter API key

# 3. Start the server
./scripts/dev-server.sh start

# 4. Open browser
open http://localhost:5001/isee-ui

# 5. After analysis completes
# Your results are saved as isee_result.md - access via web UI or data/output/ folder
```

**That's it!** The interface comes up with 14 curated models and 11 cognitive frameworks, ready for systematic multi-perspective research. Pick your language in the header — the interface is available in English and German.

**📥 Results Preview**: After your analysis completes, your comprehensive findings are saved as `isee_result.md` (the primary result file). Access your results 3 ways: quick web viewing, complete package download, or direct file system access. *See [Results Access](#-results-access) section below for full details.*

---

## 📖 What is ISEE?

ISEE transforms how we approach complex research by moving beyond single-perspective AI interactions to **systematic cognitive exploration**. Instead of asking one AI model for one answer, ISEE orchestrates multiple AI models through diverse cognitive frameworks to reveal breakthrough insights hiding in the spaces between different ways of thinking.

### The Core Innovation

**Traditional AI**: Ask a question → Get an answer → Accept cognitive limitations  
**ISEE**: Ask a question → **Systematically explore 66 perspectives** → Discover insights you couldn't anticipate

### Why Cognitive Diversity Matters

Complex problems resist simple solutions. The most transformative breakthroughs often emerge from the intersection of contradictory perspectives. ISEE provides **intellectual insurance against the cognitive limitations of homogeneous analysis**—whether single-model or consensus-based approaches.

---

## 🎯 How ISEE Works

### The Architecture

**🧠 14 Models from 14 Different Houses**  
Anthropic, OpenAI, Google, xAI, DeepSeek, Alibaba, Zhipu, Moonshot, Mistral, Meta, NVIDIA, MiniMax, Upstage and Tencent — one each. House diversity is the point; running fourteen variants of the same lineage would defeat it. Model ids and prices are verified against the live OpenRouter catalogue and recorded in `openrouter_config.json`.

**🔍 11 Cognitive Framework Lenses**  
From analytical rigor to contrarian deconstruction, ensuring comprehensive perspective coverage

**📊 Dynamic Knowledge Domain Mapping**  
Real-time identification of relevant expertise areas based on query complexity

**⚡ Automated Perspective Synthesis**  
Cluster-based organization revealing complementary, contradictory, and emergent insights

### The Process

1. **Enter your query**: Simply type your research question or complex problem
2. **Click "ANALYZE WITH ISEE"**: That's it - no parameter configuration needed
3. **Watch real-time progress**: Live indicators as ISEE works through 66 combinations of model, framework and domain. Calls that fail are reported as failures — never quietly replaced by a plausible-looking substitute.
4. **Review comprehensive results**: Access organized insights, scoring, and visual reports
5. **Download or view**: Multiple format options for your complete analysis

---

## 🎨 Web Interface Features

### Modern, Intuitive Design
- **Professional academic aesthetic** optimized for research contexts
- **Real-time progress tracking** with cognitive framework indicators
- **Ultra-simplified interface**: Just enter query and click analyze
- **14 models configured automatically**, 8 of them in the curated default selection
- **English and German interface**, switchable in the header and remembered per browser

### Comprehensive Analysis Standard
- **66 systematic calls** across models and frameworks automatically
- **~4 minutes** for a full run, **~1 minute** for an 11-call validation
- **~$0.31 per full run, ~$0.05 per validation** — measured from billed tokens, not estimated
- **Real-time indicators** show progress across all frameworks and models
- **True multi-perspective exploration** beyond single-model limitations

### Advanced Features
- **Cost reported per model, per house and in total** after every run, with the remaining OpenRouter balance
- **One API key** (OpenRouter) reaches all fourteen houses
- **Dynamic domain generation** based on query context
- **Multiple result formats** with instant viewing and download options
- **Professional report generation** with academic styling

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- OpenRouter API key (one key reaches every configured model)
- Git

### Step-by-Step Installation

```bash
# 1. Clone the repository
git clone https://github.com/ujconsulting/uj-isse-meta-framework.git
cd uj-isse-meta-framework

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.template .env
```

### Configure API Access

Edit `.env` file:
```bash
OPENROUTER_API_KEY=your_openrouter_key_here
```

**Get your OpenRouter API key**: [https://openrouter.ai/keys](https://openrouter.ai/keys)

### Launch ISEE

```bash
# Professional server management (recommended)
./scripts/dev-server.sh start

# Or direct Python execution
python app.py
```

**Access the interface**: http://localhost:5001/isee-ui

---

## 📋 Usage Guide

### Basic Usage

1. **Open ISEE**: Navigate to http://localhost:5001/isee-ui
2. **Enter your query**: Type your research question or complex problem
3. **Click "Run Full Analysis"**: No configuration needed - the system runs 66 calls
4. **Watch real-time progress**: See live indicators showing progress across all cognitive frameworks and models
5. **Review results**: Explore organized insights and download comprehensive reports in multiple formats

### Advanced Features

**Carefully Curated LLM Portfolio**:
- Pre-selected set of high-performance models optimized for cognitive diversity
- Automatically balanced across different reasoning capabilities and knowledge synthesis patterns
- No user configuration needed - optimal model selection handled automatically

**Comprehensive Cognitive Framework Coverage**:
- Analytical, Creative, Critical, Integrative, Pragmatic
- First Principles, Systems, Contrarian, Historical, Futurist, Disruption
- Each framework reveals different aspects of your query across all selected models

**Server Management**:
```bash
./scripts/dev-server.sh start    # Start server
./scripts/dev-server.sh status   # Check status and recent logs
./scripts/dev-server.sh restart  # Restart server (useful after updates)
./scripts/dev-server.sh logs     # Follow real-time logs
./scripts/dev-server.sh stop     # Stop server
```

---

## 📥 Results Access

After your ISEE analysis completes, your comprehensive research findings are saved as **`isee_result.md`** - the primary result file containing your complete multi-perspective analysis. This file is accessible through **three convenient methods**:

### 🚀 **Method 1: Quick View (Recommended for Reading)**
**Web UI: "📄 View Analysis (Quick)" Button**
- **What it does**: Opens `isee_result.md` in a new browser tab with professional formatting
- **Best for**: Reading and reviewing your analysis immediately
- **Contents**: Complete analysis with academic styling and navigation
- **Speed**: Instant access - no downloads required

### 📦 **Method 2: Complete Package Download (Recommended for Sharing)**
**Web UI: "📥 Download Complete Package" Button**
- **What it does**: Downloads a zip file to your Downloads folder containing all result files
- **Best for**: Sharing results, offline access, or comprehensive archiving
- **Contents**: 
  - `isee_result.md` (primary analysis file)
  - `queries_detailed_YYYYMMDD_HHMMSS.csv` (complete query transparency log)
  - Raw JSON data and processing logs
  - All supporting files and metadata
- **File location**: Downloads folder as `isee_results_YYYYMMDD_HHMMSS.zip`

### 🗂️ **Method 3: Direct File System Access (For Developers)**
**Location: `data/output/run_YYYYMMDD_HHMMSS/` Directory**
- **What it provides**: Direct access to all result files in the repository
- **Best for**: Development, automation, or integration with other tools
- **Contents**: Same as Method 2, but accessible directly in your project directory
- **Structure**:
  ```
  data/output/run_YYYYMMDD_HHMMSS/
  ├── isee_result.md              # ← PRIMARY RESULT FILE
  ├── queries_detailed_*.csv      # Complete query transparency
  ├── results.json               # Raw analysis data
  └── execution_log.txt          # Processing details
  ```

### 💡 **Quick Summary**
- **Want to read your analysis?** → Use "📄 View Analysis (Quick)"
- **Want to download and share?** → Use "📥 Download Complete Package" 
- **Want direct file access?** → Check `data/output/run_YYYYMMDD_HHMMSS/`
- **The main file you care about**: `isee_result.md` (your comprehensive analysis)

---

## 🔧 Configuration

### Core Configuration Files

- **`openrouter_config.json`**: Primary configuration designed for simple setup using a single OpenRouter API key. While OpenRouter provides access to a large number of LLMs, ISEE uses a carefully selected set optimized for cognitive diversity so users don't need to think about which models to use
- **`.env`**: Environment variables and API keys

### Available Scripts

ISEE includes comprehensive development scripts for server management and utilities:

- **`scripts/dev-server.sh`**: Complete server lifecycle management (start, stop, restart, status, logs)
- **`scripts/check-ports.sh`**: Port conflict detection and resolution
- **`scripts/kill-port.sh`**: Kill processes on specific ports
- **`scripts/kill-dev-ports.sh`**: Clean up development ports
- **`scripts/dev-aliases.sh`**: Convenient command aliases for faster workflows
- **`scripts/install-aliases.sh`**: Install development aliases system-wide

### Logging

- **`isee-ui.log`**: Application logs and debugging information
- **`dev-server.log`**: Server management logs
- All logs excluded from git via `.gitignore`

---

## 🎯 Who Should Use ISEE?

### Researchers & Academics
Exploring multifaceted problems requiring assumption-challenging and perspective synthesis

### Strategic Decision-Makers
Professionals whose choices require comprehensive analysis of unintended consequences and alternative frameworks

### Innovation Architects
Boundary-pushers seeking breakthrough insights that emerge from cognitive collision rather than linear thinking

---

## 💡 Example Use Cases

### Research Questions
*"How could blockchain governance models evolve to systematically incorporate insights from classical music ensemble leadership—where conductors, concertmasters, and section leaders create dynamic decision-making hierarchies that balance individual expression with collective precision?"*

### Strategic Innovation  
*"What would emerge if we designed smart contract development education programs inspired by conservatory training methods—combining technical rigor with artistic intuition, peer mentorship traditions, and performance-under-pressure experiences that classical musicians develop?"*

### Cross-Domain Synthesis
*"How might sustainable ecosystem management practices inform the design of stake pool operator communities, where long-term thinking, resource stewardship, and symbiotic relationships create resilient networks that adapt to environmental changes while maintaining core stability?"*

Each query reveals insights across multiple cognitive clusters, ensuring comprehensive understanding beyond single-perspective limitations.

---

## 🔍 Technical Architecture

### Core Python Capabilities

**🎯 Primary Controllers:**
- **`main.py`** (3,473 lines) - Core execution engine and CLI orchestration
- **`app.py`** (3,031 lines) - Flask web interface with REST API endpoints

**🤖 AI Integration Layer:**
- **`model_api_integration.py`** - Provider gateway. Sends only the sampling parameters a model actually accepts, and carries the HTTP status on every error
- **`openrouter_rankings_service.py`** - Ranking metadata only. It is *not* a source of models: the configuration decides what exists, and rankings merely annotate it

**🧠 Cognitive Diversity Engine:**
- **`cognitive_framework_visualizer.py`** (379 lines) - Manages 11 cognitive frameworks (Analytical, Creative, Critical, …, Disruption)
- **`domain_manager.py`** (410 lines) - Knowledge domain contextualization

**📊 Intelligence & Analytics:**
- **`reporting.py`** (1,056 lines) - Result synthesis and comprehensive report generation
- **`cost_estimation.py`** (958 lines) - Pre-run cost/time estimation, priced from the rates recorded per model
- **`run_cost_report.py`** - What a run actually cost, from the tokens the provider billed
- **`performance_tracker.py`** (413 lines) - SQLite-based performance monitoring

### Data Flow

```
Query → Cost Estimation → Framework Selection → Domain Context → 
Model Execution → Real-time Monitoring → Result Evaluation → 
Synthesis & Reporting → Performance Tracking
```

### Key Technical Innovations

🔬 **Cognitive Diversity**: 10 distinct thinking frameworks ensure comprehensive analysis beyond single-perspective limitations

🌐 **Unified Model Access**: One OpenRouter key for all fourteen houses. A failed call is recorded as a failure with its HTTP status — there is no fallback that invents a response

💰 **Economic Intelligence**: Transparent cost management and real-time estimation before execution

🎨 **Academic Design**: Professional interface optimized for research contexts with scholarly aesthetics

📈 **Continuous Learning**: Performance analytics and model ranking drive systematic optimization

**Total Core Codebase**: ~11,000 lines with 9 dependencies, designed for both accessibility and sophisticated multi-perspective research

---

## 🚀 Development

### Development Workflow

```bash
# Start development server
./scripts/dev-server.sh start

# View real-time logs
./scripts/dev-server.sh logs

# Check system status
./scripts/dev-server.sh status

# Stop server
./scripts/dev-server.sh stop
```

### Repository Structure

```
uj-isse-meta-framework/
├── isee-ui.html              # Primary web interface (incl. EN/DE switch)
├── app.py                    # Flask backend server
├── main.py                   # Core ISEE logic
├── openrouter_config.json    # Models, parameters and their recorded prices
├── run_cost_report.py        # Actual cost of a run, from billed tokens
├── requirements.txt          # Python dependencies
├── scripts/                  # Development tools
├── tests/                    # Test suite
├── docs/                     # Documentation and plans
├── data/                     # Output and tracking
└── archive/                  # Historical versions
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly using the web interface
5. Submit a pull request

---

## 📄 License

Licensed under the **Apache License, Version 2.0** — see the [LICENSE](LICENSE) file for
the full text, or <https://www.apache.org/licenses/LICENSE-2.0>.

> **Note on a discrepancy inherited from upstream:** the upstream README declared the MIT
> License while the `LICENSE` file invoked Apache-2.0, and that `LICENSE` file contained
> only the Apache appendix boilerplate rather than the license text itself. This fork
> resolves the contradiction in favour of the `LICENSE` file, which is the operative
> grant, and ships the complete Apache-2.0 text so recipients actually receive a copy of
> the license as Section 4(a) requires. The original copyright line is preserved
> unchanged. No relicensing is intended or claimed.

---

## 🔎 Honest by Default

Three behaviours in this fork exist because their absence had cost real work.

**A failed call is reported as a failure.** Every branch that could not reach a model
used to return a *simulated* answer instead, so a run in which all 66 calls returned
HTTP 400 produced a complete, plausible, entirely fabricated report — and called itself a
success. Failures are now recorded with model, HTTP status and error text, written to
`failed_responses/` rather than mixed in with real answers, excluded from scoring, and
counted in the summary. The exit code says which happened: `0` all succeeded, `1` some
failed, `2` nothing worked.

**Cost is reported from what was billed, not from what was assumed.** After every run:

```
  Model                      calls        in       out       USD
  GPT-5.6 Luna                   3       344     6,265    0.0076
  TOTAL                          3                        0.0076

  By house (the vendor behind the model, not the gateway):
    openai                   1 model(s)    3 calls     0.0076  100.0%

  OpenRouter balance: $18.11 remaining ($113.37 used of $131.48)
  At this run's cost that is roughly 2,386 more runs.
```

Token counts come from OpenRouter's own `usage` block; prices from the `pricing` recorded
on each model in `openrouter_config.json`. A model with no recorded price is listed as
unpriced and left out of the total rather than silently given a default. Run
`python run_cost_report.py <run_directory>` to reprint it, or with no arguments for just
the balance.

**Estimates are checkable.** The pre-run estimate and the post-run bill are both shown, so
the forecast can be compared against reality instead of standing unchecked. That matters:
the previous estimate was a flat $0.08 per combination regardless of which models were
configured, which overstated a full run by a factor of seventeen.

---

## 🌍 Interface Language

English and German, switchable in the header (`EN | DE`). The choice is remembered per
browser; on a first visit the browser's own language decides.

Not translated: the Cognitive Diversity Explorer, `/docs`, `/about`, and messages produced
by the backend. Those are separate surfaces.

---

## 🍴 About This Fork

This repository is a fork of
**[joseph-fajen/ISEE_Meta_Framework](https://github.com/joseph-fajen/ISEE_Meta_Framework)**,
maintained by UJ Consulting for internal research use.

Original work: Copyright 2025 **Joseph Fajen**, licensed under Apache-2.0. All copyright,
attribution and license notices from the original work are retained.

**Modifications in this fork** (Apache-2.0 §4(b) notice — files changed relative to
upstream `main`):

| File | Change |
| --- | --- |
| `LICENSE` | Replaced the 19-line appendix stub with the complete Apache-2.0 text; original copyright line preserved verbatim |
| `README.md` | Corrected the license statement (MIT → Apache-2.0), added this fork and modification notice, pointed the clone instructions at this fork |
| `CLAUDE.md` | Added a pointer to the cross-model plan-review workflow |
| `.gitignore` | Added entries for review working files |
| `AGENTS.md`, `.codex/`, `tools/` | New files added by this fork; not present upstream |

Upstream is not responsible for, and does not endorse, these modifications.

---

## 🏗️ Built By

**Joseph Fajen**

- Senior technical writer at IOHK
- Developed using Claude Code.

---

## 🌟 Philosophy

ISEE represents a fundamental shift from **information retrieval** to **perspective archaeology**—systematically excavating the full cognitive territory surrounding complex questions. It's designed for moments when you need more than expert responses or agreement—when you need to discover perspectives you couldn't formulate, assumptions you didn't know you held, and possibilities hiding in intellectual blind spots.

**Try ISEE. Explore systematically. Discover what cognitive diversity reveals.**

---

*Ready to move beyond single-perspective limitations? Start your systematic multi-perspective research journey today.*