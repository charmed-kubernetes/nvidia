#!/bin/bash -eu

MISSING=
command -v helm &>/dev/null || MISSING+="helm "
if [ -n "${MISSING}" ]; then
  echo "ERROR: missing requirement: ${MISSING}"
  exit 1
fi

BASE_DIR=$(dirname ${BASH_SOURCE[0]})
CHART_DIR=${BASE_DIR}/charts
CHART_NAME=network-operator
CHART_REPO=https://mellanox.github.io/network-operator
CHART_VER=${1:-23.1.0}
MANIFEST_DIR=${BASE_DIR}/${CHART_NAME}
MANIFEST_VER=v${CHART_VER//v}
TEMPLATE_PATH=${MANIFEST_DIR}/manifests/${MANIFEST_VER}/manifest.yaml
TEMPLATE_RELEASE=nvidia-charm

# Store the chart in case we need to re-template it locally
mkdir -p ${CHART_DIR}
helm pull ${CHART_NAME} \
  --destination ${CHART_DIR} \
  --repo ${CHART_REPO} \
  --version ${CHART_VER}

# Create the template with juju-isms
mkdir -p $(dirname -- ${TEMPLATE_PATH})
echo ${MANIFEST_VER} > ${MANIFEST_DIR}/version
helm template ${TEMPLATE_RELEASE} ${CHART_DIR}/${CHART_NAME}-${CHART_VER}.tgz \
  --include-crds \
  > ${TEMPLATE_PATH}

# We've tainted the chart; drop helm-isms to avoid confusion
sed -i \
  -e '\|helm.sh/chart:|d' \
  -e '\|managed-by: Helm|d' \
  -e '\|app.kubernetes.io/instance:|d' \
  ${TEMPLATE_PATH}
