# Alma Item Checks Webhook Service

Webhook service for WRLC's Alma Item Checks application.

It processes item updates from the Ex Libris Alma library management system, using a queue-based architecture to validate the webhook request, re-retrieve full item data by barcode (to verify active lifecycle status), and store the results for further processing by the Alma Item Checks Processing Service.

 ## Prerequisites

*   Python 3.12+
*   Azure Functions

## Configuration

### Environment Variables

The following environment variable must be set for the application to run:

*   `WEBHOOK_SECRET`: shared secret key sent with webhook request by Alma

The following application setting has a default value in `config.py` but can be overwritten with environment variable:

*   `FETCH_QUEUE_NAME`: [_default_: `fetch-queue`] name of the Azure Storage queue used to trigger item data retrieval

### Alma Integration Profile

To configure Alma to send webhook requests on item updates, create an integration profile:

* Integration Type: Webhooks
* Webhook Configuration:
  * Webhook listener URL: https://{`root-URL-for-deployed-webhook-service`}/webhook?institution={`inst-code-in-service-database`}
  * Secret: value set above for `WEBHOOK_SECRET`
* Subscriptions: Physical items

## License

This project is licensed under the MIT license. See the [LICENSE](LICENSE) file for details.

## Disclaimer

This application integrates with the [Alma library management system](https://exlibrisgroup.com/products/alma-library-services-platform/) but is not created by, affiliated with, or endorsed by [Ex Libris Group](https://exlibrisgroup.com/) or [Clarivate](https://clarivate.com/) in any way.
