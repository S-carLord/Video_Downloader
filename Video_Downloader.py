# -*- coding: utf-8 -*-
"""
PyDownloader Moderno – versão revisada

Principais ajustes QA‑driven:
• Formato mais flexível (bestvideo*+bestaudio / best) + merge_output_format="mp4" – cobre WebM.
• Captura do nome do arquivo realmente gerado via progress_hook (status=='finished').
• Emissão de sinal finished apenas depois da fusão, com nome correto.
• Limpeza de threads/objetos usando deleteLater() e integração com aboutToQuit.
• Melhor detecção de qualidade do vídeo na análise.
• UI: título quebrável, botão de download desabilitado se URL for alterada.
"""

import sys
import os
from typing import Optional

import yt_dlp
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QStatusBar,
)
from PySide6.QtCore import QThread, QObject, Signal, Slot, Qt


# -------------------- Trabalhador para ANÁLISE -------------------- #
class AnalysisWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    @Slot()
    def run(self):
        try:
            ydl_opts = {"quiet": True, "no_warnings": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.url, download=False)
            self.finished.emit(info_dict)
        except Exception:
            self.error.emit("Erro de análise (yt‑dlp): verifique a URL.")


# -------------------- Trabalhador para DOWNLOAD ------------------- #
class DownloadWorker(QObject):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, url: str, info_dict: dict):
        super().__init__()
        self.url = url
        self.info_dict = info_dict
        self._finished_filename: Optional[str] = None

    # --- progress hook --- #
    def progress_hook(self, d):
        status = d.get("status")
        if status == "downloading":
            percent_str = d["_percent_str"].strip().replace("%", "")
            try:
                self.progress.emit(int(float(percent_str)))
            except ValueError:
                pass  # ignore parse errors
        elif status == "finished":
            # yt‑dlp fornece o nome real do arquivo já convertido/mesclado
            self._finished_filename = os.path.basename(d.get("filename", "video.mp4"))

    @Slot()
    def run(self):
        try:
            download_path = os.path.join(os.getcwd(), "Downloads")
            os.makedirs(download_path, exist_ok=True)

            ydl_opts = {
                'format': 'bestvideo*+bestaudio/best',
                'merge_output_format': 'mp4',
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                # A LINHA 'ffmpeg_location' FOI REMOVIDA DAQUI
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # chamada blocante – inclui fusão
                ydl.download([self.url])

            # se por alguma razão o hook não capturou – fallback
            final_name = self._finished_filename or (
                yt_dlp.utils.sanitize_filename(self.info_dict.get("title", "video")) + ".mp4"
            )
            self.finished.emit(final_name)

        except Exception as e:
            self.error.emit(f"Erro durante o download: {e}")


# ----------------------- Classe Principal ------------------------- #
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyDownloader Moderno – QA Edition")
        self.setGeometry(300, 300, 520, 260)

        self.video_info: Optional[dict] = None
        self.thread: Optional[QThread] = None
        self.worker: Optional[QObject] = None

        self._build_ui()
        # garante que threads sejam finalizadas se o app fechar
        QApplication.instance().aboutToQuit.connect(self.cleanup_thread)

    # ------------------- UI ------------------- #
    def _build_ui(self):
        self.url_label = QLabel("URL do Vídeo do YouTube:")
        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("Cole a URL aqui…")
        self.url_entry.textChanged.connect(self._on_url_changed)

        self.analyze_button = QPushButton("Analisar URL")

        self.title_label = QLabel("Título do Vídeo:")
        self.video_title_label = QLabel("…")
        self.video_title_label.setWordWrap(True)
        self.video_title_label.setStyleSheet("font-weight: bold;")

        self.quality_label = QLabel("Qualidade disponível:")
        self.video_quality_label = QLabel("…")
        self.video_quality_label.setStyleSheet("font-weight: bold;")

        self.download_button = QPushButton("Baixar Vídeo")
        self.download_button.setEnabled(False)

        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Aguardando URL…")

        # layouts
        main_layout = QVBoxLayout(self)
        url_layout = QHBoxLayout()
        url_layout.addWidget(self.url_entry)
        url_layout.addWidget(self.analyze_button)

        main_layout.addWidget(self.url_label)
        main_layout.addLayout(url_layout)
        main_layout.addSpacing(15)
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.video_title_label)
        main_layout.addSpacing(8)
        main_layout.addWidget(self.quality_label)
        main_layout.addWidget(self.video_quality_label)
        main_layout.addStretch()
        main_layout.addWidget(self.download_button)
        main_layout.addWidget(self.status_bar)

        # signals
        self.analyze_button.clicked.connect(self.start_analysis)
        self.download_button.clicked.connect(self.start_download)

    # ---------- slots & helpers ---------- #
    def _on_url_changed(self):
        # se o usuário editar a URL depois da análise, reseta info
        self.video_info = None
        self.download_button.setEnabled(False)
        self.video_title_label.setText("…")
        self.video_quality_label.setText("…")
        self.status_bar.clearMessage()

    def _thread_running(self) -> bool:
        return self.thread is not None and self.thread.isRunning()

    def start_analysis(self):
        if self._thread_running():
            self.status_bar.showMessage("Aguarde a operação atual terminar.")
            return

        url = self.url_entry.text().strip()
        if not url:
            self.status_bar.showMessage("Erro: insira uma URL.")
            return

        self._set_ui_enabled(False)
        self.status_bar.showMessage("Analisando URL… aguarde.")

        self.thread = QThread(self)
        self.worker = AnalysisWorker(url)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_analysis_finished)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.cleanup_thread)
        self.worker.error.connect(self.cleanup_thread)

        self.thread.start()

    def start_download(self):
        if self._thread_running():
            self.status_bar.showMessage("Aguarde a operação atual terminar.")
            return
        if not self.video_info:
            self.status_bar.showMessage("Erro: analise um vídeo antes de baixar.")
            return

        self._set_ui_enabled(False)
        self.status_bar.showMessage("Iniciando download…")

        self.thread = QThread(self)
        self.worker = DownloadWorker(self.url_entry.text(), self.video_info)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.cleanup_thread)
        self.worker.error.connect(self.cleanup_thread)

        self.thread.start()

    # ---------- cleanup ---------- #
    def cleanup_thread(self):
        if self.thread is not None:
            self.thread.quit()
            self.thread.wait()
            self.thread.deleteLater()
            self.thread = None
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None

    # ---------- UI callbacks ---------- #
    @Slot(dict)
    def on_analysis_finished(self, info_dict: dict):
        self.video_info = info_dict

        # título
        self.video_title_label.setText(info_dict.get("title", "N/A"))

        # melhor resolução disponível
        try:
            best_height = max(f.get("height", 0) for f in info_dict.get("formats", []))
            quality_text = f"{best_height}p" if best_height else "N/A"
        except Exception:
            quality_text = "N/A"
        self.video_quality_label.setText(quality_text)

        self.status_bar.showMessage("Análise concluída. Pronto para baixar!", 6000)
        self._set_ui_enabled(True)

    @Slot(int)
    def update_progress(self, percent: int):
        self.status_bar.showMessage(f"Baixando… {percent}%")

    @Slot(str)
    def on_download_finished(self, filename: str):
        self.status_bar.showMessage(f"Download concluído: {filename}", 10000)
        self._set_ui_enabled(True)

    @Slot(str)
    def on_error(self, msg: str):
        self.status_bar.showMessage(msg, 10000)
        self._set_ui_enabled(True)

    # ---------- helpers ---------- #
    def _set_ui_enabled(self, enabled: bool):
        self.url_entry.setEnabled(enabled)
        self.analyze_button.setEnabled(enabled)
        # só habilita download se já houve análise bem‑sucedida
        self.download_button.setEnabled(enabled and self.video_info is not None)


# -------------------- main -------------------- #
# -------------------- main -------------------- #
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # A linha de setAttribute foi removida, pois o High-DPI já é padrão no Qt6. E a anterior será descontinuada em breve.

    win = MainWindow()
    win.show()

    sys.exit(app.exec())