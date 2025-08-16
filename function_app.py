"""Azure Function for Alma Item Checks Webhook Service"""
import azure.functions as func

from alma_item_checks_webhook_service.blueprints.bp_webhook import bp as bp_webhook

app = func.FunctionApp()

app.register_blueprint(bp_webhook)
