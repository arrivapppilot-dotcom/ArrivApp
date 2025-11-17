#!/bin/bash
# Quick script to run the faker and populate Render database

cd /Users/lucaalice/Desktop/AI\ projects/ArrivApp/backend

export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=arrivapp.pilot@gmail.com
export SMTP_PASSWORD=cyewwoikichclfqx
export ADMIN_EMAIL=arrivapp.pilot@gmail.com

"/Users/lucaalice/Desktop/AI projects/ArrivApp/.venv/bin/python" populate_render_db.py
