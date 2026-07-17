import uuid
from datetime import time
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, F
from django.utils.translation import gettext_lazy as _


class DayOfWeek(models.IntegerChoices):
    MONDAY = 0, _("Monday")
    TUESDAY = 1, _("Tuesday")
    WEDNESDAY = 2, _("Wednesday")
    THURSDAY = 3, _("Thursday")
    FRIDAY = 4, _("Friday")
    SATURDAY = 5, _("Saturday")
    SUNDAY = 6, _("Sunday")


class AbstractSchedule(models.Model):
    """
    Абстрактна модель із базовими полями та логікою розкладу.
    """
    is_closed: bool
    closes_next_day: bool
    open_time: Optional[time]
    close_time: Optional[time]
    break_start: Optional[time]
    break_end: Optional[time]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    is_closed = models.BooleanField(
        _("Is Closed"),
        default=False,
        help_text=_("Check this if the restaurant is completely closed.")
    )

    open_time = models.TimeField(_("Open Time"), null=True, blank=True)
    close_time = models.TimeField(_("Close Time"), null=True, blank=True)

    closes_next_day = models.BooleanField(
        _("Closes Next Day"),
        default=False,
        help_text=_("Check this if the restaurant closes after midnight.")
    )

    break_start = models.TimeField(_("Break Start"), null=True, blank=True)
    break_end = models.TimeField(_("Break End"), null=True, blank=True)

    class Meta:
        abstract = True

    def clean(self):
        super().clean()

        if self.is_closed:
            self.open_time = None
            self.close_time = None
            self.closes_next_day = False
            self.break_start = None
            self.break_end = None
            return

        if not self.open_time or not self.close_time:
            raise ValidationError({
                "open_time": _("Open time is required if not closed."),
                "close_time": _("Close time is required if not closed.")
            })

        if not self.closes_next_day and self.open_time >= self.close_time:
            raise ValidationError({
                "close_time": _("Close time must be later than open time unless 'Closes Next Day' is checked.")
            })

        if self.break_start or self.break_end:
            if not (self.break_start and self.break_end):
                raise ValidationError(_("Both break start and end times must be provided together."))

            if self.break_start >= self.break_end:
                raise ValidationError({"break_end": _("Break end must be later than break start.")})

            def to_minutes(t: time) -> int:
                return t.hour * 60 + t.minute

            open_m = to_minutes(self.open_time)
            close_m = to_minutes(self.close_time) + (1440 if self.closes_next_day else 0)
            break_start_m = to_minutes(self.break_start)
            break_end_m = to_minutes(self.break_end)

            if self.closes_next_day and break_start_m < open_m:
                break_start_m += 1440
            if self.closes_next_day and break_end_m < open_m:
                break_end_m += 1440

            if not (open_m <= break_start_m < break_end_m <= close_m):
                raise ValidationError(_("The break period must strictly fall within the working hours."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class WorkingHours(AbstractSchedule):
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        related_name='working_hours',
        verbose_name=_("Restaurant")
    )
    day_of_week = models.SmallIntegerField(
        _("Day of Week"),
        choices=DayOfWeek.choices,
        help_text=_("0 = Monday, 6 = Sunday")
    )

    class Meta:
        db_table = "working_hours"
        verbose_name = _("Working Hour")
        verbose_name_plural = _("Working Hours")
        ordering = ['restaurant', 'day_of_week']
        constraints = [
            models.UniqueConstraint(
                fields=['restaurant', 'day_of_week'],
                name='unique_working_hours_per_day'
            ),
            models.CheckConstraint(
                condition=Q(is_closed=True) | Q(closes_next_day=True) | Q(open_time__lt=F('close_time')),
                name='wh_valid_working_hours'
            ),
            models.CheckConstraint(
                condition=Q(break_start__isnull=True, break_end__isnull=True) | Q(break_start__lt=F('break_end')),
                name='wh_valid_break_hours'
            )
        ]

    def __str__(self):
        day_label = DayOfWeek(self.day_of_week).label
        if self.is_closed:
            return f"{self.restaurant.name} - {day_label}: Closed"
        next_day = " (+1 day)" if self.closes_next_day else ""
        return f"""{self.restaurant.name} - {day_label}: {self.open_time.strftime('%H:%M')} to 
                {self.close_time.strftime('%H:%M')}{next_day}"""


class HolidaySchedule(AbstractSchedule):
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        related_name='holiday_schedules',
        verbose_name=_("Restaurant")
    )
    date = models.DateField(
        _("Date"),
        db_index=True,
        help_text=_("Specific date for the exception.")
    )
    reason = models.CharField(
        _("Reason"),
        max_length=150,
        default="",
        blank=True,
        help_text=_("E.g., New Year's Eve, Renovation, Staff Party.")
    )

    class Meta:
        db_table = "holiday_schedules"
        verbose_name = _("Holiday Schedule")
        verbose_name_plural = _("Holiday Schedules")
        ordering = ['date']
        constraints = [
            models.UniqueConstraint(
                fields=['restaurant', 'date'],
                name='unique_holiday_schedule_per_date'
            ),
            models.CheckConstraint(
                condition=Q(is_closed=True) | Q(closes_next_day=True) | Q(open_time__lt=F('close_time')),
                name='hs_valid_working_hours'
            ),
            models.CheckConstraint(
                condition=Q(break_start__isnull=True, break_end__isnull=True) | Q(break_start__lt=F('break_end')),
                name='hs_valid_break_hours'
            )
        ]

    def __str__(self):
        reason_txt = f" ({self.reason})" if self.reason else ""
        if self.is_closed:
            return f"{self.restaurant.name} - {self.date}{reason_txt}: Closed"
        next_day = " (+1 day)" if self.closes_next_day else ""

        return f"""{self.restaurant.name} - {self.date}{reason_txt}: {self.open_time.strftime('%H:%M')} to 
                {self.close_time.strftime('%H:%M')}{next_day}"""
