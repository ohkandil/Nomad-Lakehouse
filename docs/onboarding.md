# Nomad Lakehouse Engineer Onboarding

Welcome to the Nomad Lakehouse project! This document will help you get up to speed quickly and start contributing effectively.

## Project Overview

Nomad Lakehouse is a lightweight, local-first data lakehouse implementation for Ubuntu servers and homelabs. It demonstrates practical Bronze/Silver/Gold workflows using open-source components with minimal infrastructure overhead.

**Key Technologies:**

- **Storage:** MinIO (S3-compatible object storage)
- **Table Format:** DuckDB (Iceberg-ready roadmap)
- **Metadata Backend:** PostgreSQL (JDBC catalog validation)
- **Query Engine:** DuckDB (local analytics and materialization)
- **Orchestration:** Docker Compose
- **Pipelines:** Python scripts for medallion layers (Bronze → Silver → Gold)

**Live Demo:** <http://127.0.0.1:8088/> (when dashboard is running)
**Documentation:** See the `docs/` directory for detailed guides

## Quick Start (5-10 Minutes)

### Prerequisites

- Ubuntu 24.04 LTS (or compatible Linux)
- Docker Engine 24+ with Compose plugin
- Python 3.11+
- ~4GB RAM available
- Git

### Setup Commands

```bash
# 1. Clone repository
git clone https://github.com/ohkandil/nomad-lakehouse nomad-lakehouse
cd nomad-lakehouse

# 2. Configure environment
cp .env.example .env
python3 scripts/configure_setup_tui.py  # Interactive first-setup wizard
# Python 3.11 uses prompt fallback automatically; for OpenTUI on Python 3.12+: pip install -e .[tui]

# 3. Make scripts executable
chmod +x scripts/*.sh

# 4. Start core services
sudo ./scripts/setup_minio.sh

# 5. Initialize Python environment
INSTALL_PROFILE=lakehouse ./scripts/setup_python_env.sh
source .venv/bin/activate

# 6. Create Bronze tables and run initial pipeline
python3 scripts/create_bronze_tables.py
python3 scripts/bronze_to_silver.py  
python3 scripts/silver_to_gold.py

# 7. Launch admin dashboard (optional)
python3 -m uvicorn dashboard.app:app --host 127.0.0.1 --port 8088
```

### Verify It Works

After running the above commands, verify:

- [ ] MinIO console accessible at <http://127.0.0.1:9001>
- [ ] PostgreSQL accepting connections on port 5432
- [ ] Bronze table created: `SELECT COUNT(*) FROM bronze.orders` returns > 0
- [ ] Dashboard loads at <http://127.0.0.1:8088>
- [ ] Sample data visible in dashboard views

Wizard note:

- The setup wizard validates credentials/ports, supports dashboard auth configuration, and prints a post-save checklist for stack startup and secure dashboard access.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────┐    ┌────────────────┐
│   MinIO (S3)    │    │ PostgreSQL   │    │   Docker Host  │
│ Object Storage  │◄──►│ (Iceberg Cat)│◄──►│   (Ubuntu)     │
│   warehouse/    │    │   iceberg DB │    │                │
└─────────────────┘    └──────────────┘    └────────────────┘
                                       │
                             ┌─────────▼─────────┐
                             │   Python Scripts  │
                             │ create_bronze_*.py│
                             │ bronze_to_silver.py│
                             │ silver_to_gold.py │
                             └─────────▲─────────┘
                                       │
                             ┌─────────▼─────────┐
                             │   DuckDB          │
                             │ Local Analytics   │
                             │ lakehouse.duckdb  │
                             └───────────────────┘
                                       │
                             ┌─────────▼─────────┐
                             │ FastAPI Dashboard │
                             │ Health/Pipeline   │
                             │ Monitoring UI     │
                             └───────────────────┘
```

### Key Design Decisions

1. **Linux-first:** Optimized for Ubuntu 24.04 LTS deployment
2. **Resource-conscious:** Designed to run on 4GB RAM machines
3. **Modular pipelines:** Each medallion layer is a separate script
4. **Contract-first:** Bronze ingestion uses versioned JSON contracts
5. **Observability:** Built-in health checks and monitoring dashboard

## Key Files and Directories

| Path | Purpose |
|------|---------|
| `docker-compose.yml` | Service orchestration (MinIO + PostgreSQL) |
| `.env.example` | Environment variable template |
| `scripts/` | All automation and pipeline scripts |
| `scripts/create_bronze_tables.py` | Creates bronze.table and validates catalog |
| `scripts/bronze_to_silver.py` | Bronze → Silver transformation |
| `scripts/silver_to_gold.py` | Silver → Gold aggregation |
| `dashboard/` | FastAPI admin dashboard |
| `dashboard/app.py` | Main dashboard application |
| `data/` | Sample data, contracts, and output |
| `data/contracts/` | Ingestion contracts (versioned) |
| `data/output/` | DuckDB database files |
| `docs/` | Operational and architectural documentation |
| `tests/` | Test suites for validation |

## Common Developer Tasks

### Adding a New Data Source

1. Add sample data to `data/sample/`
2. Create ingestion contract in `data/contracts/` (follow existing pattern)
3. Update `create_bronze_tables.py` to handle new source type
4. Add table creation logic for new bronze table
5. Update medallion pipelines if needed

### Modifying the Medallion Pipeline

1. **Bronze Layer:** Edit `scripts/create_bronze_tables.py`
2. **Silver Layer:** Edit `scripts/bronze_to_silver.py`
3. **Gold Layer:** Edit `scripts/silver_to_gold.py`
4. Each script follows: read → transform/validate → write
5. Update corresponding tests in `tests/`

### Running Health Checks

```bash
# Check service status
sudo ./scripts/healthcheck.sh

# Verify MinIO is healthy
sudo docker compose ps minio

# Check PostgreSQL connectivity  
sudo docker compose exec postgres pg_isready -U iceberg -d iceberg

# Validate Python environment
source .venv/bin/activate
python3 -c "import duckdb, pandas; print('Dependencies OK')"
```

### Running the Test Suite

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Debugging Guide

### Common Issues and Solutions

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| MinIO fails to start | Port conflict | Check if ports 9000/9001 are free |
| PostgreSQL connection fails | Service not running | `sudo docker compose up -d postgres` |
| Python module not found | Environment not activated | `source .venv/bin/activate` |
| Bronze table empty | CSV import failed | Check `data/sample/orders.csv` format |
| Dashboard won't load | FastAPI not running | Start with `uvicorn dashboard.app:app` |
| Pipeline script fails | Missing dependency | Check `.venv` has all packages |

### Useful Diagnostic Commands

```bash
# View service logs
sudo docker compose logs -f minio
sudo docker compose logs -f postgres

# Check container status
sudo docker compose ps

# Verify Bronze table contents
source .venv/bin/activate
python3 -c "
import duckdb
con = duckdb.connect('data/output/lakehouse.duckdb')
print('Bronze rows:', con.execute('SELECT COUNT(*) FROM bronze.orders').fetchone()[0])
print('Sample data:')
print(con.execute('SELECT * FROM bronze.orders LIMIT 3').fetchdf())
"

# Check disk usage
sudo docker system df
du -sh data/output/
```

### Log Locations

- **Service logs:** `sudo docker compose logs <service>`
- **Application logs:** Console output when running scripts
- **Dashboard logs:** Terminal where `uvicorn` is running
- **Security scan logs:** Output of `sudo ./scripts/security_scan.sh`

## Contribution Guidelines

### Development Workflow

1. Create feature branch: `git checkout -b feature/your-feature-name`
2. Make changes with corresponding tests
3. Ensure CI passes: `pytest tests/`
4. Update documentation if changing behavior
5. Submit PR with descriptive title and summary

### Coding Standards

- **Python:** Use type hints, follow PEP 8, run `ruff check .`
- **Shell scripts:** Use `set -euo pipefail`, add comments for complex logic
- **Documentation:** Update docs in same PR as functional changes
- **Commits:** Use conventional commits (`feat:`, `fix:`, `docs:`)

### PR Requirements

- [ ] Code follows project style (run `ruff check .`)
- [ ] Tests pass (`pytest tests/`)
- [ ] Documentation updated if behavior changed
- [ ] Clear description of what and why
- [ ] Link to related issues if applicable

## Environment-Specific Notes

### For Junior Engineers

- Start with understanding the medallion flow: Bronze → Silver → Gold
- Follow the setup scripts as executable examples
- Focus on one pipeline script at a time
- Use the dashboard to visualize data flow
- Refer to `docs/examples.md` for code walkthroughs

### For Senior Engineers

- Review architecture decisions in `docs/architecture.md`
- Examine the resource constraints and optimization choices
- Consider scalability limitations and potential improvements
- Review CI/CD pipeline in `.github/workflows/ci.yml`
- Consider stretch goals from `PROJECT_PLAN.md`

### For Contractors/Consultants

- Focus on specific scoped features or bug fixes
- Maintain backward compatibility in pipeline contracts
- Document any environment-specific assumptions
- Follow existing patterns for new script development
- Ensure changes work in the documented Ubuntu 24.04 environment

## Troubleshooting Checklist

If you're stuck, work through this checklist:

### Phase 1: Environment

- [ ] Ubuntu 24.04 LTS running
- [ ] Docker Engine installed and user in docker group
- [ ] Python 3.11+ available
- [ ] At least 4GB RAM free
- [ ] Git repository cloned successfully

### Phase 2: Services

- [ ] `.env` file configured with secure passwords
- [ ] MinIO service healthy (`sudo docker compose ps minio`)
- [ ] PostgreSQL service healthy (`sudo docker compose ps postgres`)
- [ ] Warehouse bucket created in MinIO
- [ ] Network connectivity between services

### Phase 3: Python Environment

- [ ] Virtual environment activated (`source .venv/bin/activate`)
- [ ] Required packages installed (`pip list` shows duckdb, polgars, etc.)
- [ ] Scripts have execute permissions
- [ ] Environment variables loaded correctly

### Phase 4: Data Flow

- [ ] Sample data present in `data/sample/orders.csv`
- [ ] Bronze table created without errors
- [ ] Contract generated in `data/contracts/`
- [ ] Medallion pipelines run sequentially
- [ ] Output data appears in dashboard views

### Phase 5: Verification

- [ ] Dashboard loads and shows health metrics
- [ ] Data visible in pipeline/overview tabs
- [ ] Security scans pass (if applicable)
- [ ] Service logs show no errors
- [ ] Backup/restore scripts functional (if implemented)

## Getting Help

1. **Documentation First:** Check `docs/` directory for specific topics
2. **Closure Evidence:** Review `docs/week1-closure.md` and `week2-closure.md` for validation steps
3. **Project Plan:** See `PROJECT_PLAN.md` for roadmap and decisions
4. **Architecture Notes:** Read `docs/architecture.md` for design rationale
5. **Examples:** Look at `docs/examples.md` for code walkthroughs
6. **Team Communication:**
   - GitHub Issues for bug reports and feature requests
   - Pull Request discussions for code review
   - Check commit history for recent changes

## Next Steps After Onboarding

Once you've completed the basic setup and verification:

1. **Explore the codebase:** Run the codebase analyzer script for deeper insights

   ```bash
   python3 -m pip install -e '.[dev]'  # Install dev dependencies
   # Then use the onboarding skill analyzer if available
   ```

2. **Run a full cycle:** Execute all three pipeline scripts and verify outputs
3. **Experiment with modifications:** Try adding a new column to the orders contract
4. **Review test suite:** Understand what's tested and add tests for your changes
5. **Read documentation:** Deep dive into architecture and setup guides
6. **Consider contributions:** Look at open issues or propose improvements

Welcome to the team! Your contributions help make this local lakehouse implementation more robust and accessible to others learning modern data engineering patterns.
