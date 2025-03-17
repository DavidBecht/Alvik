import asyncio
import socket

from alvik_http_server.alvic_exec_print import AlvikExecPrint
from alvik_logger.logger import get_error_message, logger


class AlvikAsyncPythonRunner:
    """Verwaltet das asynchrone Ausführen und Stoppen von Python-Skripten."""

    def __init__(self):
        self.task = None  # Speichert den laufenden Task

    @staticmethod
    def send_to_client(data, client):
        output = data.strip().replace("\n", "<br>")  # HTML-taugliche Zeilenumbrüche
        client.send(f"data: {output}\n\n".encode("utf-8"))

    async def run_python_file(self, filename: str, client: socket):
        """Startet eine Python-Datei und sendet deren Output in Echtzeit zurück."""
        with open(filename, "r") as f:
            code = f.read()

        stream = AlvikExecPrint(AlvikAsyncPythonRunner.send_to_client, client)

        try:
            exec(code, stream.namespace)  # Führe den Code mit modifizierter `print()`-Funktion aus
        except Exception as e:
            error_trace = get_error_message(e)
            stream.write(f"Execution of {filename} failed with {e}.\n{error_trace}")  # Fehler auch sofort senden
            logger.error(f"Execution of {filename} failed with {e}.\n{error_trace}")

        logger.info(f"Execution of {filename} completed.")

    async def start(self, filename: str, client: socket):
        """Startet das Python-Skript in einem neuen Task."""
        if self.task and not self.task.done():
            logger.debug("Bereits eine laufende Instanz. Stoppe die Instanz.")
            await self.stop()

        self.task = asyncio.create_task(self.run_python_file(filename, client))
        print(f"Starte {filename}...")

    async def stop(self):
        """Stoppt das aktuell laufende Python-Skript."""
        if self.task and not self.task.done():
            self.task.cancel()
            logger.debug("Task wird gestoppt.")
            try:
                await self.task  # Warte auf das Stoppen des Tasks
            except asyncio.CancelledError:
                logger.debug("Task wurde erfolgreich gestoppt.")
        else:
             logger.debug("Kein laufender Task gefunden.")
