resource "random_string" "db_name_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "azurerm_mysql_flexible_database" "database" {
  name                = "${var.project_name}${random_string.db_name_suffix.result}"
  resource_group_name = var.mysql_resource_group_name
  server_name         = var.mysql_server_name
  charset             = "utf8mb4"
  collation           = "utf8mb4_unicode_ci"
}

resource "random_password" "mysql_user_password" {
  length  = 16
  special = false
}

resource "mysql_user" "user" {
  user               = var.mysql_user_username
  host               = "%"
  plaintext_password = random_password.mysql_user_password.result
}

resource "mysql_grant" "user_grant" {
  user     = mysql_user.user.user
  host     = mysql_user.user.host
  database = azurerm_mysql_flexible_database.database.name
  privileges = ["ALL PRIVILEGES"]
}

# Stage Database
resource "random_string" "stage_db_name_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "azurerm_mysql_flexible_database" "stage_database" {
  name                = "${var.project_name}-stage-${random_string.stage_db_name_suffix.result}"
  resource_group_name = var.mysql_resource_group_name
  server_name         = var.mysql_server_name
  charset             = "utf8mb4"
  collation           = "utf8mb4_unicode_ci"
}

resource "random_password" "stage_mysql_user_password" {
  length  = 16
  special = false
}

resource "mysql_user" "stage_user" {
  user               = "${var.mysql_user_username}-stage"
  host               = "%"
  plaintext_password = random_password.stage_mysql_user_password.result
}

resource "mysql_grant" "stage_user_grant" {
  user     = mysql_user.stage_user.user
  host     = mysql_user.stage_user.host
  database = azurerm_mysql_flexible_database.stage_database.name
  privileges = ["ALL PRIVILEGES"]
}
