terraform {
  required_version = ">= 0.12"
}

data "example_example" "qwe" {}

output "string" {
  value = data.example_example.qwe
}