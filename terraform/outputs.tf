output "function_app_name" {
  description = "The name of the main Function App."
  value       = azurerm_linux_function_app.function_app.name
}

output "python_version" {
  description = "The Python version installed in the function app."
  value       = azurerm_linux_function_app.function_app.site_config[0].application_stack[0].python_version
}
