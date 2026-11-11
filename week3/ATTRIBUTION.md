# Data source and attribution

Data source: **StatsBomb Open Data**, distributed in the [Hudl open-data repository](https://github.com/hudl/open-data).

This project downloads the specific Git revision recorded in `data/snapshot.json`; it does not use a moving default branch. Source URLs and SHA-256 checksums for every selected event file are in `data/source_manifest.json`.

The source [README at the pinned revision](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/README.md) requests StatsBomb credit and its logo when research, analysis or insights are published, shared or distributed. Official logo assets are linked from that README's Media Pack. Consult the source terms before redistribution; this project does not relicense StatsBomb data.

Raw events are downloaded into an ignored local cache. Committed compact metadata, shot-derived features, predictions and metrics are for the student's AI research project. They are not official StatsBomb xG estimates. `xg` is the student's fitted distance/angle baseline probability.
