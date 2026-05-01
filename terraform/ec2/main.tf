# Provision a Debian EC2 instance as a homelab fleet member.
#
# What this creates:
#   - 1x EC2 instance (t3.small by default) running Debian 12
#   - Security group with SSH (your IP only), HTTP, HTTPS ingress
#   - Elastic IP so the public IP is stable across reboots
#   - Stores the public IP and instance ID in AWS SSM Parameter Store
#     so the Ansible inventory can discover it automatically
#
# After running `terraform apply`:
#   1. Uncomment the EC2 block in inventory/main.py
#   2. Run `make configure-ec2`

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Store state in S3 — reuse the same bucket you likely already have for SSM/CDK.
  # Uncomment and fill in your bucket name:
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "homelab/ec2/terraform.tfstate"
  #   region = "ap-southeast-2"
  # }
}

provider "aws" {
  region = var.aws_region
}

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

# Latest Debian 12 (Bookworm) official AMI.
data "aws_ami" "debian_12" {
  most_recent = true
  owners      = ["136693071363"] # Official Debian account

  filter {
    name   = "name"
    values = ["debian-12-amd64-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Your current public IP — used to restrict SSH ingress.
data "http" "my_public_ip" {
  url = "https://checkip.amazonaws.com"
}

data "aws_ssm_parameter" "ssh_public_key" {
  name            = "/homelab/ssh/public-key"
  with_decryption = false
}

# ---------------------------------------------------------------------------
# Key pair — uses the same SSH public key stored in SSM
# ---------------------------------------------------------------------------

resource "aws_key_pair" "homelab" {
  key_name   = var.key_name
  public_key = data.aws_ssm_parameter.ssh_public_key.value

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# Security group
# ---------------------------------------------------------------------------

resource "aws_security_group" "ec2" {
  name        = "${var.instance_name}-sg"
  description = "Homelab EC2 fleet member security group"
  vpc_id      = var.vpc_id

  # SSH — your IP only.
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${trimspace(data.http.my_public_ip.response_body)}/32"]
    description = "SSH from your current IP"
  }

  # HTTP.
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }

  # HTTPS.
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS"
  }

  # All outbound traffic allowed.
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound"
  }

  tags = merge(local.common_tags, {
    Name = "${var.instance_name}-sg"
  })
}

# ---------------------------------------------------------------------------
# EC2 instance
# ---------------------------------------------------------------------------

resource "aws_instance" "ec2" {
  ami                    = data.aws_ami.debian_12.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.homelab.key_name
  vpc_security_group_ids = [aws_security_group.ec2.id]
  subnet_id              = var.subnet_id

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size_gb
    delete_on_termination = true
    encrypted             = true
  }

  # IMDSv2 only — required for security best practice.
  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    http_endpoint               = "enabled"
  }

  tags = merge(local.common_tags, {
    Name = var.instance_name
  })

  lifecycle {
    # Prevent accidental destruction — must explicitly set this to false to destroy.
    prevent_destroy = true
  }
}

# Elastic IP — keeps the public IP stable across stop/start cycles.
resource "aws_eip" "ec2" {
  instance = aws_instance.ec2.id
  domain   = "vpc"

  tags = merge(local.common_tags, {
    Name = "${var.instance_name}-eip"
  })

  # EIP must be released before the instance is destroyed.
  depends_on = [aws_instance.ec2]
}

# ---------------------------------------------------------------------------
# SSM parameters — Ansible inventory reads these to discover the instance
# ---------------------------------------------------------------------------

resource "aws_ssm_parameter" "public_ip" {
  name  = "/homelab/ec2/${var.instance_name}/public-ip"
  type  = "String"
  value = aws_eip.ec2.public_ip

  tags = local.common_tags
}

resource "aws_ssm_parameter" "instance_id" {
  name  = "/homelab/ec2/${var.instance_name}/instance-id"
  type  = "String"
  value = aws_instance.ec2.id

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# Locals
# ---------------------------------------------------------------------------

locals {
  common_tags = {
    Project     = "homelab"
    ManagedBy   = "terraform"
    Environment = var.environment
  }
}
