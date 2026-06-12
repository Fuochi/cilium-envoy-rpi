# cilium-envoy (arm64 / Raspberry Pi)

Unofficial automated builds of [cilium/proxy](https://github.com/cilium/proxy)
(cilium-envoy) for **arm64**, compiled with **gperftools** instead of tcmalloc
so the binary works on the Raspberry Pi kernel. Images are published to the
GitHub Container Registry (ghcr.io).

> Not affiliated with, sponsored by, or endorsed by the Cilium project, the
> Envoy project, or the CNCF. See [NOTICE](./NOTICE).

## Why this exists

The Raspberry Pi kernel ships `CONFIG_ARM64_VA_BITS_39`, which is incompatible
with tcmalloc. Upstream documents the workaround of building Envoy with
`--define tcmalloc=gperftools`. These images bake that in for arm64 so you
don't have to compile it yourself.

## Images

Published to `ghcr.io/<owner>/cilium-envoy` (public — anonymous pulls work).

| Tag | Meaning |
| --- | --- |
| `<envoy>-arm64-rpi` | The Envoy build itself, e.g. `v1.35.9-arm64-rpi` |
| `cilium-<cilium>-arm64-rpi` | Alias for a Cilium release, e.g. `cilium-v1.19.0-arm64-rpi` |

Many Cilium releases share one Envoy version, so each Envoy build gets one
canonical tag plus a `cilium-*` alias per release that uses it.

## Usage (Cilium via Helm)

Run Envoy as a DaemonSet and point its image at the alias matching your
Cilium version:

```bash
helm upgrade cilium cilium/cilium \
    --namespace kube-system \
    --reuse-values \
    --set envoy.enabled=true \
    --set envoy.image.override=ghcr.io/<owner>/cilium-envoy:cilium-v1.19.0-arm64-rpi
```

## How it works

A scheduled GitHub Actions workflow reads the upstream version-compatibility
matrix, keeps the newest patch per Cilium minor, dedupes by Envoy version, and
builds only versions not already in GHCR. A new build is produced automatically
whenever the matrix changes.

- `.github/workflows/cilium-envoy-rpi.yml` — the pipeline
- `tools/parse_matrix.py` — matrix parser / work-list builder

## Build one locally

```bash
    git clone --branch v1.35 --depth 1 https://github.com/cilium/proxy.git
    cd proxy
    ARCH=arm64 \
    BAZEL_BUILD_OPTS="--define tcmalloc=gperftools --jobs=2" \
    DOCKER_BUILD_OPTS="--output=type=docker" \
    DOCKER_DEV_ACCOUNT=ghcr.io/<owner> \
    make docker-image-envoy
```

## License & attribution

This repository's pipeline code is licensed under Apache-2.0 (see [LICENSE](./LICENSE)).
The published images redistribute cilium/proxy and Envoy (Apache-2.0) and
gperftools (BSD-3-Clause); attribution is in [NOTICE](./NOTICE). No upstream source is
modified — only the gperftools build flag is changed.

## Trademarks

"Cilium" and "Envoy" are trademarks of their respective owners. These are
unofficial community builds for identification purposes only.
