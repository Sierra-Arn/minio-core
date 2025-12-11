# =====================================================
# Justfile Settings
# =====================================================
# Load environment variables from .env file into justfile context
# This allows justfile recipes to reference variables using ${VAR_NAME} syntax
set dotenv-load := true

# Export all loaded environment variables to child processes
# This makes variables available to all commands executed within recipes
# (e.g., docker compose, shell scripts, and other external tools)
set export := true


# =====================================================
# Environment Setup
# =====================================================
# Create local environment configuration file from template
# Copy .env.example to .env for initial project setup
# After copying, edit .env file to set your specific configuration values
copy-env:
    cp .env.example .env
    

# =====================================================  
# MinIO Persistent Storage Management  
# =====================================================  
# Initialize MinIO data directory structure  
# Creates the local directory specified by MINIO_DATA_PATH environment variable  
# This directory will store uploaded objects, bucket metadata, and MinIO state  
init-minio-storage:
	sudo mkdir -p ${MINIO_DATA_PATH}

# Remove MinIO persistent storage directory and all contents    
delete-minio-storage:
	sudo rm -rf ${MINIO_DATA_PATH}


# =====================================================
# Docker Compose 1: MinIO Server Initialization
# =====================================================
# Start MinIO server in detached mode with S3-compatible object storage
#
# -d flag (detached mode):
#   Runs containers in the background and releases the terminal immediately.
#   Without -d, docker compose would stream logs to stdout and block the shell
#   until interrupted. Detached mode is ideal for long-running storage services like MinIO.
minio-up-1:
	docker compose -f docker-composes/docker-compose.1-init.yml --env-file .env up -d

# Stop and remove MinIO container
minio-down-1:
	docker compose -f docker-composes/docker-compose.1-init.yml --env-file .env down


# =====================================================  
# Docker Compose 2: Persistent MinIO Server Initialization  
# =====================================================  
# Start MinIO server with full data persistence    
minio-up-2:  
    docker compose -f docker-composes/docker-compose.2-persistent.yml --env-file .env up -d

# Stop and remove MinIO container  
# Persistent data in MINIO_DATA_PATH is preserved for future restarts
minio-down-2:
    docker compose -f docker-composes/docker-compose.2-persistent.yml --env-file .env down