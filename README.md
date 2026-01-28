# **MinIO Core**

*An educational project showcasing how to use MinIO with Python, covering both synchronous and asynchronous approaches.*

## **Project Structure**

```bash
minio-core/
├── app/                   # Main application code
├── docker-composes/       # Docker Compose configurations for MinIO servers
├── .env.example           # Example environment variables file
├── justfile               # Project-specific commands using Just
├── pixi.lock              # Locked dependency versions for reproducible environments
├── pixi.toml              # Pixi project configuration: environments, dependencies, and platforms
└── playground-testing/    # Jupyter notebooks for playground testing
```

Each directory includes its own `README.md` with detailed information about its contents and usage, and every file contains comprehensive inline comments to explain the code.

## **Dependencies Overview**

- [pydantic-settings](https://github.com/pydantic/pydantic-settings) — 
a Pydantic-powered library for managing application configuration and environment variables with strong typing, validation, and seamless `.env` support.

- [boto3](https://github.com/boto/boto3) — 
a synchronous Python client for Amazon S3 and other AWS services; compatible with S3-compatible storage systems, including MinIO. [^1]

- [aioboto3](https://github.com/terricain/aioboto3) — 
An asynchronous Python client for Amazon S3 and other AWS services; compatible with S3-compatible storage systems, including MinIO. [^1]

[^1]: I chose `boto3` over `minio-py` because the latter is synchronous-only, and MinIO doesn’t provide an official async client. On the other hand, `aioboto3`— built on top of `boto3` and `aiobotocore`— offers an async client with a nearly identical API. Since this is an educational project, I wanted to keep the codebase consistent and avoid using two entirely different libraries for sync and async operations.

- [just](https://github.com/casey/just) — 
a lightweight, cross-platform command runner that replaces complex shell scripts with clean, readable, and reusable project-specific recipes. [^2]

[^2]: Despite using `pixi`, there are issues with `pixi tasks` regarding environment variable handling from `.env` files and caching mechanism that is unclear and causes numerous errors. In contrast, `just` provides predictable, transparent execution without the complications encountered with `pixi tasks` system. I truly hope `pixi tasks` have been improved by the time you’re reading this! <33

### **Testing & Development Dependencies**
- [ipykernel](https://github.com/ipython/ipykernel) — 
the IPython kernel for Jupyter, enabling interactive notebook development and seamless integration with the project’s virtual environments.

- [requests](https://github.com/psf/requests) — 
a simple, yet powerful HTTP client for Python that makes it easy to send HTTP/1.1 requests; used here to test S3 presigned URL functionality directly from Python code without relying on external tools like `curl`.

## **Quick Start**

### **I. Prerequisites**

- [Docker and Docker Compose](https://docs.docker.com/engine/install/) container tools.
- [Pixi](https://pixi.sh/latest/) package manager.

> **Platform note**: All development and testing were performed on `linux-64`.  
> If you're using a different platform, you’ll need to:
> 1. Update the `platforms` list in the `pixi.toml` accordingly.
> 2. Ensure that platform-specific scripts are compatible with your operating system or replace them with equivalents.

### **II. Storage Setup**

1. **Clone the repository**

    ```bash
    git clone https://github.com/Sierra-Arn/minio-core.git
    cd minio-core
    ```

2. **Install dependencies**
    
    ```bash
    pixi install --all
    ```

3. **Activate pixi environment**
    
    ```bash
    pixi shell
    ```

4. **Setup environment configuration**
   ```bash
   just copy-env
   ```

5. **Start MinIO**
   ```bash
   just minio-up-1
   ```

### **III. Testing**

Once a storage is ready, you can run and test the MinIO implementation with interactive Jupyter notebooks in `playground-testing/`.

> **Note:**  
> Before running the notebooks, ensure that the `playground-testing/assets/` directory contains a couple of sample files with MIME types that match those specified in the `.env` file.

### **IV. Cleanup**

```bash
just minio-down-1
```

## **License**

This project is licensed under the [BSD-3-Clause License](LICENSE).