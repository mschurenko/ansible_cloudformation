#!/usr/bin/env bash

# setup ansible working directory for a cloudformation project

if [[ $# -ne 1 ]];then
  echo "usage: $0 <target directory>"
  exit 1
fi

target_dir=$1

if ! [[ -d $target_dir ]];then
  echo "ERROR: $target_dir does not exist"
  exit 2
fi

mkdir ${target_dir}/{includes,jinja_templates,rendered_templates}

cp skel/stack.yml ${target_dir}/includes/
cp skel/example.yml ${target_dir}/
