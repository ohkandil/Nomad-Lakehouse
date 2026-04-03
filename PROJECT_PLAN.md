# Nomad Lakehouse Project Plan

This plan is derived from the MVP definition in `Local_Lakehouse_MVP.md` and adapted to the current project direction.

## Planning Assumptions

- Timeline: 4+ weeks
- Trino: post-MVP stretch goal
- Audience: recruiters, beginners, open-source contributors
- Runtime target: Ubuntu server (Linux-first deployment)
- Hardware target: 4GB RAM class machine, low-end CPU
- Ubuntu baseline: 24.04 LTS
- Catalog choice: JDBC catalog (PostgreSQL backend)
- Docker mode: rootful Docker
- Exposure model: LAN-only (private network)
- Go-to-market: build and blog/launch in parallel

## 1. Success Criteria

### Product outcomes

- Fresh clone to running environment in <= 15 minutes on low-spec hardware
- End-to-end Bronze -> Silver -> Gold flow demonstrated with sample data
- Time travel + schema evolution demonstrated with reproducible scripts/notebooks
- Clear architecture documentation and interview-ready talking points

### Quality outcomes

- Python codebase with type hints and consistent formatting
- CI pipeline for lint + tests
- Setup docs that enable first-time user success without direct support

## 2. Scope Definition

### In scope for MVP

- MinIO object storage
- Apache Iceberg table workflows
- One catalog implementation (JDBC catalog)
- DuckDB analytics
- Python pipelines for medallion layers
- Docker Compose orchestration
- Documentation and launch assets

### Out of scope for MVP

- Trino integration (deferred to stretch)
- Multi-node distributed deployment
- Cloud deployment templates (AWS/Azure)

## 3. Architecture Decisions

### Baseline stack

- Storage: MinIO
- Table format: Apache Iceberg
- Query engine: DuckDB
- Processing: Python + PyIceberg and/or PySpark (resource-aware)
- Metadata backend: PostgreSQL (JDBC catalog)
- Orchestration: Docker Compose
- Catalog: JDBC catalog (MVP default)

### Linux-first implementation strategy (Ubuntu)

- Treat Ubuntu as the primary runtime and validation environment
- Use bash scripts as default automation path; provide PowerShell scripts only as optional local-dev helpers
- Pin Docker and Compose plugin versions in setup docs
- Add systemd unit guidance for auto-start/restart on server reboot

### Resource-aware implementation strategy (4GB RAM class machine)

- Prioritize PyIceberg + DuckDB for core path
- Keep PySpark optional or run in constrained mode for demo-only steps
- Use smaller sample datasets by default with optional scale-up profiles
- Provide a "low-resource" compose profile and tuning guidance

## 4. Work Breakdown (5-Week Plan)

### Week 1: Foundation and Repo Scaffolding

Week 1 deliverables:

- Project structure and starter files
- Docker Compose baseline (MinIO + required supporting services)
- Environment config templates and health checks
- Initial README quick start skeleton
- Ubuntu server install and runbook draft

Week 1 tasks:

- Create folders: configs, scripts, docs, notebooks, data/sample
- Add compose services with pinned versions
- Add bash-first setup scripts for bucket and namespace initialization
- Add verification checklist and smoke test commands
- Add Linux service management instructions (systemd + journalctl diagnostics)
- Add Week 1 closure evidence checklist (`docs/week1-closure.md`)

Week 1 exit criteria:

- Services start successfully on target machine
- MinIO console reachable and storage bucket created
- Reboot-safe service startup is documented and tested
- Week 1 closure evidence is captured in `docs/week1-closure.md`

Week 1 minimum hardening checklist:

- Create a non-root sudo user for operations and disable password-based SSH login
- Configure SSH key authentication and disable direct root SSH access
- Enable UFW with allow rules only for SSH and required application ports on LAN
- Install and configure fail2ban for SSH protection
- Enable unattended security updates for Ubuntu packages
- Store secrets in .env files that are excluded from git and rotate default credentials immediately
- Restrict service bind addresses where possible (0.0.0.0 only when required)
- Add basic log review routine: journalctl service checks + Docker container health checks

### Week 2: Iceberg + Bronze Layer

Week 2 deliverables:

- Catalog setup (single choice)
- Bronze table creation workflow
- First ingestion script from CSV to Iceberg

Week 2 tasks:

- Configure JDBC catalog backend and validate connectivity
- Implement create_bronze_tables script
- Add minimal dataset and ingestion contract
- Validate metadata and files in object storage

Week 2 exit criteria:

- Bronze table created and queryable
- Re-runnable setup script without manual cleanup

### Week 3: Silver/Gold + Query Layer

Week 3 deliverables:

- Bronze -> Silver cleaning pipeline
- Silver -> Gold aggregation pipeline
- DuckDB query examples and expected outputs

Week 3 tasks:

- Implement data quality checks (nulls, dedupe, schema validation)
- Add Gold metrics table(s)
- Publish query examples in docs/examples
- Add notebook walkthrough for full data path

Week 3 exit criteria:

- End-to-end medallion run completes locally
- Gold layer provides business-readable metrics

### Week 4: Advanced Iceberg Features + Stabilization

Week 4 deliverables:

- Time travel examples
- Schema evolution examples
- Basic optimization notes (file size, compaction approach)

Week 4 tasks:

- Create repeatable snapshot/time-travel demo
- Add schema change migration script and compatibility checks
- Add troubleshooting notes for low-memory systems
- Add integration test skeleton for pipeline flow

Week 4 exit criteria:

- Advanced features demonstrated via script or notebook
- Core scenarios documented with known limitations

### Week 5: Portfolio Packaging and Launch

Week 5 deliverables:

- Final README polish and architecture docs
- Launch content (blog draft + share plan)
- Contribution guide + roadmap for stretch goals
- Ubuntu deployment guide with hardening checklist

Week 5 tasks:

- Add architecture diagram and screenshots
- Add local vs cloud cost framing
- Draft publishing checklist for Medium/Dev.to + social posting
- Add issues templates and first-timers contribution path
- Add Linux operational notes (backup, log rotation, upgrade process)

Week 5 exit criteria:

- Project is portfolio-ready and externally shareable
- Launch assets prepared and scheduled

## 5. Default Repository Backlog

### Core files to create

- docker-compose.yml
- .env.example
- pyproject.toml
- scripts/setup_minio.sh
- scripts/healthcheck.sh
- scripts/backup_metadata.sh
- scripts/restore_metadata.sh
- scripts/create_bronze_tables.py
- scripts/bronze_to_silver.py
- scripts/silver_to_gold.py
- docs/architecture.md
- docs/setup.md
- docs/examples.md
- docs/ubuntu-deploy.md
- CONTRIBUTING.md
- .github/workflows/ci.yml

### Early test coverage targets

- Script-level unit tests for transformations
- One integration test that runs Bronze -> Silver -> Gold on sample data
- Compose startup validation test/check script

## 6. Risks and Mitigations

- Risk: 4GB RAM constraints impact Spark usability
- Mitigation: Keep Spark optional, optimize defaults for DuckDB/PyIceberg first

- Risk: Linux host drift (Docker/OS package versions) causes setup failures
- Mitigation: Pin versions in docs, provide compatibility matrix, and include healthcheck script

- Risk: Service downtime after reboot or crash
- Mitigation: Provide systemd restart policy and startup verification checklist

- Risk: Catalog complexity delays MVP
- Mitigation: Start with one catalog only; document alternatives later

- Risk: New users fail setup
- Mitigation: Add health checks, troubleshooting matrix, and simple quick-start path

## 7. Decision Gates

### Gate A (End of Week 1)

- Confirm compose baseline is stable on target machine
- Confirm default memory profile works

### Gate B (End of Week 2)

- Confirm JDBC catalog integration and Bronze ingestion contract

### Gate C (End of Week 3)

- Confirm medallion flow is complete and reproducible

### Gate D (End of Week 5)

- Confirm portfolio readiness and launch checklist complete

## 8. Open Decisions

No blocking architecture decisions remain for MVP planning.

Future optional decision: when to add reverse proxy and TLS for internet-facing deployment.

## 9. Immediate Next Actions

1. Scaffold repository structure and baseline compose file for Ubuntu 24.04.
2. Implement low-resource profile first, then standard profile.
3. Implement JDBC catalog configuration and validate Bronze table creation.
4. Build Bronze ingestion first vertical slice (small but complete).
5. Start architecture doc and blog outline in parallel.
