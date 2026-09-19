from django.core.management.base import BaseCommand
from tracker.scraper.browser import scrape_product


class Command(BaseCommand):
    help = "Run Playwright scraper in headed mode for any product URL or ID"

    def add_arguments(self, parser):
        parser.add_argument("--product", type=str, required=True, help="Product URL or numeric ID (e.g. 1 or https://demo.inelabteamdev.com/product/1)")

    def handle(self, *args, **options):
        inp = options["product"]
        url = inp if inp.startswith("http") else f"https://demo.inelabteamdev.com/product/{inp}"

        self.stdout.write(self.style.NOTICE(f"Launching headed browser for '{url}'..."))

        res = scrape_product(url, headless=False)

        if res["success"]:
            self.stdout.write(self.style.SUCCESS("Scrape completed successfully!"))
            self.stdout.write(f"  Product Name: {res['product_name']}")
            self.stdout.write(f"  Price:        {res['currency']} {res['price']}")
            self.stdout.write(f"  Stock:        {res['stock']}")
            self.stdout.write(f"  Attempts:     {res['attempts']}")
        else:
            self.stdout.write(self.style.ERROR(f"Scrape failed after {res['attempts']} attempts:"))
            self.stdout.write(self.style.ERROR(f"  Error: {res['error']}"))
