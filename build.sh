#!/bin/bash
# Build script for Render - ejecutar migraciones de Flask
set -e

echo "==== Building Time Pro ===="
echo "Migrating database..."

cd src
flask db upgrade
cd ..

echo "==== Build completed successfully ===="
