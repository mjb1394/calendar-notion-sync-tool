import argparse
import logging

from notion_calendar_sync.clients.notion_client import NotionClient
from notion_calendar_sync.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def list_all_databases(client: NotionClient):
    """Lists all accessible databases."""
    logger.info("Fetching all accessible databases...")
    databases = client.list_databases()
    if not databases:
        logger.info("No databases found or accessible by the integration.")
        return

    print("\n--- Accessible Notion Databases ---")
    for db in databases:
        db_id = db.get("id")
        title_list = db.get("title", [])
        title = "".join([t.get("plain_text", "") for t in title_list]) if title_list else "Untitled"
        print(f"  - Name: {title}")
        print(f"    ID:   {db_id}\n")
    print("---------------------------------")


def list_all_pages(client: NotionClient, database_id: str):
    """Lists all pages in a given database."""
    logger.info(f"Fetching all pages from database: {database_id}...")

    # First, verify the database exists and get its title
    db_info = client.get_database(database_id)
    if not db_info:
        logger.error(f"Could not retrieve database with ID: {database_id}. Please check the ID and permissions.")
        return

    db_title_list = db_info.get("title", [])
    db_title = "".join([t.get("plain_text", "") for t in db_title_list]) if db_title_list else "Untitled"

    pages = client.query_database(database_id)
    if not pages:
        logger.info(f"No pages found in the database '{db_title}'.")
        return

    print(f"\n--- Pages in '{db_title}' (ID: {database_id}) ---")
    for page in pages:
        page_id = page.get("id")
        properties = page.get("properties", {})

        # Find the title property (its name can vary)
        title_prop_name = next((name for name, prop in properties.items() if prop.get("type") == "title"), None)
        title = "Untitled"
        if title_prop_name and properties[title_prop_name].get("title"):
            title_list = properties[title_prop_name].get("title", [])
            title = "".join([t.get("plain_text", "") for t in title_list]) if title_list else "Untitled"

        print(f"  - Title: {title}")
        print(f"    ID:    {page_id}\n")
    print("-------------------------------------------")


def main():
    """Main function to run the Notion query tool."""
    parser = argparse.ArgumentParser(description="A tool to query Notion databases and pages.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--list-databases",
        action="store_true",
        help="List all databases accessible by the integration."
    )
    group.add_argument(
        "--list-pages",
        type=str,
        metavar="DATABASE_ID",
        help="List all pages within a specific database ID."
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level."
    )

    args = parser.parse_args()

    # Set logging level from args
    logging.getLogger().setLevel(args.log_level)

    # Check for Notion token
    if not settings.notion_token:
        logger.error("NOTION_TOKEN is not set. Please set it in your environment or .env file.")
        return

    client = NotionClient()

    if args.list_databases:
        list_all_databases(client)
    elif args.list_pages:
        list_all_pages(client, args.list_pages)


if __name__ == "__main__":
    main()
