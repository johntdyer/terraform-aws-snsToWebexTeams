#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
set -o xtrace

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

outdir="${__dir}/module/lambda"
zipname="sns-to-webex-teams.zip"

pushd sns-to-webex-teams

# rm -rf "${outdir}/${zipname}"
# zip -r9 "${outdir}/${zipname}" ./packages/
# zip -u "${outdir}/${zipname}" lambda_function.py

# pushd $VIRTUAL_ENV/lib/python2.7/site-packages
pushd package


zip -FSr -r "${outdir}/${zipname}" .   --exclude pip\* \
  --exclude setuptools\* \
  --exclude virtualenv\*
popd
zip -u "${outdir}/${zipname}" lambda_function.py

# zip -uFSr -r "${outdir}/${zipname}" . \
#   --exclude pip\* \
#   --exclude setuptools\* \
#   --exclude virtualenv\*

# popd

popd
