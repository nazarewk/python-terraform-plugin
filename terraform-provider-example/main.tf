terraform {
  required_version = ">= 0.12"
}

data "example_example" "qwe" {
  input = "example-input2"
}

output "data-source" {
  value = data.example_example.qwe
}

resource "example_example" "asd" {
  input = data.example_example.qwe.output
}

output "resource" {
  value = example_example.asd
}
