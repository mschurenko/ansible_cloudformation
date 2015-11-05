#!/usr/bin/env bash

# override base_dir by setting $BASE_DIR env variable
base_dir=${BASE_DIR:-/usr/local/ansible_cloudformation}

function create_config() {
cat << EOF > ~/.ansible.cfg
[defaults]
transport = local
gathering = explicit
host_key_checking = False
retry_files_enabled = False
inventory = ${base_dir}/hosts
filter_plugins = ${base_dir}/filter_plugins
lookup_plugins = ${base_dir}/lookup_plugins
library = ${base_dir}/library
EOF
}

if [[ $1 == '-f' ]];then
  force=1
else
  force=0
fi

echo "Installing ansible and deps using pip..."
pip install -r requirements.txt

echo "Installing filters/lookups under ${base_dir} ..."
mkdir $base_dir 2>/dev/null
echo 'localhost' > ${base_dir}/hosts
cp -r library $base_dir
cp -r filter_plugins $base_dir
cp -r lookup_plugins $base_dir
cp -r custom_utils $base_dir

echo "Creating ~/.ansible.cfg ..."
if ! [[ -f ~/.ansible.cfg ]];then
  create_config
else
  if [[ $force == 1 ]];then
    echo "Moving ~/.ansible.cfg to ~/.ansible.cfg.orig.$$"
    mv ~/.ansible.cfg{,.orig.$$}
    create_config  
  else
    echo "Warning: ~/.ansible.cfg already exists. not going to overwrite it unless -f flag is set."
  fi
fi
