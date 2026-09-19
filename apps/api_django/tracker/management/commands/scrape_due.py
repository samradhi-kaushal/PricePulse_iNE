from django.core.management.base import BaseCommand
from tracker.services.scrape_runner import run_scrape_due_batch


class Command(BaseCommand):
    help = "Find active tracked products due for scraping and execute batch scrape"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("SCRAPE RUN"))
        self.stdout.write(self.style.NOTICE("----------"))

        batch_res = run_scrape_due_batch(limit=50)

        self.stdout.write(f"Products due: {batch_res['due_count']}\n")

        for item in batch_res["results"]:
            pname = item["product_name"] or item["product_id"]
            if item["success"]:
                if item["attempts"] > 1:
                    msg = f"{pname} → SUCCESS after {item['attempts']} attempts"
                else:
                    msg = f"{pname} → SUCCESS"
                self.stdout.write(self.style.SUCCESS(msg))
            else:
                msg = f"{pname} → FAILED ({item['error']})"
                self.stdout.write(self.style.ERROR(msg))

        self.stdout.write("\nSummary:")
        self.stdout.write(self.style.SUCCESS(f"Successful: {batch_res['successful_count']}"))
        self.stdout.write(self.style.WARNING(f"Retried:    {batch_res['retried_count']}"))
        self.stdout.write(self.style.ERROR(f"Failed:     {batch_res['failed_count']}"))
