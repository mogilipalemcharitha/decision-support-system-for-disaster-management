from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.db import get_db
from app.models import get_all_disasters, log_activity
from app.routes.auth_routes import login_required, roles_required
from datetime import datetime

gdss_bp = Blueprint("gdss", __name__)

@gdss_bp.route("/gdss")
@login_required
def index():
    conn = get_db()
    decisions = conn.execute("""
        SELECT g.*, d.disaster_type, d.location
        FROM gdss_decisions g
        JOIN disasters d ON g.disaster_id = d.id
        ORDER BY g.id DESC
    """).fetchall()

    disasters = get_all_disasters()
    conn.close()

    # Enhance decisions with opinions, votes, and consensus percentage
    enhanced_decisions = []
    conn = get_db()
    for d in decisions:
        opinions = conn.execute("SELECT * FROM gdss_opinions WHERE decision_id = ? ORDER BY id ASC", (d["id"],)).fetchall()
        votes = conn.execute("SELECT * FROM gdss_votes WHERE decision_id = ? ORDER BY id ASC", (d["id"],)).fetchall()

        # Consensus math
        vote_counts = {}
        total_votes = len(votes)
        consensus_pct = 0.0
        winning_option = None

        if total_votes > 0:
            for v in votes:
                opt = v["vote_option"]
                vote_counts[opt] = vote_counts.get(opt, 0) + 1
            winning_option = max(vote_counts, key=vote_counts.get)
            consensus_pct = round((vote_counts[winning_option] / total_votes) * 100, 1)

        user_voted = conn.execute("SELECT * FROM gdss_votes WHERE decision_id = ? AND user_id = ?", (d["id"], session.get("user_id"))).fetchone()

        enhanced_decisions.append({
            "details": d,
            "opinions": opinions,
            "votes": votes,
            "vote_counts": vote_counts,
            "total_votes": total_votes,
            "consensus_pct": consensus_pct,
            "winning_option": winning_option,
            "user_voted": user_voted
        })
    conn.close()

    return render_template("gdss.html", decisions=enhanced_decisions, disasters=disasters)

@gdss_bp.route("/gdss/create", methods=["POST"])
@login_required
@roles_required("System Administrator", "Disaster Management Authority")
def create_decision():
    disaster_id = int(request.form.get("disaster_id"))
    title = request.form.get("title")
    issue_description = request.form.get("issue_description")
    expert_recommendation = request.form.get("expert_recommendation", "")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute("""
        INSERT INTO gdss_decisions (disaster_id, title, issue_description, expert_recommendation, status, created_at)
        VALUES (?, ?, ?, ?, 'OPEN', ?)
    """, (disaster_id, title, issue_description, expert_recommendation, now_str))
    conn.commit()
    conn.close()

    log_activity(session.get("user_id"), session.get("username"), session.get("role"),
                 "CREATE_GDSS_DECISION", f"Created decision proposal: {title}")
    flash(f"Emergency Decision '{title}' proposed for stakeholder collaboration.", "success")
    return redirect(url_for("gdss.index"))

@gdss_bp.route("/gdss/<int:decision_id>/opinion", methods=["POST"])
@login_required
def add_opinion(decision_id):
    opinion_text = request.form.get("opinion_text")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute("""
        INSERT INTO gdss_opinions (decision_id, user_id, username, role, opinion_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (decision_id, session.get("user_id"), session.get("username"), session.get("role"), opinion_text, now_str))
    conn.commit()
    conn.close()

    log_activity(session.get("user_id"), session.get("username"), session.get("role"),
                 "SUBMIT_GDSS_OPINION", f"Submitted opinion on Decision #{decision_id}")
    flash("Opinion registered successfully.", "info")
    return redirect(url_for("gdss.index"))

@gdss_bp.route("/gdss/<int:decision_id>/vote", methods=["POST"])
@login_required
def cast_vote(decision_id):
    vote_option = request.form.get("vote_option")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    # Check if already voted
    existing = conn.execute("SELECT id FROM gdss_votes WHERE decision_id = ? AND user_id = ?",
                            (decision_id, session.get("user_id"))).fetchone()
    if existing:
        conn.execute("""
            UPDATE gdss_votes
            SET vote_option = ?, created_at = ?
            WHERE id = ?
        """, (vote_option, now_str, existing["id"]))
        flash("Your vote has been updated.", "info")
    else:
        conn.execute("""
            INSERT INTO gdss_votes (decision_id, user_id, username, role, vote_option, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (decision_id, session.get("user_id"), session.get("username"), session.get("role"), vote_option, now_str))
        flash("Vote recorded successfully!", "success")

    conn.commit()
    conn.close()

    log_activity(session.get("user_id"), session.get("username"), session.get("role"),
                 "CAST_GDSS_VOTE", f"Voted '{vote_option}' on Decision #{decision_id}")
    return redirect(url_for("gdss.index"))

@gdss_bp.route("/gdss/<int:decision_id>/finalize", methods=["POST"])
@login_required
@roles_required("System Administrator", "Disaster Management Authority")
def finalize_decision(decision_id):
    final_decision = request.form.get("final_decision")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute("""
        UPDATE gdss_decisions
        SET status = 'FINALIZED', final_decision = ?, finalized_by = ?
        WHERE id = ?
    """, (final_decision, session.get("username"), decision_id))
    conn.commit()
    conn.close()

    log_activity(session.get("user_id"), session.get("username"), session.get("role"),
                 "FINALIZE_GDSS_DECISION", f"Finalized Decision #{decision_id}: {final_decision}")
    flash(f"Decision #{decision_id} successfully finalized & recorded in audit history.", "success")
    return redirect(url_for("gdss.index"))

@gdss_bp.route("/history")
@login_required
def history():
    conn = get_db()
    finalized_decisions = conn.execute("""
        SELECT g.*, d.disaster_type, d.location
        FROM gdss_decisions g
        JOIN disasters d ON g.disaster_id = d.id
        WHERE g.status = 'FINALIZED'
        ORDER BY g.id DESC
    """).fetchall()

    history_list = []
    for d in finalized_decisions:
        opinions = conn.execute("SELECT * FROM gdss_opinions WHERE decision_id = ?", (d["id"],)).fetchall()
        votes = conn.execute("SELECT * FROM gdss_votes WHERE decision_id = ?", (d["id"],)).fetchall()
        history_list.append({
            "details": d,
            "opinions_count": len(opinions),
            "votes_count": len(votes),
            "opinions": opinions,
            "votes": votes
        })

    all_logs = conn.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    return render_template("history.html", history_list=history_list, logs=all_logs)
