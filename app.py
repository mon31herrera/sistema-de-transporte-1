import os
from datetime import date

import mysql.connector
from flask import Flask, flash, redirect, render_template, request, url_for
from mysql.connector import Error


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "cambia-esta-clave")


DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "transporte_escolar"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
}


def get_server_connection():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        port=DB_CONFIG["port"],
    )


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def init_database():
    connection = get_server_connection()
    cursor = connection.cursor()

    cursor.execute(
        f"""
        CREATE DATABASE IF NOT EXISTS {DB_CONFIG["database"]}
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci
        """
    )
    cursor.execute(f"USE {DB_CONFIG['database']}")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rutas (
          id INT AUTO_INCREMENT PRIMARY KEY,
          nombre VARCHAR(100) NOT NULL,
          origen VARCHAR(150) NOT NULL,
          destino VARCHAR(150) NOT NULL,
          descripcion VARCHAR(255),
          creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS horarios (
          id INT AUTO_INCREMENT PRIMARY KEY,
          ruta_id INT NOT NULL,
          hora_salida TIME NOT NULL,
          hora_llegada TIME NOT NULL,
          cupos_totales INT NOT NULL,
          cupos_disponibles INT NOT NULL,
          creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT fk_horarios_rutas
            FOREIGN KEY (ruta_id) REFERENCES rutas(id)
            ON DELETE CASCADE,
          CONSTRAINT chk_cupos_totales CHECK (cupos_totales > 0),
          CONSTRAINT chk_cupos_disponibles CHECK (cupos_disponibles >= 0)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reservas (
          id INT AUTO_INCREMENT PRIMARY KEY,
          horario_id INT NOT NULL,
          estudiante VARCHAR(120) NOT NULL,
          acudiente VARCHAR(120) NOT NULL,
          telefono VARCHAR(30) NOT NULL,
          fecha_reserva DATE NOT NULL,
          estado ENUM('Activa', 'Cancelada') NOT NULL DEFAULT 'Activa',
          creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT fk_reservas_horarios
            FOREIGN KEY (horario_id) REFERENCES horarios(id)
            ON DELETE CASCADE
        )
        """
    )
    connection.commit()
    cursor.close()
    connection.close()


def fetch_all(query, params=None):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, params or ())
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return rows


def execute(query, params=None):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, params or ())
    connection.commit()
    last_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return last_id


@app.route("/")
def index():
    try:
        rutas = fetch_all("SELECT * FROM rutas ORDER BY nombre")
        horarios = fetch_all(
            """
            SELECT h.*, r.nombre AS ruta_nombre, r.origen, r.destino
            FROM horarios h
            JOIN rutas r ON r.id = h.ruta_id
            ORDER BY h.hora_salida
            """
        )
        reservas = fetch_all(
            """
            SELECT
                res.*,
                h.hora_salida,
                h.hora_llegada,
                r.nombre AS ruta_nombre,
                r.origen,
                r.destino
            FROM reservas res
            JOIN horarios h ON h.id = res.horario_id
            JOIN rutas r ON r.id = h.ruta_id
            ORDER BY res.fecha_reserva DESC, res.id DESC
            """
        )
    except Error as exc:
        flash(f"No se pudo conectar con MySQL: {exc}", "error")
        rutas, horarios, reservas = [], [], []

    return render_template(
        "index.html",
        rutas=rutas,
        horarios=horarios,
        reservas=reservas,
        today=date.today().isoformat(),
        db_name=DB_CONFIG["database"],
    )


@app.post("/rutas")
def crear_ruta():
    nombre = request.form.get("nombre", "").strip()
    origen = request.form.get("origen", "").strip()
    destino = request.form.get("destino", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    if not nombre or not origen or not destino:
        flash("Completa nombre, origen y destino de la ruta.", "error")
        return redirect(url_for("index"))

    try:
        execute(
            """
            INSERT INTO rutas (nombre, origen, destino, descripcion)
            VALUES (%s, %s, %s, %s)
            """,
            (nombre, origen, destino, descripcion),
        )
        flash("Ruta creada correctamente.", "success")
    except Error as exc:
        flash(f"No se pudo crear la ruta: {exc}", "error")

    return redirect(url_for("index"))


@app.post("/horarios")
def crear_horario():
    ruta_id = request.form.get("ruta_id")
    hora_salida = request.form.get("hora_salida")
    hora_llegada = request.form.get("hora_llegada")
    cupos_totales = request.form.get("cupos_totales", type=int)

    if not ruta_id or not hora_salida or not hora_llegada or not cupos_totales:
        flash("Completa ruta, horas y cupos del horario.", "error")
        return redirect(url_for("index"))

    if cupos_totales <= 0:
        flash("Los cupos deben ser mayores que cero.", "error")
        return redirect(url_for("index"))

    try:
        execute(
            """
            INSERT INTO horarios (ruta_id, hora_salida, hora_llegada, cupos_totales, cupos_disponibles)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (ruta_id, hora_salida, hora_llegada, cupos_totales, cupos_totales),
        )
        flash("Horario creado correctamente.", "success")
    except Error as exc:
        flash(f"No se pudo crear el horario: {exc}", "error")

    return redirect(url_for("index"))


@app.post("/reservas")
def crear_reserva():
    horario_id = request.form.get("horario_id")
    estudiante = request.form.get("estudiante", "").strip()
    acudiente = request.form.get("acudiente", "").strip()
    telefono = request.form.get("telefono", "").strip()
    fecha_reserva = request.form.get("fecha_reserva")

    if not horario_id or not estudiante or not acudiente or not telefono or not fecha_reserva:
        flash("Completa todos los datos de la reserva.", "error")
        return redirect(url_for("index"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        connection.start_transaction()

        cursor.execute(
            "SELECT cupos_disponibles FROM horarios WHERE id = %s FOR UPDATE",
            (horario_id,),
        )
        horario = cursor.fetchone()

        if not horario:
            flash("El horario seleccionado no existe.", "error")
            connection.rollback()
            return redirect(url_for("index"))

        if horario["cupos_disponibles"] <= 0:
            flash("No hay cupos disponibles para ese horario.", "error")
            connection.rollback()
            return redirect(url_for("index"))

        cursor.execute(
            """
            INSERT INTO reservas (horario_id, estudiante, acudiente, telefono, fecha_reserva)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (horario_id, estudiante, acudiente, telefono, fecha_reserva),
        )
        cursor.execute(
            """
            UPDATE horarios
            SET cupos_disponibles = cupos_disponibles - 1
            WHERE id = %s
            """,
            (horario_id,),
        )
        connection.commit()
        flash("Reserva registrada correctamente.", "success")
    except Error as exc:
        if connection:
            connection.rollback()
        flash(f"No se pudo registrar la reserva: {exc}", "error")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for("index"))


@app.post("/reservas/<int:reserva_id>/cancelar")
def cancelar_reserva(reserva_id):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        connection.start_transaction()

        cursor.execute(
            "SELECT horario_id, estado FROM reservas WHERE id = %s FOR UPDATE",
            (reserva_id,),
        )
        reserva = cursor.fetchone()

        if not reserva:
            flash("La reserva no existe.", "error")
            connection.rollback()
            return redirect(url_for("index"))

        if reserva["estado"] == "Cancelada":
            flash("La reserva ya estaba cancelada.", "error")
            connection.rollback()
            return redirect(url_for("index"))

        cursor.execute(
            "UPDATE reservas SET estado = 'Cancelada' WHERE id = %s",
            (reserva_id,),
        )
        cursor.execute(
            """
            UPDATE horarios
            SET cupos_disponibles = cupos_disponibles + 1
            WHERE id = %s
            """,
            (reserva["horario_id"],),
        )
        connection.commit()
        flash("Reserva cancelada y cupo liberado.", "success")
    except Error as exc:
        if connection:
            connection.rollback()
        flash(f"No se pudo cancelar la reserva: {exc}", "error")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for("index"))


if __name__ == "__main__":
    init_database()
    app.run(debug=True)
