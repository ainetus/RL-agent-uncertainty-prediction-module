# Conformal Prediction for Grid2Op

This project runs conformal-prediction simulations for Grid2Op power-grid environments. The recommended way to run it is with Docker, because Docker installs the Python dependencies inside a reproducible Linux image and keeps generated results outside the image.

## Quick links

- [Setup using Docker](#running-project-with-docker)
  - [Troubleshoot](#docker-troubleshooting)
- [Setup using Conda](#running-project-using-conda-without-docker)
- [Project Structure](#project-structure)

## Running Project With Docker

### Prerequisites

Install Docker Desktop from the official Docker website:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

On Windows, make sure the `C:` drive has at least 10 GB of free space for the Docker image, build cache, and app runtime data.

Install Git LFS before building the Docker image. Git LFS is required because the `.pkl` model files are stored as large files:

```powershell
git lfs install
git lfs pull
```

On Windows, you can also download the installer from the [Git LFS website](https://git-lfs.com/).

### First Docker Run

Create a local environment file:

```bash
cp .env.example .env
```

In Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Start the smoke test:

```powershell
docker compose up --build
```

The default `.env.example` uses `CP_CONFIG=smoke`, which is the recommended first run. 
The full configuration can be much slower and heavier.

### Choose Where Docker Saves Results

Docker runs Python inside the container, so the final message prints a container path such as:

```text
Results were saved in: /app/src/RESULTS/SMOKE_TEST
```

That folder is mounted to a normal folder on your computer. By default, the host folder is `results/`.
To choose a different host folder, edit `.env`.


You can also choose where cache files are stored (keeping the cache folder between runs can save time on docker mounting):

```env
HOST_CACHE_DIR=F:/grid2op-cache
```


### Reuse an Existing Docker Setup

After the image has been built once, you usually do not need to rebuild it.

Run the existing Compose service again:

```powershell
docker compose up
```

Use `--build` only when Docker-related files, `requirements.txt`, or project files copied into the image have changed.

To run a different configuration without editing `.env`, start a one-off Compose run:

```powershell
docker compose run --rm -e CP_CONFIG=full app python main.py --config full
```

To run the smoke test again:

```powershell
docker compose run --rm -e CP_CONFIG=smoke app python main.py --config smoke
```

### Run Manual Commands Inside Docker

You can open a temporary shell inside the Docker environment. This uses the already built image, installed Python dependencies, and mounted results/cache folders:

```powershell
docker compose run --rm app bash
```

Inside that shell, run the project just like you would in a normal command line:

```bash
python main.py --config smoke
python main.py --config full
```

Leave the shell with:

```bash
exit
```

This is useful when you want to try different existing commands without rebuilding the image. If you edit Python files on the host, rebuild the image before expecting Docker to use those code changes. 
### Change Forecasting Mode Or Data

If the mode you need is already represented by `smoke` or `full`, use `CP_CONFIG` and `--config` as shown above.

If you need a different Grid2Op environment, agent, or forecaster, add or edit a Python configuration file first, then run Docker with that configuration. 
### Docker Outputs And Cache

Runtime files are written outside the image:

- `HOST_RESULTS_DIR` from `.env` is mounted to `/app/src/RESULTS`
- `HOST_CACHE_DIR` from `.env` is mounted to `/app/src/CACHE`
- the named Docker volume `grid2op-data` stores Grid2Op environment data under `/home/appuser/data_grid2op`

Logs are written to standard output and standard error:

```powershell
docker compose logs -f
```

### Stop And Finish Docker Work

If the simulation is currently running in the terminal, stop it gracefully with:

```text
Ctrl+C
```

Then stop and remove the Compose container/network:

```powershell
docker compose down
```

This does not delete generated results, cache folders, or the named `grid2op-data` volume.

Use this only when you intentionally want Docker to forget downloaded Grid2Op environment data:

```powershell
docker compose down --volumes
```

### Docker Troubleshooting

The default smoke/full case-14 configuration expects these files to exist before the image is built:

- `HBGB_14.pkl`
- `curriculum_14/model/saved_model.pb`
- `curriculum_14/actions/actions.npy`

If model files are missing or tiny pointer files, run this on the host before building:

```powershell
git lfs install
git lfs pull
```

After fetching Git LFS files, rebuild the Docker image:

```powershell
docker compose up --build
```

Possible issues and solutions:

- `Required artifact is missing`: fetch Git LFS files, then rebuild.
- `HBGB_14.pkl appears to be a Git LFS pointer`: from the project folder, run `git lfs install`, `git lfs pull`, `docker compose down`, then `docker compose up --build`.
- `Unknown CP_CONFIG`: set `CP_CONFIG=smoke` or `CP_CONFIG=full`.
- `read-only file system` while Docker is committing a build layer: check free space on the Windows `C:` drive. Docker Desktop stores its image/build data there by default and this project needs at least 10 GB free for the image and app data together.
- Permission errors in `docker-output` or `docker-cache`: remove the local mounted folder and let Docker recreate it, or fix ownership/permissions on the host.
- Grid2Op environment errors: keep the `grid2op-data` Docker volume so downloaded environment data persists across runs.
- Very slow startup: confirm `.env` still uses `CP_CONFIG=smoke` for validation.

## Running Project Using Conda (without Docker)

Use this path only if you want to run the project directly on the host machine. 

### Clone And Fetch Model Files

Install Git LFS to download the `.pkl` models. From the project folder, run:

```sh
git lfs install
git lfs pull
```

### Create A Conda Environment

Install Conda or Miniconda first:

- [Miniconda Quickstart Install](https://www.anaconda.com/docs/getting-started/miniconda/install#quickstart-install-instructions)

Create the environment:

```sh
conda create -n Grid2Op_CP python=3.11.13
```

Activate the environment:

```sh
conda activate Grid2Op_CP
```

Install the dependencies:

```sh
pip install -r requirements.txt
```

### Run A Local Experiment

Move to the `src/` folder:

```sh
cd src
```

The default command uses the full configuration from `src/config_full.py`:

```sh
python main.py
```

For a quick end-to-end smoke test, use `src/config_smoke.py`:

```sh
python main.py --config smoke
```

You can also select the smoke configuration with an environment variable:

```sh
CP_CONFIG=smoke python main.py
```

In PowerShell, use:

```powershell
$env:CP_CONFIG = "smoke"
python main.py
```

Both configuration files are plain Python. Paths such as `OUTPUT_DIR`, `MODEL_PATH`, and `FORECASTER_PATH` are resolved relative to the `src` configuration directory.

If needed, change parameters such as `CALIB_EPISODES`, `TEST_EPISODES`, and `OUTPUT_DIR` in the selected configuration file, then start the simulation again.

## Project Structure

The framework is implemented inside `src/`.

- `src/` contains the main pipeline and application code.
- `src/utils/` contains utilities used by the pipeline.
- `src/plotting/` contains plotting utilities.
- `src/conformalized_models/` contains conformalized model implementations.
- `src/stl_rules/` contains implemented STL rules.

New conformal models should be added to `src/conformalized_models/`. New STL rules should be added to `src/stl_rules/`.

The STL rules assume the project is checking whether a trajectory is safe or unsafe. If the project needs to predict something else, the rule structure may need to be refactored.
