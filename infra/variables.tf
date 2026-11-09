variable "subscription_id" {
  type        = string
  description = "ID da assinatura Azure (az account show --query id -o tsv)"
}

variable "location" {
  type        = string
  default     = "brazilsouth"
  description = "Região. Se a sua assinatura de estudante bloquear, tente eastus2 ou eastus."
}

variable "vm_size" {
  type        = string
  default     = "Standard_B2s"
  description = "Tamanho da VM. Se der erro de SKU/quota, tente Standard_B2ats_v2, Standard_B2s_v2 ou Standard_B1ms."
}

variable "admin_username" {
  type    = string
  default = "azureuser"
}

variable "admin_ssh_public_key" {
  type        = string
  description = "Conteúdo da chave PÚBLICA SSH (arquivo .pub)"
}

variable "admin_cidr" {
  type        = string
  description = "Seu IP público no formato x.x.x.x/32. É o ÚNICO que acessa a porta 22 (SSH)."

  validation {
    condition     = !contains(["0.0.0.0/0", "*", "Internet", "::/0"], var.admin_cidr)
    error_message = "A porta administrativa (SSH) nunca pode ficar aberta para a internet toda."
  }
}

variable "app_image" {
  type        = string
  description = "Imagem do GHCR, em minúsculas. Ex.: ghcr.io/meuusuario/bairrovivo:latest"
}

variable "repo_url" {
  type        = string
  description = "URL HTTPS do repositório público. Ex.: https://github.com/meuusuario/bairrovivo.git"
}

variable "postgres_password" {
  type        = string
  sensitive   = true
  description = "Senha do Postgres (só letras e números)"
}

variable "metrics_token" {
  type        = string
  sensitive   = true
  description = "Token que protege /metrics (o mesmo vai no Prometheus e no GitHub Secret METRICS_TOKEN)"
}

variable "demo_mode" {
  type        = string
  default     = "1"
  description = "1 habilita /api/demo/erro (para demonstrar o alerta). Volte para 0 depois da avaliação."
}
