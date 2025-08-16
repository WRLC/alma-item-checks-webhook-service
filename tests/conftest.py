"""Test configurations"""
import os

os.environ["AzureWebJobsStorage"] = (
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey"
    "=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http"
    "://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
)
os.environ["SQLALCHEMY_CONNECTION_STRING"] = "sqlite:///:memory:"
os.environ["WEBHOOK_SECRET"] = "test_webhook_secret"
