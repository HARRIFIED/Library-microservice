# Flask Library Management API (Backend accessment task)

This project is a microservice-style library management API built with **Flask**. It is designed to manage a library system using a modular, enterprise-standard structure. The application uses SQLAlchemy for ORM, integrates with NATS JetStream for asynchronous messaging, and follows the application factory pattern for scalability and maintainability.

## Endpoints:
1. Add Book to library: POST /api/admin/books 
2. Get unavailable books: GET /api/admin/books/unavailable
3. Get users in the library: GET /api/admin/users
4. Remove book from library: DELETE /api/admin/books/:id
5. Get users and the books borrowed: GET /api/admin/users_borrowed

6. Get available books users: GET /api/frontend/books
7. Borrow any available book: POST /api/frontend/books/:id/borrow
8. Enroll: POST /api/frontend/users
9. Get book by ID: GET /api/frontend/books/1
   
## Get Started
This project contains two microservices—**admin-api** and **frontend-api**—that communicate with a [NATS Jetstream](https://nats.io/) server. You can run the entire stack using one of two approaches:

1. **Kubernetes with Skaffold**  
2. **Docker Compose** (easiest to run)

## Prerequisites

- **Python 3.9+**  
- **pip** (Python package manager) 
- **Docker:** Installed and running.
- **Kubernetes Cluster:** (For Skaffold option)  
  - You can use [Minikube](https://minikube.sigs.k8s.io/docs/start/) or any other Kubernetes provider.
- **Skaffold:** Installed. See the [Skaffold installation guide](https://skaffold.dev/docs/install/) for details.
- **kubectl:** Installed and configured to communicate with your Kubernetes cluster (if using the Skaffold option).

## Project Structure

```plaintext
.
├── admin-api
│   ├── Dockerfile
│   └── ... (source code)
├── frontend-api
│   ├── Dockerfile
│   └── ... (source code)
├── infra
│   └── k8s
│       ├── admin_depl.yaml
│       ├── frontend_depl.yaml
│       ├── nats_depl.yaml
│       └── ingress-srv.yaml
├── docker-compose.yaml
└── skaffold.yaml
```
## Installation

1. **Clone the repository:**

  ```bash
  git clone https://github.com/HARRIFIED/Library-microservice.git
  ```

## Option 1: Running with Kubernetes and Skaffold
This method deploys the services to your Kubernetes cluster and continuously rebuilds the images when you change the source code.

### 1. Build and Deploy
In the project root, run:

```bash
skaffold dev
```
#### This command will:
1. Watch for file changes.
2. Build the Docker images defined in the skaffold.yaml.
3. Deploy the Kubernetes manifests located in ./infra/k8s/*.


### 2. Accessing the Services
1. The Ingress resource is configured to route requests:
 a. library.dev/api/admin routes to the admin-api (port 5001).
 b. library.dev/api/frontend routes to the frontend-api (port 5000).
2. You might need to update your /etc/hosts (or local DNS) to point library.dev to your cluster’s IP (e.g., the Minikube IP).

## Option 2: Running with Docker Compose

This method builds the images locally using your Dockerfiles and runs all services on a single host.

1. Build and Start the Containers
In the project root, run:

```bash
docker-compose up 
```

