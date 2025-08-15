"""Azure Function for Alma Item Checks Webhook Service"""
import azure.functions as func

from alma_item_checks_webhook_service.blueprints.bp_webhook import bp as bp_webhook
from alma_item_checks_webhook_service.blueprints.bp_retrieve_item_data import bp as bp_retrieve_item_data

app = func.FunctionApp()

app.register_blueprint(bp_webhook)
app.register_blueprint(bp_retrieve_item_data)
