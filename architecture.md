# Lariba Cloud Architecture Documentation

## Step 1: Decide Tech Stack

To build a scalable, secure, and maintainable cloud platform, we have selected the following technologies for Lariba Cloud:

| Component           | Choice                  | Rationale |
|--------------------|------------------------|-----------|
| **Programming Language** | Python                | Simple, widely used, strong community support, and excellent libraries for cloud automation and APIs |
| **Backend Framework**    | FastAPI               | Lightweight, fast, modern API framework, ideal for building scalable cloud services |
| **Database**             | PostgreSQL            | Reliable relational database for structured cloud data and easy integration with Python |
| **Cloud Provider**       | AWS                   | Mature cloud ecosystem, wide range of services (compute, storage, DB), easy to scale |
| **Deployment**           | Docker                | Containerized apps allow portability, reproducibility, and simplified cloud deployment |
| **CI/CD**                | GitHub Actions        | Automates testing, building, and deployment workflows, integrates seamlessly with GitHub |

### Notes

- These choices will guide all future development decisions, including folder structure, API design, database schema, and deployment strategy.  
- This step is foundational; every component of Lariba Cloud will align with this tech stack.  

---

**Next Step:** System architecture design, API planning, and folder structure will follow this stack selection.

## Step 2: System Architecture

The Lariba Cloud system architecture defines how the different components interact to provide a scalable and reliable cloud platform.

### Overview

Users -> Frontend (optional dashboard/web interface)
│
▼
Backend API (FastAPI)
│
├── Auth Service # Handles user authentication and authorization
├── Cloud Service # Manages cloud resources and user projects
├── Analytics/Monitoring # Tracks usage, performance, and logs
│
Database (PostgreSQL)
│
Cloud Provider (AWS)
├── EC2 # Virtual machines
├── S3 # Storage
└── RDS # Managed database services

### Key Components

| Component        | Purpose |
|-----------------|---------|
| **Frontend**     | Optional user interface for managing cloud projects and services |
| **Backend API**  | Provides endpoints for user requests, handles business logic |
| **Auth Service** | Secure authentication using JWT or OAuth for users |
| **Cloud Service** | Manages compute, storage, and other cloud resources |
| **Analytics / Monitoring** | Tracks performance, usage, and error logs for the platform |
| **Database**     | Stores user data, project info, and cloud service configurations |
| **Cloud Provider** | Hosts infrastructure, storage, and database services |

### Notes

- The architecture is **modular**, allowing each service to be developed, tested, and deployed independently.
- This design supports **scalability**, **security**, and **automation-ready deployments**.
- Future features, like AI automation or advanced analytics, will integrate into the backend API layer.

---

**Next Step:** Once the architecture is documented, we will start planning the **Backend API routes and folder structure**.

## Step 3: Backend API Planning

The Backend API is the core of Lariba Cloud, handling user requests, business logic, and communication with the database and cloud services.

### API Overview

| Route                | Method | Purpose |
|----------------------|--------|---------|
| `/health`            | GET    | Check service status |
| `/users`             | GET/POST/PUT/DELETE | Manage users (registration, update, delete) |
| `/auth/login`        | POST   | Authenticate users and return JWT token |
| `/projects`          | GET/POST | Manage user cloud projects |
| `/services`          | GET/POST/PUT/DELETE | Manage cloud services within projects |
| `/analytics`         | GET    | Retrieve analytics and monitoring data |

> This is a **skeleton API**; additional routes can be added as features grow.

### Folder Structure for Backend (`src/`)

src/
- main.py # Application entry point (or app.py for Python)
├── config/ # Configuration files (DB, cloud, environment)
├── api/ # API routes and controllers
├── services/ # Business logic for cloud services and auth
├── models/ # Database models and schemas
├── database/ # DB connection setup and migrations
└── utils/ # Helper functions, utilities

### Notes

- **Modular structure** allows easy testing, maintenance, and scaling.
- Each route should correspond to a **service module** in `services/`.
- Future integrations (e.g., AI automation, cloud orchestration) will extend the API without affecting existing endpoints.

---

**Next Step:** Once API planning is complete, you can start implementing **database models and services** in `src/`, using this structure as a guide.

## Step 4: Database Models Planning

Lariba Cloud uses PostgreSQL as the primary database. The database stores all users, projects, and cloud service data.  

### Core Tables

| Table Name    | Columns & Types | Description |
|---------------|----------------|-------------|
| **users**     | id (UUID), name (string), email (string), password_hash (string), created_at (timestamp) | Stores user account information |
| **projects**  | id (UUID), user_id (UUID), name (string), description (string), created_at (timestamp) | Represents cloud projects owned by users |
| **services**  | id (UUID), project_id (UUID), type (string), status (string), created_at (timestamp) | Tracks cloud services within each project |
| **analytics** | id (UUID), project_id (UUID), metric (string), value (float), timestamp (timestamp) | Stores monitoring and analytics data |

### Relationships

- `users` → `projects` : **One-to-Many** (a user can have multiple projects)  
- `projects` → `services` : **One-to-Many** (a project can have multiple cloud services)  
- `projects` → `analytics` : **One-to-Many** (each project can generate multiple analytics records)  

### Folder Structure for Database (`src/database/`)

src/database/
├── db_connection.py # Database connection setup
├── models/ # Optional: model definitions for ORM
└── migrations/ # Database migration scripts

### Notes

- Using **UUIDs** ensures globally unique identifiers across distributed cloud systems.  
- Each table is designed to **scale** with the number of users and projects.  
- ORM (like SQLAlchemy for Python) can be used to map these tables to code for easier development.  

---

**Next Step:** Once database models are planned, you can start **implementing services** that interact with these tables in `src/services/`.

## Step 5: User Authentication System

The authentication system ensures that only authorized users can access Lariba Cloud services.  

### Authentication Approach

- **JWT (JSON Web Tokens)** for API authentication
  - Tokens issued on login and sent with each request
  - Short-lived access tokens + optional refresh tokens for security
- **Password Storage**
  - Store password hashes using secure algorithms (e.g., bcrypt)
  - Never store plain text passwords
- **Optional OAuth Integration**
  - Support login via Google, GitHub, or other OAuth providers in the future

### API Endpoints for Authentication

| Route          | Method | Purpose |
|----------------|--------|---------|
| `/auth/register` | POST | Register a new user |
| `/auth/login`    | POST | Authenticate user and return JWT token |
| `/auth/refresh`  | POST | Refresh access token using a valid refresh token |
| `/auth/logout`   | POST | Invalidate refresh token and log out user |

### Folder Structure

src/services/
├── auth_service.py # Handles authentication logic (JWT, hashing)
├── user_service.py # Handles user CRUD operations
└── utils/ # Optional: password hashing, token helpers


### Notes

- **Security is critical**: all sensitive operations must be validated and logged.
- This modular structure allows easy integration with the backend API routes (`/users`, `/projects`, `/services`).
- Future multi-factor authentication (MFA) can be added without changing core architecture.

---

**Next Step:** Once authentication is planned, we can move on to **Step 6: Cloud Provider Research and Deployment Planning**.

### Notes

- **Security is critical**: all sensitive operations must be validated and logged.
- This modular structure allows easy integration with the backend API routes (`/users`, `/projects`, `/services`).
- Future multi-factor authentication (MFA) can be added without changing core architecture.

---

**Next Step:** Once authentication is planned, we can move on to **Step 6: Cloud Provider Research and Deployment Planning**.

## Step 6: Cloud Provider Research & Deployment Planning

Lariba Cloud will be hosted on a cloud provider to ensure scalability, reliability, and security. This step outlines the chosen provider and deployment strategy.

### Recommended Cloud Provider: AWS

| Service         | Purpose |
|----------------|---------|
| **EC2**        | Virtual machines to run backend services |
| **S3**         | Object storage for user data, projects, and files |
| **RDS**        | Managed PostgreSQL database instances |
| **CloudWatch** | Monitoring, logging, and alerting |
| **IAM**        | Manage user access and security policies |

### Why AWS?

- Most mature and widely adopted cloud platform  
- Large ecosystem of services for compute, storage, database, monitoring, and security  
- Easy to scale as Lariba Cloud grows  
- Supports containerized deployment with Docker and orchestration with ECS or Kubernetes

### Deployment Strategy

- **Docker** will be used to containerize all backend services  
- **CI/CD with GitHub Actions**:
  - Push code → Run tests → Build Docker image → Deploy to staging/production
- **Infrastructure as Code (Optional)**:
  - Use Terraform or AWS CloudFormation for automated infrastructure setup
- **Monitoring & Logging**:
  - Track system health, resource usage, and errors via CloudWatch

### Notes

- Modular architecture allows each service to be deployed independently  
- Future cloud provider integrations (Azure, GCP) can be added without major refactoring  
- Security and access management handled via AWS IAM roles and policies

---

**Next Step:** After cloud deployment planning, the next step is **Step 7: CI/CD and Automation Planning**, where GitHub Actions and workflow automation will be defined.

## Step 7: CI/CD & Automation Planning

To ensure consistent quality, quick deployments, and automated workflows, Lariba Cloud will implement **CI/CD pipelines** and automation strategies.

### CI/CD with GitHub Actions

- **Continuous Integration (CI)**
  - On every push or pull request:
    - Run automated tests
    - Check code style / linting
    - Validate database migrations
- **Continuous Deployment (CD)**
  - On successful CI:
    - Build Docker images for backend services
    - Deploy to staging environment
    - Optional: Deploy to production after manual approval
- **Infrastructure Automation**
  - Optionally use **Terraform** or **CloudFormation** to provision cloud resources
  - Automates setup for EC2, S3, RDS, and IAM policies

### Workflow Example

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/

  deploy:
  runs-on: ubuntu-latest
  needs: build-and-test
  steps:
    - uses: actions/checkout@v3
    - name: Build Docker image
      run: docker build -t lariba-cloud .
    - name: Push & Deploy
      run: echo "Deployment steps here (e.g., AWS ECS or EC2)"
```
**Notes**

- CI/CD ensures fast feedback for developers and reduces manual errors  
- Modular workflows allow adding new services, testing, and deployment pipelines easily  
- Future automation can include:
  - Scheduled tasks for backups  
  - Automated scaling of services  
  - Notifications on failures or deployment events  

  
---

# **How to Add It**

### Option 1: GitHub Web
1. Open `docs/architecture.md`  
2. Click **Edit**  
3. Paste Step 7 content below Step 6  
4. Commit directly to main branch

### Option 2: Local + Git
```bash id="y7f2tr"
nano docs/architecture.md   # paste Step 7 content
git add docs/architecture.md
git commit -m "Add Step 7: CI/CD & Automation Planning"
git push origin main
```
## Step 8: Documentation & Wiki Setup

Proper documentation ensures Lariba Cloud is maintainable, scalable, and easy for future contributors to understand.

### Repository Documentation Structure

| File / Section        | Purpose |
|-----------------------|----------|
| `README.md`           | Project overview, installation guide, usage instructions |
| `docs/architecture.md`| System architecture and technical planning |
| `docs/api-spec.md`    | Detailed API endpoint documentation |
| `docs/deployment-guide.md` | Deployment instructions and cloud setup |
| `LICENSE`             | Defines legal usage and distribution rights |

### README Structure

The README should include:

1. Project Overview  
2. Features  
3. Tech Stack  
4. Installation Instructions  
5. Running Locally  
6. API Overview  
7. Deployment Summary  
8. Contribution Guidelines  

### GitHub Wiki (Optional)

Enable GitHub Wiki for extended documentation:

- Detailed architecture explanations
- Database schema diagrams
- Cloud deployment walkthrough
- Troubleshooting guides
- Future roadmap

### Contribution Guidelines

Add a `CONTRIBUTING.md` file including:

- Branch naming conventions
- Pull request process
- Code style rules
- Commit message standards

### Issue & Project Management

- Use GitHub Issues to track:
  - Bugs
  - Feature requests
  - Improvements
- Use GitHub Projects to manage:
  - Roadmap
  - Sprint planning
  - Task tracking

### Notes

- Clear documentation improves scalability and team collaboration.
- Keeping documentation updated is part of the development lifecycle.
- Professional documentation increases credibility for investors and contributors.

---

**Lariba Cloud Architecture Documentation Complete (Phase 1)**

The foundational planning phase is now complete.  
Next phase: Begin implementation of backend services and database models.
