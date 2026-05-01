variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "ap-southeast-2"
}

variable "instance_name" {
  description = "Name tag for the EC2 instance (also used as SSM parameter prefix)."
  type        = string
  default     = "jmpa-ec2-1"
}

variable "instance_type" {
  description = "EC2 instance type. t3.small is a good starting point (2 vCPU, 2GB RAM)."
  type        = string
  default     = "t3.small"
}

variable "root_volume_size_gb" {
  description = "Root EBS volume size in GB."
  type        = number
  default     = 20
}

variable "key_name" {
  description = "Name of the EC2 key pair to create (uses the SSH public key from SSM)."
  type        = string
  default     = "homelab"
}

variable "vpc_id" {
  description = "VPC ID to launch the instance into. Defaults to the default VPC if empty."
  type        = string
  default     = ""
}

variable "subnet_id" {
  description = "Subnet ID to launch the instance into. Must be a public subnet for the Elastic IP to work."
  type        = string
  default     = ""
}

variable "environment" {
  description = "Environment tag value."
  type        = string
  default     = "homelab"
}
