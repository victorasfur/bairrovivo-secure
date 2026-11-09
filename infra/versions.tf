terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
  # O state NÃO fica no repositório (.gitignore). Local por padrão; para o time inteiro,
  # use um backend remoto (Storage Account) - ver README.
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}
