# ansible_cloudformation
Some Ansible modules and plugins that make CloudFormation easier to work with.

Inspired by http://www.unixdaemon.net/cloud/ansible-expand-cloudformation-templates.html

Setup
=====

Clone this repo into what will be your Ansible working directory:
```sh
git clone https://github.com/mschurenko/ansible_cloudformation.git && cd ansible_cloudformation
```

Run:
```sh
pip install -r requirements.txt 
```

This will install Ansible, boto and a couple other python dependencies. It you are installing Ansible a different way then maybe exclude that from the requirements.txt or cherry pick the modules that you need from it.

<b>Note:</b> I don't know if Ansible 2.x will work with any of this. There's a great chance it won't. It is advisable to just stick with the latest stable version of 1.9.x. (If you install Ansible via the requirements.txt file then you don't have to worry about this.)

You will need to have some AWS access keys with suitable permisions. I export my AWS access keys via the following environment variables:

```sh
AWS_ACCESS_KEY_ID=<my_access_ke>
AWS_SECRET_ACCESS_KEY=<my_secret_key>
```

Under the hood it's all boto so any way you mange your keys for boto should work here too.

Usage
=====

Create/run your Ansible playbooks from this directory. Example:
```sh
ansible-playbook playbook-example.yml
```

cloudformation module
=====================

This is a fork of the core Ansible module "cloudformation" http://docs.ansible.com/ansible/cloudformation_module.html

##### Why fork this?

The cloudformation module that's included with Ansible contains two states: present or absent. Having a single state that can both create and update a stack proved to be dangerous. It felt like carrying around a loaded hand gun with the safety off. On more than one occassion I copied an existing playbook, forgot to change the stack_name paramter and then ran the playbook. You might be able to guess what happened: all the resources in my original stack were deleted and replaced by the resources in what was supposed to be my new stack. Sure I could have been more careful or could have used an empty skeleton template to always start out with, but that doesn't change the fact that this is still very precarious. "<i>Sorry guys. I just blew away our entire production VPC.</i>"

The following states are supported by this fork:

 <b>create</b>

This will invoke the create_stack CloudFormation API call. If a stack with the same name already exists it will return an OK/unchanged response to Ansible. 

<b>update</b>

This will invoke the update_stack CloudFormation API call. update can only be applied against an existing stack.
It is not advisable to set update in a playbook file as this can be a dangerous operation. Instead it is best to do this with ansible-playbook by using the '-e' flag.

An example of setting state to update with ansible-playbook:

```sh
ansible-playbook my-playbook.yml -e stack_state=update
```

<b>pass</b>

Setting stack_state to pass will simply return Ok/unchanged and exit immediately. This is useful if one wants to create or update a CloudFormation template without actually passing it to the API.

<b>delete</b>

This will delete an existing stack.

<b>compare</b>

Unfortunately CloudFormation doesn't provide a dry-run. I suppose one is supposed to cross their fingers and hope for the best? compare is like a poor man's dry-run. This is useful to compare what the changes would be between the current stack and a newer template. It is advisable to run this before making any stack updates. This will output a vimdiff command which can then be copied and pasted into a terminal.

For example:

```sh
$ ansible-playbook my-playbook.yml -e stack_state=compare -v
...

TASK: [Mangage CloudFormation Stack] ******************************************
ok: [localhost] => {"changed": false, "output": {"Run the following command to compare current template with new one": "vimdiff -o /tmp/mystack_new.json /tmp/mystack_current.json"}}

```

This is certainly not perfect but a lot better than nothing. When combined with a stack policy that prevents accidentally deleting or replacing resources it's actually quite effective. 

##### Playbook example

```yaml
hosts: localhost

tasks:
  - name: Mangage CloudFormation Stack
    cloudformation:
      state: "{{ stack_state | default('create') }}"
      stack_name: my-stack
      template: my-stack-tempmlate.yml
```

Notice that state is being set with the variable "stack_state" rather than hard coding it in the playbook. This opens up the option of overriding the default by using the '-e' option to ansible-playbook. (Examples of running ansible-playbook can be found above. Take a look at playbook-example.yml for an example playbook.)

##### Added Features:
- automatically create an s3 bucket and upload template to bucket if size is >= 50 KB (an existing s3 bucket can also be used)
- added additonal validation for proper stack names
- added support for in-line stack polices
- added support for .yml or .yaml files which are converted to JSON

Lookups
=======
<b>cf_resource</b>

This can be used to obtain a physical ID from a logical ID in an existing Cloudformation stack.

For example:
```yaml
ec2:
 subnets: "{{ lookup('cf_resource', 'ProdWeb/Subnet1/Subnet2/Subnet3').split(',') }}"
```

Will return a comma delimited string containing the subnet IDs from a CloudFormation stack called ProdWeb. The split method is being used in order to pass an array to the ec2.subnets variable.

<b>cf_output</b>

This works the same way as cf_resource except it references keys in stack outputs rather than logical IDs.

<b>get_azs</b>

This lookup will return a comma delimited list of availability zones given an AWS region. The region can either be set in the AWS_REGION environment variable or can be given as an agrument. For example:

```yaml
us_west_2:
  azs: "{{ lookup('get_azs').split(',') }}"
```

For more info on lookups see: http://docs.ansible.com/ansible/playbooks_lookups.html

Filters
=======
<b>eip_allocid</b>

When applied to an EIP, will give back the corresponding allocation ID. This can be useful when using the AWS::EC2::EIPAssociation resource type as it requires an allocation ID and not an EIP. For example:

```yaml
Type: AWS::EC2::EIPAssociation
  Properties:
    AllocationId: {{ ec2.eips['_' ~ num][n] | eip_allocid }}
```

For more info on filters see: http://docs.ansible.com/ansible/playbooks_filters.html

General Approach
================
- While CloudFormation parameters and outputs are fully supported I don't find myself using them. Instead I store variables in seperate .yml files which get included in playbooks and interpolated by the jinja2 template engine. Jinja2 is a core component of Ansible. For more information on Jinja2 see http://jinja.pocoo.org/docs/dev/

- I write templates in YAML as it is way less annoying then trying to using Jinja2 on top of JSON; howerver writing them in JSON is completely fine too. 

- Intrinsic fucntions like Ref and Fn::GetAtt are necessary. Ones like Fn::Join, Fn::Select, etc are probably not. Jinja2 is far batter at logic than CloudFormation so I stick with that. 

- I keep User Data in a seperate template which can be included into multiple templates (See http://jinja.pocoo.org/docs/dev/templates/#include). There is also no need for doing complex escaping. No one should ever have to write something like this:
```json
"UserData": { "Fn::Base64": { "Fn::Join": [ "", [
  "#!/bin/bash -e\n",
  "wget https://opscode-omnibus-packages.s3.amazonaws.com/ubuntu/12.04/x86_64/chef_11.6.2-1.ubuntu.12.04_amd64.deb\n",
 "dpkg -i chef_11.6.2-1.ubuntu.12.04_amd64.deb\n"
 ] ] } }
}
```
