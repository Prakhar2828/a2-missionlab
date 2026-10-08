# Zero-Cost Architecture

A2 MissionLab is designed so the core public application can operate at **$0 recurring cost**.

## Hosting

Primary options:

- **GitHub Pages** for the static public application.
- **Cloudflare Pages** as an alternate free static host.

A custom domain is optional and is intentionally not required. The project can use the free `github.io` or `pages.dev` URL.

## Data strategy

The source mission archive is far too large to mirror in the repository. The application will instead:

1. download public NASA/PDS source data during reproducible preprocessing,
2. extract only the fields needed for analysis,
3. write compact JSON/Parquet products,
4. preserve source identifiers, URLs, timestamps, hashes when practical, and transformation metadata,
5. link to or stream large imagery/audio/video from authoritative sources when allowed and technically practical.

## Browser analytics

Later phases can use DuckDB-WASM for local queries over compact Parquet files. This eliminates the need for a paid database server. Because browser memory is limited, the application will never attempt to load the complete raw Artemis II archive into memory.

## AI strategy

A paid cloud LLM API is **not required** for the core project.

The Mission Analyst will be built in layers:

1. deterministic evidence search and structured querying,
2. citation-first answer templates for common mission questions,
3. optional in-browser LLM inference on compatible devices,
4. optional user-supplied API key support only if ever desired later.

The public experience must remain useful without any paid model.

## CI/CD

Public GitHub repositories can use GitHub Actions for automated validation/build workflows without requiring a paid runner for normal public-repository use.

## Large-data and compute limitations

Zero dollars changes architecture, not project scope. We avoid:

- mirroring hundreds of gigabytes of NASA media,
- an always-on paid backend,
- a hosted vector database,
- paid LLM inference,
- paid map/3D APIs,
- paid observability platforms.

We replace them with preprocessing, static assets, client-side computation, public NASA data endpoints, local scientific Python, and reproducible cached derivatives.
