from django.db import models


class DailyMetric(models.Model):
    date = models.DateField()
    metric = models.CharField(max_length=80)
    value = models.IntegerField(default=0)

    class Meta:
        unique_together = ('date', 'metric')

    def __str__(self) -> str:
        return f"{self.date} {self.metric}: {self.value}"
