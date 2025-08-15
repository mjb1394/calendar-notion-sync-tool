from flask import (
    Blueprint,
    current_app,
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
)
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import date

from notion_calendar_sync.local.builder import parse_items, build_calendar
from notion_calendar_sync.local.updater import Calendar
import json
import logging
from notion_calendar_sync.web import services
from notion_calendar_sync.web import config_manager
from notion_calendar_sync.web import scheduler

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """
    Main page, displays a summary of calendar items.
    """
    # This is a simple example of integrating with existing logic.
    # In a real app, you'd handle file-not-found errors etc.
    events_path = Path(current_app.config["CALENDAR_FILE_PATH"])
    if events_path.exists():
        events, tasks = parse_items(events_path, timezone=ZoneInfo("UTC"))
        summary = {"event_count": len(events), "task_count": len(tasks)}
    else:
        summary = {
            "event_count": 0,
            "task_count": 0,
            "error": "calendar.json not found",
        }

    return render_template("index.html", summary=summary)


@main_bp.route("/calendar")
def calendar():
    """
    Displays the FullCalendar view.
    """
    return render_template("calendar.html")


@main_bp.route("/api/events")
def api_events():
    """
    API endpoint to fetch events for FullCalendar.
    """
    events_path = Path(current_app.config["CALENDAR_FILE_PATH"])
    calendar_events = []
    if events_path.exists() and events_path.stat().st_size > 0:
        try:
            with open(events_path, "r") as f:
                items = json.load(f)
            for item in items:
                if item.get("type") == "event":
                    event_date = item.get("date")
                    # Use a default time if 'start' or 'end' is missing
                    start_time = item.get("start", "00:00")
                    end_time = item.get("end", "23:59")

                    start_dt = f"{event_date}T{start_time}"
                    end_dt = f"{event_date}T{end_time}"

                    calendar_events.append({
                        "title": item.get("title"),
                        "start": start_dt,
                        "end": end_dt,
                        "color": "#5372f0" # Accent color for events
                    })
                elif item.get("type") == "task":
                    due_date = item.get("due_date")
                    if due_date:
                        calendar_events.append({
                            "title": f"Task: {item.get('title')}",
                            "start": due_date,
                            "allDay": True,
                            "color": "#ff9f43" # Orange for tasks
                        })
        except (json.JSONDecodeError, TypeError) as e:
            logging.error(f"Error processing calendar.json: {e}", exc_info=True)
            return jsonify({"error": "Failed to load calendar events."}), 500

    return jsonify(calendar_events)


@main_bp.route("/healthz")
def healthz():
    """
    Health check endpoint.
    """
    return jsonify({"status": "ok"}), 200


@main_bp.route("/add", methods=["GET", "POST"])
def add_item():
    """
    Page for adding a new event or task.
    """
    if request.method == "POST":
        item_type = request.form.get("item_type")
        title = request.form.get("title")
        cal = Calendar(current_app.config["CALENDAR_FILE_PATH"])

        try:
            if item_type == "event":
                cal.add_event(
                    event=title,
                    eventtype=request.form.get("event_type"),
                    location=request.form.get("location"),
                    room=request.form.get("room"),
                    date=request.form.get("date"),
                    start=request.form.get("start"),
                    end=request.form.get("end"),
                )
                flash(f"Event '{title}' added successfully!", "success")
            elif item_type == "task":
                cal.add_task(
                    task=title,
                    due_date=request.form.get("due_date"),
                    priority=request.form.get("priority"),
                    status=request.form.get("status"),
                    notes=request.form.get("notes"),
                )
                flash(f"Task '{title}' added successfully!", "success")
            else:
                flash("Invalid item type selected.", "error")

        except Exception as e:
            flash(f"Error adding item: {e}", "error")

        return redirect(url_for("main.add_item"))

    return render_template("add_item.html")


@main_bp.route("/build", methods=["GET", "POST"])
def build():
    """
    Page for building a calendar file.
    """
    if request.method == "POST":
        try:
            week_date = None
            if request.form.get("week"):
                week_date = date.fromisoformat(request.form.get("week"))

            output_files = build_calendar(
                events_path=Path(current_app.config["CALENDAR_FILE_PATH"]),
                view=request.form.get("view"),
                year=(
                    int(request.form.get("year")) if request.form.get("year") else None
                ),
                month=(
                    int(request.form.get("month"))
                    if request.form.get("month")
                    else None
                ),
                week=week_date,
                include_tasks=request.form.get("include_tasks") == "true",
                formats=[request.form.get("format")],
            )

            if not output_files:
                flash("Calendar could not be built with the given options.", "error")
                return redirect(url_for("main.build"))

            # Send the first generated file for download
            output_file = output_files[0]
            return send_from_directory(
                directory=output_file.parent, path=output_file.name, as_attachment=True
            )

        except Exception as e:
            flash(f"Error building calendar: {e}", "error")
            return redirect(url_for("main.build"))

    return render_template("build.html")


@main_bp.route("/sync")
def sync_page():
    """
    Displays the Sync & Integrations page.
    """
    return render_template("sync.html")


@main_bp.route("/sync/run", methods=["POST"])
def run_sync_route():
    """
    Triggers the Notion sync process.
    """
    dry_run = request.form.get("dry_run") == "true"
    result = services.run_sync(dry_run=dry_run)
    flash(result["message"], "success" if result["success"] else "error")
    return redirect(url_for("main.sync_page"))


@main_bp.route("/sync/plan-study", methods=["POST"])
def run_plan_study_route():
    """
    Triggers the study planning process.
    """
    try:
        exam_title = request.form["exam_title"]
        exam_date = date.fromisoformat(request.form["exam_date"])
        total_hours = int(request.form["total_hours"])
        session_duration = int(request.form["session_duration"])
        dry_run = request.form.get("dry_run") == "true"

        result = services.run_plan_study(
            exam_title=exam_title,
            exam_date=exam_date,
            total_hours=total_hours,
            session_duration_hours=session_duration,
            dry_run=dry_run,
        )
        flash(result["message"], "success" if result["success"] else "error")
    except (KeyError, ValueError) as e:
        flash(f"Invalid form submission: {e}", "error")

    return redirect(url_for("main.sync_page"))


@main_bp.route("/sync/spaced-repetition", methods=["POST"])
def run_spaced_repetition_route():
    """
    Triggers the spaced repetition scheduling process.
    """
    try:
        task_uid = request.form["task_uid"]
        intervals_str = request.form["intervals"]
        intervals = [int(i.strip()) for i in intervals_str.split(",")]
        dry_run = request.form.get("dry_run") == "true"

        result = services.run_spaced_repetition(
            source_task_uid=task_uid,
            intervals=intervals,
            dry_run=dry_run,
        )
        flash(result["message"], "success" if result["success"] else "error")
    except (KeyError, ValueError) as e:
        flash(f"Invalid form submission: {e}", "error")

    return redirect(url_for("main.sync_page"))


@main_bp.route("/sync/weekly-review", methods=["POST"])
def run_weekly_review_route():
    """
    Triggers the weekly review generation process.
    """
    dry_run = request.form.get("dry_run") == "true"
    result = services.run_weekly_review(dry_run=dry_run)
    flash(result["message"], "success" if result["success"] else "error")
    return redirect(url_for("main.sync_page"))


@main_bp.route("/settings", methods=["GET", "POST"])
def settings_page():
    """
    Displays the Settings page and handles updates.
    """
    if request.method == "POST":
        action = request.form.get("action")
        configs = config_manager.load_configs()

        if action == "save":
            config_name = request.form.get("config_name")
            # In a real app, you'd validate this data thoroughly
            settings_data = {
                "plan_study": {
                    "total_hours": int(request.form.get("total_hours")),
                    "session_duration": int(request.form.get("session_duration")),
                },
                "spaced_rep": {
                    "intervals": [int(i.strip()) for i in request.form.get("intervals").split(",")]
                }
            }
            config_manager.save_config(config_name, settings_data)
            flash(f"Configuration '{config_name}' saved.", "success")

        elif action == "create":
            new_name = request.form.get("new_config_name")
            if new_name and new_name not in configs:
                config_manager.save_config(new_name, config_manager.get_config("default"))
                flash(f"Configuration '{new_name}' created.", "success")
            else:
                flash("Invalid or duplicate configuration name.", "error")

        elif action == "delete":
            config_name = request.form.get("config_name")
            if config_name != "default" and config_name in configs:
                del configs[config_name]
                config_manager.save_configs(configs)
                flash(f"Configuration '{config_name}' deleted.", "success")
            else:
                flash("Cannot delete the default or a non-existent configuration.", "error")

        return redirect(url_for("main.settings_page"))

    configs = config_manager.load_configs()
    active_config_name = config_manager.get_active_config_name()
    active_config = configs.get(active_config_name, {})
    job_status = scheduler.get_job_status()
    return render_template("settings.html", configs=configs, active_config_name=active_config_name, active_config=active_config, job_status=job_status)


@main_bp.route("/settings/scheduler/start", methods=["POST"])
def start_scheduler():
    try:
        interval = int(request.form.get("interval", 30))
        scheduler.start_sync_job(interval)
        flash(f"Sync job started. Interval: {interval} minutes.", "success")
    except Exception as e:
        flash(f"Error starting scheduler: {e}", "error")
    return redirect(url_for("main.settings_page"))


@main_bp.route("/settings/scheduler/stop", methods=["POST"])
def stop_scheduler():
    try:
        scheduler.stop_sync_job()
        flash("Sync job stopped.", "success")
    except Exception as e:
        flash(f"Error stopping scheduler: {e}", "error")
    return redirect(url_for("main.settings_page"))


@main_bp.route("/notion-tools", methods=["GET", "POST"])
def notion_tools_page():
    """
    Displays the Notion Tools page and handles page creation.
    """
    if request.method == "POST":
        try:
            database_id = request.form["database_id"]
            title = request.form["page_title"]
            properties_json = request.form.get("properties_json", "{}")
            properties = json.loads(properties_json)

            result = services.create_notion_page(
                database_id=database_id,
                title=title,
                properties=properties
            )
            flash(result["message"], "success" if result["success"] else "error")
        except (KeyError, json.JSONDecodeError) as e:
            flash(f"Invalid form submission: {e}", "error")

        return redirect(url_for("main.notion_tools_page"))

    return render_template("notion_tools.html")
