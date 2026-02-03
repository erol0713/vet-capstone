from django.core.management.base import BaseCommand
from django.db import models

from dogs.models import Dog


class Command(BaseCommand):
    help = 'Normalize intake dog statuses so they appear in the Dog Pound list.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--include-undated',
            action='store_true',
            help='Also update ownerless dogs without capture/surrender dates.',
        )

    def handle(self, *args, **options):
        include_undated = options['include_undated']
        base_filter = models.Q(owner__isnull=True) & ~models.Q(
            status__in=[Dog.Status.IMPOUNDED, Dog.Status.AVAILABLE]
        )
        dated_filter = models.Q(capture_datetime__isnull=False) | models.Q(
            surrender_datetime__isnull=False
        )
        if include_undated:
            queryset = Dog.objects.filter(base_filter)
        else:
            queryset = Dog.objects.filter(base_filter & dated_filter)

        if not queryset.exists():
            self.stdout.write(self.style.SUCCESS('No intake records needed updates.'))
            return

        available_ids = list(
            queryset.filter(surrender_datetime__isnull=False).values_list('id', flat=True)
        )
        impounded_ids = list(
            queryset.filter(surrender_datetime__isnull=True).values_list('id', flat=True)
        )

        available_count = 0
        impounded_count = 0
        if available_ids:
            available_count = Dog.objects.filter(id__in=available_ids).update(
                status=Dog.Status.AVAILABLE
            )
        if impounded_ids:
            impounded_count = Dog.objects.filter(id__in=impounded_ids).update(
                status=Dog.Status.IMPOUNDED
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Updated {available_count} to AVAILABLE and {impounded_count} to IMPOUNDED.'
            )
        )
