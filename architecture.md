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
