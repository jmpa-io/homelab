<!-- markdownlint-disable MD041 MD010 -->
<p align="center">
    <img src="docs/logo.png" width="80%">
</p>

# `homelab`

```diff
+ 🏠 A collection of "things" that manage my homelab.

! PLEASE NOTE:
! This repository is a work-in-progress. Use at your own risk!
```

<a href="LICENSE" target="_blank"><img src="https://img.shields.io/github/license/jmpa-io/homelab.svg" alt="GitHub License"></a>
[![CI/CD](https://github.com/jmpa-io/homelab/actions/workflows/cicd.yml/badge.svg)](https://github.com/jmpa-io/homelab/actions/workflows/cicd.yml)
[![Codecov](https://codecov.io/github/jmpa-io/homelab/graph/badge.svg)](https://codecov.io/github/jmpa-io/homelab)

<table>
<tr>
<td>

<details open="open">

<summary>🤔 <b>Why set up this homelab?</b></summary><br/>

After moving to the other side of the world, I found myself in a job market where higher-level roles require different skills than I’m used to. To adapt to this change, I've created this homelab setup to expand my knowledge from the cloud to on-prem.

I'm primarly a DevOps Engineer who has been focused on the cloud, but this setup gives me the option to easily run my own services, written in various languages, that I'd like to try out.

This is my first time setting up a homelab, so any feedback would be greatly appreciated!

</details>

</td>
</tr>
</table>

## 🖼️ `Architecture`

<details open="open">
<summary>✋🏼 <b>Click here to hide.</b></summary>

<br/>

<p align="centre">
    <img src="docs/architecture.png">
</p>

</details>

## 🏗️ `Getting started`

To get started with this repository, you need a Proxmox host. If you're unsure how to do this, click [here](./docs/proxmox/README.md).

This setup uses `3` Proxmox hosts, as of writing, which is dynamically configured in the [`inventory/main.py`](./inventory/main.py). You would need to configure this file to match the number of servers you're running. See the [`inventory/README.md`](./inventory/README.md) for more information.

This repository also uses Ansible - you can see a collection of custom roles under [`./roles/`](./roles/) that are used in both the [`./proxmox-hosts/`](./proxmox-hosts/) & [`./proxmox-services/`](./proxmox-services/) directories.

Once this all makes sense, and you've configured the [`inventory/main.py`](./inventory/main.py) for your needs, using a terminal, you can run:

```bash
make run-playbook
```

And this repository should do the rest.

```bash
# You can also run:
make
# or
make help
# To see a list of available commands in this repository.
```


## 📖 `References`

Below are a few references I've used to help me on this homelab journey:

<details>
<summary><b>👇🏼 Click here to show, since it's quite long.</b></summary>

<br/>

**General:**
* https://community-scripts.github.io/ProxmoxVE/
* https://www.toptechskills.com/ansible-tutorials-courses/speed-up-ansible-playbooks-pipelining-mitogen
* https://www.reddit.com/r/homelab/comments/13u66yn/automating_your_homelab_with_proxmox_cloudinit
* https://github.com/rishavnandi/ansible_homelab
* https://github.com/marcwrobel/setup
* https://www.youtube.com/watch?v=dvyeoDBUtsU
* https://www.reddit.com/r/selfhosted/comments/1gow9jb/launched_my_side_project_on_a_selfhosted_m1_mac

**Diagrams:**
* https://www.reddit.com/r/selfhosted/comments/1gr0k5r/my_home_server_dashboard
* https://www.reddit.com/r/selfhosted/comments/1bd0reo/how_my_i_dont_want_to_pay_microsoft_a_dime_for
* https://www.reddit.com/r/selfhosted/comments/1gd9pb0/my_home_lab_its_a_mess_but_im_very_proud_of_it
* https://www.reddit.com/r/selfhosted/comments/1gjli4h/finally_had_the_balls_to_wipe_windows_and_self
* https://www.reddit.com/r/dns/comments/rbkz94/how_can_setup_or_the_graph_can_be_improved
* https://www.reddit.com/r/selfhosted/comments/1i74my7/sharing_my_network_configuration
* https://www.reddit.com/r/selfhosted/comments/1imobmz/am_i_relying_too_much_on_tailscale
* https://www.reddit.com/r/selfhosted/comments/1g03ap2/ever_expanding_homelab_update
* https://www.reddit.com/r/selfhosted/comments/1gdsosc/tired_of_cloud_service_price_hikes_shout_out_this
* https://www.reddit.com/r/selfhosted/comments/1f2ojf9/i_tried_with_a_diagram
* https://www.reddit.com/r/selfhosted/comments/1gjli4h/finally_had_the_balls_to_wipe_windows_and_self
* https://www.reddit.com/r/selfhosted/comments/11lgtk8/my_fully_selfhosted_server
* https://www.reddit.com/r/selfhosted/comments/n4tdgp/finally_got_a_landing_page_built_for_my_little

**Dashboards:**
* https://www.reddit.com/r/selfhosted/comments/18xgcsu/my_dashboard_now_with_descriptions
* https://www.reddit.com/r/selfhosted/comments/nhlzww/my_dashboard_2021_edition_i_love_self_hosting
* https://www.reddit.com/r/selfhosted/comments/1gfq437/my_basic_homepage
* https://www.reddit.com/r/selfhosted/comments/10wyzxh/40_containers_counting
* https://www.reddit.com/r/selfhosted/comments/elcxiv/to_all_the_2020_posts_about_what_services_we_run
* https://www.reddit.com/r/selfhosted/comments/15ssm6o/my_selfhosted_journey_so_far_dashboard
* https://www.reddit.com/r/selfhosted/comments/119l044/final_version_of_my_unbound_dashboard/
* https://www.reddit.com/r/selfhosted/comments/1b2tmj3/my_simple_dashboard
* https://www.reddit.com/r/selfhosted/comments/gsetnd/this_is_my_current_homer_dashboard
* https://www.reddit.com/r/selfhosted/comments/mftm74/6_mo_ago_i_googled_nas_for_the_first_time_today

**Networking:**
* https://wiki.debian.org/BridgeNetworkConnections#Bridging_with_a_wireless_NIC
* https://github.com/joshrnoll/tailscale-info

**Ansible:**
* https://github.com/olivomarco/my-ansible-linux-setup
* https://github.com/debops/debops
* https://github.com/joshrnoll/ansible-playbook-homelab

**Proxmox:**
* https://forum.proxmox.com/threads/containers-loose-network-until-reboot-of-the-lxc.153588/

</details>

## 🪪 `License`

This work is published under the MIT license.

Please see the [`LICENSE`](./LICENSE) file for details.


# `TODO`

### Setting up k3s:

* Add IP addresses to known_hosts.


* https://github.com/k3s-io/k3s-ansible
* https://github.com/adelinofaria/homelab-iac-ansible/tree/main/roles/proxmox_kvm


### Setting up `Debian` template:

* https://gist.github.com/si458/98aa940837784e9ef9bff9e24a7a8bfd
* https://github.com/maxfield-allison/scripts/blob/main/proxmox-template-create.sh
* https://static.xtremeownage.com/blog/2024/proxmox---debian-cloud-init-templates/#options-tab
* https://gist.github.com/casperghst42/9f03f331d357f6bcda5285afdec87007
* https://docs.ansible.com/ansible/latest/collections/community/general/proxmox_kvm_module.html
* https://github.com/DavidPesticcio/selfhosted/blob/c58f626ecf40276ce71023ee3b553181acfc50b7/roles/proxmox_hypervisor/tasks/pve_kvm_template.yml

