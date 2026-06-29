# ─── Routes ───────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        error = "Username atau password salah."
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    users = [dict(u) for u in get_users()]
    return render_template_string(DASHBOARD_HTML, users=users)

@app.route("/api/messages/<int:user_id>")
@login_required
def api_messages(user_id):
    msgs = [dict(m) for m in get_messages(user_id)]
    return jsonify({"messages": msgs})

@app.route("/api/toggle_ai", methods=["POST"])
@login_required
def api_toggle_ai():
    data = request.json
    toggle_ai(data["user_id"], data["enabled"])
    return jsonify({"ok": True})

@app.route("/api/send", methods=["POST"])
@login_required
def api_send():
    data = request.json
    user_id = data["user_id"]
    text = data["text"]
    ok, err = send_telegram_message(user_id, text)
    if ok:
        save_admin_message(user_id, text)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": err})

@app.route("/media/<path:filename>")
@login_required
def serve_media(filename):
    # Keamanan: hanya serve file dari MEDIA_PATH
    safe_path = MEDIA_PATH / filename
    if not str(safe_path.resolve()).startswith(str(MEDIA_PATH.resolve())):
        return "Forbidden", 403
    return send_from_directory(MEDIA_PATH, filename)

# ─── Main ─────────────────────────────────────────────────────
if name == "main":
    port = int(os.environ.get("DASHBOARD_PORT", 5000))
    print(f"Dashboard berjalan di http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
