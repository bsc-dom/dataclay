# PyCOMPSs - dataClay Integrated Environment

This example provides a Docker Compose setup to easily run and test the integration between **PyCOMPSs** and **dataClay**, including optional components such as **dislib**, **DDS**, etc.

We offer two environments:

- `docker-compose.yml`: Runs the **latest production versions** of all components from Docker Hub.
- `docker-compose.dev.yml`: Runs the **development versions** of `dataClay` and `dislib` for testing local changes.

---

## Running with Production Images

To use the **latest production versions** of `dataClay`, `dislib`, and other components:

```bash
docker compose up
```

Once the stack is running, you can enter the `compss` container and run an example:

```bash
docker compose exec compss /bin/bash
cd ~/examples/kmeans
./run_with_dataClay.sh
```

> ⚠️ The first time you run this, Docker will need to pull and build several images, so it may take a while.

---

## Running with Development Versions

To run the environment with your **local development versions** of `dataClay` and `dislib`, use the development Compose file:

```bash
docker compose -f docker-compose.dev.yml up
```

This environment is designed for contributors who want to test their changes to `dataClay` or `dislib`.

### ⚠️ Setting up `dislib` for Development

To use a local version of `dislib` inside the dev environment:

1. Clone the `dislib` repository locally (if you haven't already).
2. Create a symbolic link to your `dislib` repo inside this project:

   ```bash
   ln -s /path/to/your/dislib ./examples/compss-local/components/compss/dislib
   ```

   > **Note:** The folder `examples/compss-local/components/compss/dislib` is **not tracked by git**, so this step is required each time you set up a fresh environment.

This will make your local `dislib` code available inside the `compss` container.

---

## Using Jupyter Notebook

You can also explore and test examples using a Jupyter Notebook interface.

1. Launch the stack (`docker compose up` or `docker compose -f docker-compose.dev.yml up`).
2. Once the stack is up, open your browser and go to:

   ```
   http://localhost:8888
   ```

3. Navigate to the examples directory and experiment interactively.
