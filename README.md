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

## 📄 `Prerequisites`

This repository needs a few values stored in `AWS SSM Parameter Store` to function properly.

### Generate an API token for Proxmox.

1. Login to Proxmox UI.
2. Navigate to `Datacentre` -> `Permissions` -> `API Tokens` -> `Add`.
3. Create a new token with the name `proxmox-api-token`; Ensure `Privilage Separation`, if using the `root@pam` user.
4. Copy the token value.
5. Run the following, replacing `<token>` with the token value you've copied:

```bash
aws ssm put-parameter --name /homelab/proxmox/api-token --type SecureString --overwrite --value <token>
```

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

### Setting up `k3s`:

* Add IP addresses to known_hosts.


* https://github.com/k2s-io/k3s-ansible
* https://github.com/adelinofaria/homelab-iac-ansible/tree/main/roles/proxmox_kvm

## 📖 `References`

Check out [`./docs/references.md`](./docs/references.md) for the list of references I've used to create and setup this repository - there's a lot.

## 🪪 `License`

This work is published under the MIT license.

Please see the [`LICENSE`](./LICENSE) file for details.



