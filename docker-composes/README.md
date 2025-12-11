# **Docker Compose Configurations**

This README gives a concise overview of the Docker Compose configurations: what each file is for and when to use it. For detailed configuration notes, environment variables, and usage commands are in `.env.example` and the `justfile`.

## **Files**

To keep configuration **readable and incremental**, the setup is split into two progressively layered files. Second file adds only new directives — and comments **only the additions**, assuming familiarity with the previous stage.

1. **`docker-compose.1-init.yml`**  
Base MinIO container: minimal config with essential settings and inline explanations.

2. **`docker-compose.2-persistent.yml`**  
Builds on (1) — adds persistent volume. Only new lines are commented.