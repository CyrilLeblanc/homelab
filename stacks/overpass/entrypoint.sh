#!/bin/bash
set -e

PBF_CACHE="/data/rhone-alpes-latest.osm.pbf"
BZ2_TARGET="/db/input.osm.bz2"
BZ2_TMP="/db/planet_tmp.osm.bz2"
GEOFABRIK_URL="https://download.geofabrik.de/europe/france/rhone-alpes-latest.osm.pbf"
MIN_PBF_SIZE=$((250*1024*1024))

# ---- Cleanup handler ----
cleanup() {
    local exit_code=$?
    if [ -f "$BZ2_TMP" ]; then
        echo "[entrypoint] Cleaning up temporary files..."
        rm -f "$BZ2_TMP"
    fi
    exit "$exit_code"
}
trap cleanup EXIT

# ---- Helper: validate PBF integrity with osmium ----
validate_pbf() {
    local file="$1"
    if [ ! -f "$file" ]; then
        return 1
    fi
    echo "[entrypoint] Validating PBF file integrity..."
    if osmium fileinfo "$file" > /dev/null 2>&1; then
        echo "[entrypoint] PBF integrity check passed."
        return 0
    else
        echo "[entrypoint] PBF integrity check FAILED."
        return 1
    fi
}

# ---- Step 1: obtain a valid PBF ----
echo "[entrypoint] Checking OSM PBF file..."

if validate_pbf "$PBF_CACHE"; then
    echo "[entrypoint] Using cached PBF file."
else
    echo "[entrypoint] Downloading PBF from Geofabrik..."
    rm -f "$PBF_CACHE"

    if ! wget -q --show-progress --tries=3 --timeout=30 -O "$PBF_CACHE" "$GEOFABRIK_URL"; then
        echo "[entrypoint] ERROR: download failed after 3 attempts."
        rm -f "$PBF_CACHE"
        exit 1
    fi

    # Verify minimum expected size
    actual_size=$(stat -c%s "$PBF_CACHE" 2>/dev/null || echo 0)
    if [ "$actual_size" -lt "$MIN_PBF_SIZE" ]; then
        echo "[entrypoint] ERROR: downloaded PBF is too small ($actual_size bytes, expected at least $MIN_PBF_SIZE)."
        rm -f "$PBF_CACHE"
        exit 1
    fi
    echo "[entrypoint] Download complete ($actual_size bytes)."

    if ! validate_pbf "$PBF_CACHE"; then
        echo "[entrypoint] ERROR: downloaded PBF is corrupted."
        rm -f "$PBF_CACHE"
        exit 1
    fi
fi

# ---- Step 2: convert PBF -> .osm.bz2 if needed ----
if [ ! -f /db/init_done ] && [ ! -f "$BZ2_TARGET" ]; then
    echo "[entrypoint] Converting PBF to BZ2 format..."
    if osmium cat "$PBF_CACHE" -o "$BZ2_TMP" --overwrite; then
        mv "$BZ2_TMP" "$BZ2_TARGET"
        echo "[entrypoint] Conversion complete."
    else
        echo "[entrypoint] ERROR: PBF to BZ2 conversion failed."
        rm -f "$BZ2_TMP"
        exit 1
    fi
else
    echo "[entrypoint] BZ2 file already present or init already done, skipping conversion."
fi

# ---- Step 3: ensure /db is world-traversable (for fcgiwrap/www-data) ----
if [ -d /db ] && [ "$(stat -c '%a' /db)" = "700" ]; then
    echo "[entrypoint] Fixing /db permissions to 755..."
    chmod 755 /db
fi

# ---- Step 4: hand off to the official entrypoint ----
echo "[entrypoint] Starting Overpass..."
exec /app/docker-entrypoint.sh
