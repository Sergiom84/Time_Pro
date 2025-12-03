"""
Scheduled tasks for the TimeTracker application.
"""
from datetime import datetime, date, time as dt_time
from models.models import TimeRecord
from models.database import db
from flask import current_app


def auto_close_open_records():
    """
    Auto-close all open time records at 23:59:59.
    This function is called by the scheduler daily.
    """
    with current_app.app_context():
        try:
            # Get current date and create the auto-close datetime (23:59:59 of the same day)
            today = date.today()
            auto_close_time = datetime.combine(today, dt_time(23, 59, 59))

            # Find all open records from today (check_in not null, check_out is null)
            # BYPASS tenant filter to process ALL clients (scheduler has no HTTP session)
            open_records = TimeRecord.query.bypass_tenant_filter().filter(
                TimeRecord.date == today,
                TimeRecord.check_in.isnot(None),
                TimeRecord.check_out.is_(None)
            ).all()

            if open_records:
                current_app.logger.info(f"Auto-closing {len(open_records)} open time records across all clients for {today}")

                # Close all open records and their active pauses
                for record in open_records:
                    record.check_out = auto_close_time
                    record.notes = (record.notes or "") + (" - " if record.notes else "") + "Cerrado automáticamente"

                    # Cerrar también las pausas activas de este registro
                    from models.models import WorkPause
                    active_pauses = WorkPause.query.bypass_tenant_filter().filter(
                        WorkPause.time_record_id == record.id,
                        WorkPause.pause_end.is_(None)
                    ).all()

                    for pause in active_pauses:
                        pause.pause_end = auto_close_time
                        pause.notes = (pause.notes or "") + (" - " if pause.notes else "") + "Cerrado automáticamente"
                        current_app.logger.info(f"Cerrando pausa activa (ID: {pause.id}) del registro {record.id}")

                # Commit all changes
                db.session.commit()
                current_app.logger.info(f"Successfully auto-closed {len(open_records)} records")
            else:
                current_app.logger.info(f"No open records to auto-close for {today}")

        except Exception as e:
            current_app.logger.error(f"Error in auto_close_open_records: {str(e)}")
            if db.session:
                db.session.rollback()


def manual_auto_close_records(target_date=None, is_manual=True):
    """
    Manual function to close open records for a specific date.
    Used for testing or administrative purposes.

    Args:
        target_date: The date to close records for (defaults to today)
        is_manual: If True, use current time. If False, use 23:59:59 (for automatic midnight close)
    """
    with current_app.app_context():
        try:
            if target_date is None:
                target_date = date.today()

            # Si es cierre manual (desde el botón), usar hora actual
            # Si es cierre automático (medianoche), usar 23:59:59
            if is_manual:
                auto_close_time = datetime.now()
            else:
                auto_close_time = datetime.combine(target_date, dt_time(23, 59, 59))

            # Find all open records from the target date
            # BYPASS tenant filter to process ALL clients
            open_records = TimeRecord.query.bypass_tenant_filter().filter(
                TimeRecord.date == target_date,
                TimeRecord.check_in.isnot(None),
                TimeRecord.check_out.is_(None)
            ).all()

            if open_records:
                close_type = "Manual" if is_manual else "Automático"
                current_app.logger.info(f"{close_type} auto-closing {len(open_records)} open time records across all clients for {target_date}")

                # Close all open records and their active pauses
                for record in open_records:
                    record.check_out = auto_close_time
                    close_note = "Cerrado manualmente" if is_manual else "Cerrado automáticamente"
                    record.notes = (record.notes or "") + (" - " if record.notes else "") + close_note

                    # Cerrar también las pausas activas de este registro
                    from models.models import WorkPause
                    active_pauses = WorkPause.query.bypass_tenant_filter().filter(
                        WorkPause.time_record_id == record.id,
                        WorkPause.pause_end.is_(None)
                    ).all()

                    for pause in active_pauses:
                        pause.pause_end = auto_close_time
                        pause.notes = (pause.notes or "") + (" - " if pause.notes else "") + close_note
                        current_app.logger.info(f"Cerrando pausa activa (ID: {pause.id}) del registro {record.id}")

                # Commit all changes
                db.session.commit()
                return len(open_records)
            else:
                current_app.logger.info(f"No open records to auto-close for {target_date}")
                return 0

        except Exception as e:
            current_app.logger.error(f"Error in manual_auto_close_records: {str(e)}")
            if db.session:
                db.session.rollback()
            raise