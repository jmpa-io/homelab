output "public_ip" {
  description = "Elastic IP address of the EC2 instance."
  value       = aws_eip.ec2.public_ip
}

output "instance_id" {
  description = "EC2 instance ID."
  value       = aws_instance.ec2.id
}

output "ami_id" {
  description = "Debian 12 AMI used."
  value       = data.aws_ami.debian_12.id
}

output "ssm_public_ip_path" {
  description = "SSM parameter path where the public IP is stored."
  value       = aws_ssm_parameter.public_ip.name
}

output "next_steps" {
  description = "What to do after apply."
  value       = <<-EOT
    EC2 instance provisioned.

    Next steps:
      1. Uncomment the EC2 block in inventory/main.py
      2. Run: make configure-ec2
      3. Verify Tailscale: ssh admin@${aws_eip.ec2.public_ip} tailscale status
  EOT
}
