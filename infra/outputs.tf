output "public_ip" {
  value       = azurerm_public_ip.pip.ip_address
  description = "IP público da VM"
}

output "app_url" {
  value       = "http://${azurerm_public_ip.pip.ip_address}"
  description = "URL pública do MVP (use no PDF e na variável APP_URL do GitHub)"
}

output "ssh" {
  value = "ssh ${var.admin_username}@${azurerm_public_ip.pip.ip_address}"
}
