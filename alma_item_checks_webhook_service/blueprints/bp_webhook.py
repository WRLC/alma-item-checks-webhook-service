"""Process webhook from Alma on item update."""
import azure.functions as func

from alma_item_checks_webhook_service.services.webhook_service import WebhookService

bp = func.Blueprint()


@bp.function_name('item_webhook')
@bp.route('scfwebhook', methods=['GET', 'POST'], auth_level='anonymous')
def item_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """Process webhook from Alma on item update.

    Args:
        req (func.HttpRequest): The incoming HTTP request.

    Returns:
        func.HttpResponse: The HTTP response.
    """
    webhook_service: WebhookService = WebhookService(req)  # initialize WebhookService
    response: func.HttpResponse = webhook_service.parse_webhook()  # parse webhook

    return response
